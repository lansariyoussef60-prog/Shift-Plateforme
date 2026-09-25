from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.partner import Partner
from app.models.speaker import Speaker
from app.models.target_list import TargetList
from app.models.user import User
from app.schemas.search import SearchResultItem, SearchResults
from app.utils.normalize import normalize_company_name

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResults)
def global_search(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Searches partners and speakers by normalized name (same matching logic
    as the dedup checks), and users/target lists by plain case-insensitive
    substring — each source capped at 10 results to keep this fast and
    scannable rather than a full paginated search per entity."""
    normalized = normalize_company_name(q)
    name_like_pattern = f"%{normalized}%"
    plain_like_pattern = f"%{q.lower()}%"

    partners = (
        db.query(Partner).filter(Partner.normalized_name.ilike(name_like_pattern)).limit(10).all()
    )
    speakers = (
        db.query(Speaker).filter(Speaker.normalized_name.ilike(name_like_pattern)).limit(10).all()
    )
    users = (
        db.query(User).filter(func.lower(User.full_name).like(plain_like_pattern)).limit(10).all()
    )
    target_lists = (
        db.query(TargetList).filter(func.lower(TargetList.name).like(plain_like_pattern)).limit(10).all()
    )

    return SearchResults(
        partners=[SearchResultItem(id=p.id, label=p.company_name, subtitle=p.status.value) for p in partners],
        speakers=[SearchResultItem(id=s.id, label=s.name, subtitle=s.status.value) for s in speakers],
        users=[SearchResultItem(id=u.id, label=u.full_name, subtitle=u.role.value) for u in users],
        target_lists=[SearchResultItem(id=t.id, label=t.name, subtitle=None) for t in target_lists],
    )
