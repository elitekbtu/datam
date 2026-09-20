from pydantic import BaseModel, ConfigDict


class ReadSchema(BaseModel):
    """Response model serialised straight from an ORM instance."""

    model_config = ConfigDict(from_attributes=True)


class WriteSchema(BaseModel):
    """Request model that rejects fields the client is not allowed to set."""

    model_config = ConfigDict(extra="forbid")


class Page[ItemT: ReadSchema](BaseModel):
    """One slice of a listing, alongside the size of the full result set."""

    items: list[ItemT]
    total: int
    limit: int
    offset: int
