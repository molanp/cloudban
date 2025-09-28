from tortoise import fields
from tortoise.models import Model


class BanRecord(Model):
    """黑名单记录"""

    id = fields.IntField(pk=True)
    """自增ID"""
    target_type = fields.CharField(max_length=10)
    """目标类型，qq/group"""
    target_id = fields.CharField(max_length=20)
    """目标ID"""
    reason = fields.TextField(null=True)
    """原因"""
    evidence = fields.JSONField(default=[])
    """证据"""
    hwic = fields.TextField()
    """上报者HWIC"""
    ip = fields.CharField(max_length=45)
    """上报者IP"""
    create_at = fields.DatetimeField(auto_now_add=True)
    """提交时间UTC"""
    update_at = fields.DatetimeField(auto_now=True)
    """更新时间UTC"""
    status = fields.CharField(max_length=20, default="pending")
    """状态"""
    note = fields.TextField(null=True)
    """备注"""

class BlockedHWIC(Model):
    """封禁的HWIC"""

    id = fields.IntField(pk=True)
    """自增ID"""
    hwic = fields.TextField()
    """HWIC"""
    reason = fields.TextField(null=True)
    """封禁理由"""
    blocked_at = fields.DatetimeField(auto_now_add=True)
    """封禁时间"""


class AdminAction(Model):
    """管理员操作记录"""

    id = fields.IntField(pk=True)
    """自增ID"""
    user = fields.CharField(max_length=32)
    """操作者"""
    action = fields.CharField(max_length=64)
    """操作"""
    target_id = fields.IntField()
    """目标ID"""
    detail = fields.TextField()
    """详情"""
    timestamp = fields.DatetimeField(auto_now_add=True)
    """操作时间"""
