from typing import Any

from lykke.domain.entities.template import TemplateEntity
from lykke.infrastructure.database.tables import templates_tbl
from sqlalchemy.sql import Select

from .base import TemplateQuery, UserScopedBaseRepository


class TemplateRepository(UserScopedBaseRepository[TemplateEntity, TemplateQuery]):
    Object = TemplateEntity
    table = templates_tbl
    QueryClass = TemplateQuery

    def build_query(self, query: TemplateQuery) -> Select[tuple]:
        """Build a SQLAlchemy Core select statement from a query object."""
        stmt = super().build_query(query)

        if query.usecase is not None:
            stmt = stmt.where(self.table.c.usecase == query.usecase)

        if query.key is not None:
            stmt = stmt.where(self.table.c.key == query.key)

        return stmt

    @staticmethod
    def entity_to_row(template: TemplateEntity) -> dict[str, Any]:
        """Convert a Template entity to a database row dict."""
        return {
            "id": template.id,
            "user_id": template.user_id,
            "usecase": template.usecase,
            "key": template.key,
            "name": template.name,
            "description": template.description,
            "content": template.content,
            "created_at": template.created_at,
        }
