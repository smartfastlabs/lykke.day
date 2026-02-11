"""Query to compute risk scores for tasks based on tags and completion history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from lykke.application.queries.base import BaseQueryHandler, Query
from lykke.application.repositories import AuditLogRepositoryReadOnlyProtocol
from lykke.domain import value_objects

if TYPE_CHECKING:
    from uuid import UUID

    from lykke.domain.entities import TaskEntity


@dataclass(frozen=True)
class TaskRiskScore:
    """Risk score for a task."""

    task_id: UUID
    completion_rate: float  # 0-100
    risk_reason: str


@dataclass(frozen=True)
class ComputeTaskRiskQuery(Query):
    """Query to compute risk scores for tasks."""

    tasks: list[TaskEntity]
    lookback_days: int = 30  # How many days to look back for completion history


@dataclass(frozen=True)
class TaskRiskResult:
    """Result of risk computation."""

    high_risk_tasks: list[TaskRiskScore]


class ComputeTaskRiskHandler(BaseQueryHandler[ComputeTaskRiskQuery, TaskRiskResult]):
    """Compute risk scores for tasks based on tags and completion history."""

    audit_log_ro_repo: AuditLogRepositoryReadOnlyProtocol

    async def handle(self, query: ComputeTaskRiskQuery) -> TaskRiskResult:
        """Compute risk scores for tasks."""
        high_risk_tasks: list[TaskRiskScore] = []

        # Calculate lookback window
        lookback_start = datetime.now(UTC) - timedelta(days=query.lookback_days)

        for task in query.tasks:
            # Skip completed tasks
            if task.status == value_objects.TaskStatus.COMPLETE:
                continue

            # Skip daily routine tasks (they're not "out of the ordinary")
            if task.frequency == value_objects.TaskFrequency.DAILY:
                continue

            risk_score = 0.0
            risk_reasons: list[str] = []

            # Check tags for risk signals
            if value_objects.TaskTag.AVOIDANT in task.tags:
                risk_score += 30.0
                risk_reasons.append("marked as avoidant")
            if value_objects.TaskTag.FORGETTABLE in task.tags:
                risk_score += 25.0
                risk_reasons.append("marked as forgettable")
            if value_objects.TaskTag.URGENT in task.tags:
                risk_score += 20.0
                risk_reasons.append("marked as urgent")

            # Compute completion rate from audit logs
            # Look for TaskCompletedEvent and TaskPuntedEvent for this task
            completion_events = await self.audit_log_ro_repo.search(
                value_objects.AuditLogQuery(
                    entity_id=task.id,
                    entity_type="task",
                    activity_type="TaskCompletedEvent",
                    occurred_after=lookback_start,
                )
            )

            punt_events = await self.audit_log_ro_repo.search(
                value_objects.AuditLogQuery(
                    entity_id=task.id,
                    entity_type="task",
                    activity_type="TaskPuntedEvent",
                    occurred_after=lookback_start,
                )
            )

            # Also check for task state updates that show completion
            # Look for any task-related events for this task definition or routine
            total_attempts = len(completion_events) + len(punt_events)

            if total_attempts > 0:
                completion_rate = (len(completion_events) / total_attempts) * 100.0
            else:
                # No history - check if it's a new task or one-time task
                if task.frequency == value_objects.TaskFrequency.ONCE:
                    # One-time tasks with no history are medium risk
                    completion_rate = 50.0
                    risk_reasons.append("one-time task with no completion history")
                else:
                    # Recurring tasks with no history might be new - lower risk
                    completion_rate = 70.0

            # Adjust risk score based on completion rate
            if completion_rate < 40.0:
                risk_score += 40.0
                risk_reasons.append(f"low completion rate ({completion_rate:.0f}%)")
            elif completion_rate < 60.0:
                risk_score += 20.0
                risk_reasons.append(
                    f"moderate completion rate ({completion_rate:.0f}%)"
                )

            # Consider frequency - non-daily tasks are inherently more "out of the ordinary"
            # We already skipped DAILY tasks above, so this check is safe
            # Use a list check to avoid mypy comparison-overlap error
            non_daily_frequencies = [
                value_objects.TaskFrequency.CUSTOM_WEEKLY,
                value_objects.TaskFrequency.WEEKLY,
                value_objects.TaskFrequency.ONCE,
                value_objects.TaskFrequency.YEARLY,
                value_objects.TaskFrequency.MONTHLY,
                value_objects.TaskFrequency.BI_WEEKLY,
                value_objects.TaskFrequency.WEEK_DAYS,
                value_objects.TaskFrequency.WEEKEND_DAYS,
            ]
            if task.frequency in non_daily_frequencies:
                risk_score += 15.0
                if not any("out of the ordinary" in r for r in risk_reasons):
                    risk_reasons.append("non-daily task (out of the ordinary)")

            # Only include tasks with significant risk (score >= 30)
            if risk_score >= 30.0:
                high_risk_tasks.append(
                    TaskRiskScore(
                        task_id=task.id,
                        completion_rate=completion_rate,
                        risk_reason=", ".join(risk_reasons)
                        if risk_reasons
                        else "high risk",
                    )
                )

        return TaskRiskResult(high_risk_tasks=high_risk_tasks)
