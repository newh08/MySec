import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import init_db
from app.services.discord_bot import SecretaryBot
from app.services.scheduler import start_scheduler, shutdown_scheduler

bot = SecretaryBot()


async def run_bot():
    try:
        async with bot:
            await bot.start(settings.discord_bot_token)
    except Exception as e:
        print(f"[Bot] Fatal error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    bot_task = asyncio.create_task(run_bot())
    await bot.wait_until_ready()

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
    return {
        "status": "ok",
        "bot_ready": bot.is_ready(),
        "active_sessions": len(bot.sessions),
    }
