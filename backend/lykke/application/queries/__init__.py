"""Query handlers for read-only operations.

Query handlers execute read operations and return data without side effects.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from .brain_dump import (
    GetBrainDumpHandler,
    GetBrainDumpQuery,
    SearchBrainDumpsHandler,
    SearchBrainDumpsQuery,
)
from .compute_task_risk import (
    ComputeTaskRiskHandler,
    ComputeTaskRiskQuery,
    TaskRiskResult,
    TaskRiskScore,
)
from .get_day_context import GetDayContextHandler, GetDayContextQuery
from .get_incremental_changes import (
    GetIncrementalChangesHandler,
    GetIncrementalChangesQuery,
)
from .get_llm_prompt_context import GetLLMPromptContextHandler, GetLLMPromptContextQuery
from .list_base_personalities import (
    BasePersonalityInfo,
    ListBasePersonalitiesHandler,
    ListBasePersonalitiesQuery,
)
from .preview_day import PreviewDayHandler, PreviewDayQuery
from .preview_tasks import PreviewTasksHandler, PreviewTasksQuery
from .usecase_config import GetUseCaseConfigHandler, GetUseCaseConfigQuery

if TYPE_CHECKING:
    # NOTE: This is lazily imported at runtime to avoid circular imports via
    # `lykke.application.llm` <-> `lykke.application.commands`.
    from .preview_llm_snapshot import PreviewLLMSnapshotHandler, PreviewLLMSnapshotQuery

__all__ = [
    "BasePersonalityInfo",
    "ComputeTaskRiskHandler",
    "ComputeTaskRiskQuery",
    "GetBrainDumpHandler",
    "GetBrainDumpQuery",
    "GetDayContextHandler",
    "GetDayContextQuery",
    "GetIncrementalChangesHandler",
    "GetIncrementalChangesQuery",
    "GetLLMPromptContextHandler",
    "GetLLMPromptContextQuery",
    "GetUseCaseConfigHandler",
    "GetUseCaseConfigQuery",
    "ListBasePersonalitiesHandler",
    "ListBasePersonalitiesQuery",
    "PreviewDayHandler",
    "PreviewDayQuery",
    "PreviewLLMSnapshotHandler",
    "PreviewLLMSnapshotQuery",
    "PreviewTasksHandler",
    "PreviewTasksQuery",
    "SearchBrainDumpsHandler",
    "SearchBrainDumpsQuery",
    "TaskRiskResult",
    "TaskRiskScore",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "PreviewLLMSnapshotHandler": (".preview_llm_snapshot", "PreviewLLMSnapshotHandler"),
    "PreviewLLMSnapshotQuery": (".preview_llm_snapshot", "PreviewLLMSnapshotQuery"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_IMPORTS:
        module_name, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_name, __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
