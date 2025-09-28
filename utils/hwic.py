from models import BlockedHWIC


async def is_blocked_hwic(hwic: str) -> bool:
    return await BlockedHWIC.filter(hwic=hwic).exists()


async def sync_block_hwic(hwic: str, reason: str):
    exists = await BlockedHWIC.get_or_none(hwic=hwic)
    if not exists:
        await BlockedHWIC.create(hwic=hwic, reason=reason)
