from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from models import AdminAction, BanRecord, BlockedHWIC
from utils.security import (
    is_login,
    require_login,
)


class OperateRecord(BaseModel):
    record_id: int
    """记录ID"""
    note: str = ""
    """备注"""


router = APIRouter()


@router.post("/check_token")
async def _(user=Depends(require_login)):
    return {"user": user}


@router.post("/approve_ban")
async def approve_ban(data: OperateRecord):
    record = await BanRecord.get_or_none(id=data.record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Record already processed")

    record.status = "approved"
    record.note = data.note
    await record.save()

    return {"message": "Ban record approved"}


@router.post("/reject_ban")
async def reject_ban(data: OperateRecord):
    record = await BanRecord.get_or_none(id=data.record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if record.status != "pending":
        raise HTTPException(status_code=400, detail="Record already processed")

    record.status = "rejected"
    record.note = data.note
    await record.save()

    return {"message": "Ban record rejected"}


@router.post("/set_hwic_block")
async def set_hwic_block(hwic: str, block: bool, reason: str = ""):
    if block:
        # SQLite 封禁记录（去重）
        exists = await BlockedHWIC.get_or_none(hwic=hwic)
        if not exists:
            await BlockedHWIC.create(hwic=hwic, reason=reason)

        return {"message": "HWIC blocked"}
    else:
        # SQLite 删除记录
        deleted = await BlockedHWIC.filter(hwic=hwic).delete()
        return {"message": "HWIC unblocked", "deleted": deleted}


@router.get("/list_pending")
async def list_pending():
    records = (
        await BanRecord.filter(status="pending").order_by("-update_at").limit(100).all()
    )

    return [
        {
            "id": r.id,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "reason": r.reason,
            "evidence": r.evidence,
            "hwic": r.hwic,
            "ip": r.ip,
            "update_at": r.update_at,
            "create_at": r.create_at,
        }
        for r in records
    ]


@router.get("/ban_stats")
async def ban_stats():
    total = await BanRecord.all().count()
    approved = await BanRecord.filter(status="approved").count()
    rejected = await BanRecord.filter(status="rejected").count()
    pending = await BanRecord.filter(status="pending").count()

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
    }


@router.post("/modify_ban_record")
async def modify_ban_record(
    record_id: int,
    reason: str = "",
    evidence: list[str] | None = None,
    status: str = "",
    note: str = "",
    Authorization: str = Header(""),
):
    if evidence is None:
        evidence = []
    record = await BanRecord.get_or_none(id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    updates = []
    if reason:
        record.reason = reason
        updates.append("reason")
    if evidence:
        record.evidence = evidence
        updates.append("evidence")
    if status:
        record.status = status
        updates.append("status")
    if note:
        record.note = note
        updates.append("note")

    await record.save()

    # 写入操作记录
    user = is_login(Authorization)
    await AdminAction.create(
        user=user,
        action="modify_ban_record",
        target_id=record_id,
        detail=f"Updated fields: {', '.join(updates)}",
    )

    return {"message": "Record updated", "updated": updates}


@router.get("/query_ban_records")
async def query_ban_records(
    target_type: str = "",
    status: str = "",
    offset: int = 0,
    limit: int = 50,
):
    q = BanRecord.all()

    if target_type in {"qq", "group"}:
        q = q.filter(target_type=target_type)
    if status in {"pending", "approved", "rejected"}:
        q = q.filter(status=status)

    records = await q.order_by("-update_at").offset(offset).limit(limit)

    return [
        {
            "id": r.id,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "reason": r.reason,
            "evidence": r.evidence,
            "hwic": r.hwic,
            "ip": r.ip,
            "status": r.status,
            "note": r.note,
            "update_at": r.update_at,
            "create_at": r.create_at,
        }
        for r in records
    ]


@router.get("/admin_actions")
async def admin_actions(offset: int = 0, limit: int = 50):
    actions = await AdminAction.all().order_by("-timestamp").offset(offset).limit(limit)
    return [
        {
            "admin": a.user,
            "action": a.action,
            "target_id": a.target_id,
            "detail": a.detail,
            "timestamp": a.timestamp.isoformat(),
        }
        for a in actions
    ]


@router.get("/ban_stats_detail")
async def ban_stats_detail():
    from tortoise.functions import Count
    from datetime import datetime, timedelta

    # 时间趋势（过去7天）
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    trend = []
    for i in range(7):
        day = today - timedelta(days=i)
        count = await BanRecord.filter(
            update_at__gte=day.replace(hour=0, minute=0, second=0, microsecond=0),
            update_at__lte=day.replace(
                hour=23, minute=59, second=59, microsecond=999999
            ),
        ).count()
        trend.append({"date": day.isoformat(), "count": count})

    # 来源分析
    hwic_stats = (
        await BanRecord.annotate(c=Count("hwic"))
        .group_by("hwic")
        .order_by("-c")
        .limit(5)
    )
    ip_stats = (
        await BanRecord.annotate(c=Count("ip")).group_by("ip").order_by("-c").limit(5)
    )
    type_stats = await BanRecord.annotate(c=Count("target_type")).group_by(
        "target_type"
    )

    return {
        "trend": list(reversed(trend)),
        "hwic": [
            {
                "hwic": r.hwic,
                "count": r.c,  # pyright: ignore[reportAttributeAccessIssue]
            }
            for r in hwic_stats
        ],
        "ip": [
            {"ip": r.ip, "count": r.c}  # pyright: ignore[reportAttributeAccessIssue]
            for r in ip_stats
        ],
        "type": [
            {
                "type": r.target_type,
                "count": r.c,  # pyright: ignore[reportAttributeAccessIssue]
            }
            for r in type_stats
        ],
    }
