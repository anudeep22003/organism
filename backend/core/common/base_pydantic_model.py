from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AliasedBaseModel(BaseModel):
    """
    Base model with camelCase aliasing for API consistency.
    All API-facing schemas should inherit from this.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def model_dump_json(self, **kwargs: Any) -> str:
        return super().model_dump_json(by_alias=True, **kwargs)
