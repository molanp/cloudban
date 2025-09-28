# api/report.py

from typing import Literal
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from models import BanRecord
from utils.hwic import is_blocked_hwic

router = APIRouter()

class ReportRequest(BaseModel):
    target_type: Literal["qq", "group"]
    """上报类型"""
    target_id: str = Field(..., min_length=5, max_length=20)
    """上报对象ID"""
    reason: str = Field(..., min_length=5, max_length=500)
    """原因"""
    evidence: list[str]
    """证据"""
    hwic: str = Field(..., min_length=10, max_length=128)
    """HWIC"""

@router.post("/report")
async def report_ban(data: ReportRequest, request: Request):
    ip = getattr(request.client, "host", None)

    if await is_blocked_hwic(data.hwic):
        raise HTTPException(status_code=403, detail="HWIC is blocked")

    await BanRecord.create(
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        evidence=data.evidence,
        hwic=data.hwic,
        ip=ip,
        status="pending"
    )

    return {"message": "Report submitted successfully"}