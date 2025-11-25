from typing import Self, Any

import pydantic


class BaseObject(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        # frozen=True,
    )

    def clone(self, **kwargs: dict[str, Any]) -> Self:
        return self.model_copy(update=kwargs)

    @property
    def id(self) -> str:
        if hasattr(self, "guid"):
            return str(self.guid)
        elif hasattr(self, "uuid"):
            return str(self.uuid)
        elif hasattr(self, "platform_id") and hasattr(self, "platform"):
            return f"{self.platform}_{self.platform_id}"
        elif hasattr(self, "email"):
            return str(self.email)

        raise AttributeError("No suitable ID attribute found.")
