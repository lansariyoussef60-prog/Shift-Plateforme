import uuid
from typing import List, Optional

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    id: uuid.UUID
    label: str
    subtitle: Optional[str] = None


class SearchResults(BaseModel):
    partners: List[SearchResultItem]
    speakers: List[SearchResultItem]
    users: List[SearchResultItem]
    target_lists: List[SearchResultItem]
