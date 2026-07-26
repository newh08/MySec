import asyncio

from contextlib import asynccontextmanager

import discord
from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.services.discord_bot import SecretaryBot
from app.services.scheduler import start_scheduler, shutdown_scheduler

bot = SecretaryBot()


async def run_bot():
    try:
        async with bot:
            await bot.start(settings.discord_bot_token, reconnect=True)
    except discord.LoginFailure:
        print("[Bot] Login failed: invalid token.")
    except Exception as e:
        print(f"[Bot] Fatal error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    bot_task = asyncio.create_task(run_bot())
    try:
        await asyncio.wait_for(bot.wait_until_ready(), timeout=15)
    except asyncio.TimeoutError:
        print("[Main] Bot did not connect within 15s. Continuing without bot.")

    start_scheduler(bot)

    yield

    shutdown_scheduler()
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="MySecretary API", lifespan=lifespan)


@app.get("/health")
async def health():
    guild_count = len(bot.guilds) if bot.is_ready() else 0
    return {
        "status": "ok",
        "bot_ready": bot.is_ready(),
        "bot_user": str(bot.user) if bot.is_ready() else None,
        "guild_count": guild_count,
        "active_sessions": len(bot.sessions),
        "invite_url": (
            f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&permissions=3072"
            if bot.is_ready()
            else None
        ),
    }
