from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

scheduler = AsyncIOScheduler(timezone=settings.timezone)


def start_scheduler(bot):
    channel_id = int(settings.discord_channel_id)
    user_id = int(settings.discord_user_id)

    trigger = CronTrigger(hour=23, minute=0, timezone=settings.timezone)

    scheduler.add_job(
        func=_trigger_reflection,
        trigger=trigger,
        args=[bot, channel_id, user_id],
        id="daily_reflection",
        name="Daily Reflection at 23:00 KST",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    print(
        f"[Scheduler] Daily reflection scheduled at 23:00 ({settings.timezone})"
    )


async def _trigger_reflection(bot, channel_id: int, user_id: int):
    print(
        f"[Scheduler] Triggering daily reflection at {datetime.now()}"
    )
    try:
        await bot.send_daily_reflection(channel_id, user_id)
    except Exception as e:
        print(f"[Scheduler] Error: {e}")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
