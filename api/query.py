from fastapi import APIRouter, Query
from models import BanRecord

router = APIRouter()

@router.get("/banlist")
async def query_ban(
    target_type: str = Query(..., regex="^(qq|group)$"),
    target_id: str = Query(..., min_length=5, max_length=20)
):
    records = await BanRecord.filter_cached(
        target_type=target_type,
        target_id=target_id,
        status="approved"
    )

    if not records:
        return {"banned": False}
    record = records[0]

    return {
        "banned": True,
        "count": len(records),
        "reason": record.reason,
        "evidence": record.evidence,
        "create_at": record.create_at,
        "update_at": record.update_at,
    }

@router.get("/public_banlist")
async def public_banlist(page: int = 1, page_size: int = 10):
    if page <= 0 or page_size <= 0 or page_size > 100:
        return {"error": "Invalid page or page_size"}
    qs = BanRecord.filter(status="approved").order_by("-update_at")
    total = await qs.count()
    records = await qs.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "records": [
            {
                "create_at": r.create_at,
                "update_at": r.update_at,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "reason": r.reason,
                "evidence": r.evidence
            }
            for r in records
        ]
    }