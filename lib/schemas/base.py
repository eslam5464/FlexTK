from pydantic import BaseModel, ConfigDict


class BaseMetadata(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        strict=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )
