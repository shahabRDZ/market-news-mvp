from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, generate_api_key
from ..db import get_db
from ..models import ApiKey, User
from ..services.plans import get_plan

router = APIRouter(prefix="/keys", tags=["keys"])


class CreateKeyPayload(BaseModel):
    name: str


class KeyOut(BaseModel):
    id: int
    name: str
    prefix: str
    created_at: str
    last_used_at: str | None
    revoked: bool


class CreateKeyResponse(BaseModel):
    key: str
    meta: KeyOut


@router.get("", response_model=list[KeyOut])
def list_keys(u: User = Depends(current_user), db: Session = Depends(get_db)) -> list[KeyOut]:
    rows = db.execute(select(ApiKey).where(ApiKey.user_id == u.id).order_by(ApiKey.created_at.desc())).scalars().all()
    return [
        KeyOut(
            id=r.id,
            name=r.name,
            prefix=r.key_prefix,
            created_at=r.created_at.isoformat() + "Z",
            last_used_at=(r.last_used_at.isoformat() + "Z") if r.last_used_at else None,
            revoked=r.revoked,
        )
        for r in rows
    ]


@router.post("", response_model=CreateKeyResponse)
def create_key(
    body: CreateKeyPayload,
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CreateKeyResponse:
    plan = get_plan(u.plan)
    if plan.api_calls_per_day <= 0:
        raise HTTPException(402, "Your plan does not include API access. Upgrade to Pro or higher.")
    full, prefix, key_hash = generate_api_key()
    row = ApiKey(user_id=u.id, name=body.name[:64] or "default", key_prefix=prefix, key_hash=key_hash)
    db.add(row)
    db.commit()
    db.refresh(row)
    return CreateKeyResponse(
        key=full,
        meta=KeyOut(
            id=row.id,
            name=row.name,
            prefix=row.key_prefix,
            created_at=row.created_at.isoformat() + "Z",
            last_used_at=None,
            revoked=False,
        ),
    )


@router.delete("/{key_id}")
def revoke_key(key_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    row = db.get(ApiKey, key_id)
    if row is None or row.user_id != u.id:
        raise HTTPException(404, "Key not found")
    row.revoked = True
    db.add(row)
    db.commit()
    return {"ok": True}
