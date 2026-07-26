import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import discord
from discord.ext import commands

from app.config import settings
from sqlalchemy import select

from app.database import async_session
from app.models import DailyLog, Schedule
from app.services.llm_service import (
    generate_daily_question,
    generate_followup_question,
    get_fixed_questions,
    summarize_and_extract_schedules,
)


class ConversationSession:
    def __init__(self, user_id: int, channel_id: int):
        self.user_id = user_id
        self.channel_id = channel_id
        self.fixed_questions: list[str] = get_fixed_questions()
        self.ai_question: str = ""
        self.answers: list[str] = []
        self.conversation_history: list[dict[str, str]] = []
        self.step: int = 0
        self.follow_up_count: int = 0
        self.max_follow_ups: int = settings.max_follow_ups
        self.is_active: bool = True
        self.created_at: datetime = datetime.now(timezone.utc)

    @property
    def total_questions(self) -> int:
        return len(self.fixed_questions) + 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "fixed_questions": self.fixed_questions,
            "ai_question": self.ai_question,
            "answers": self.answers,
            "conversation_history": self.conversation_history,
            "step": self.step,
            "follow_up_count": self.follow_up_count,
            "max_follow_ups": self.max_follow_ups,
            "is_active": self.is_active,
        }


class ReflectionCog(commands.Cog):
    def __init__(self, bot: "SecretaryBot"):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        print(f"[Discord] Ping command received from {ctx.author}")
        await ctx.send("pong!")

    @commands.command(name="회고", aliases=["start", "시작"])
    async def start_reflection(self, ctx: commands.Context):
        if ctx.author.id in self.bot.sessions:
            await ctx.send("⏳ 이미 진행 중인 회고 세션이 있습니다. `끝`이라고 입력해주세요.")
            return
        await ctx.send("🌙 **오늘의 회고를 시작합니다!** 잠시만 기다려주세요...")
        await self.bot.start_session(ctx.channel, ctx.author.id)

    @commands.command(name="취소", aliases=["cancel"])
    async def cancel_reflection(self, ctx: commands.Context):
        session = self.bot.sessions.pop(ctx.author.id, None)
        if session:
            session.is_active = False
            await ctx.send("❌ 회고 세션이 취소되었습니다.")
        else:
            await ctx.send("진행 중인 회고 세션이 없습니다.")


class SecretaryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.sessions: dict[int, ConversationSession] = {}

    async def on_ready(self):
        print(f"[Discord] Logged in as {self.user} (ID: {self.user.id})")
        for guild in self.guilds:
            print(f"[Discord] Connected to guild: {guild.name} (ID: {guild.id})")

    async def setup_hook(self):
        print("[Discord] setup_hook called - registering cogs")
        await self.add_cog(ReflectionCog(self))
        print("[Discord] Cogs registered")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        print(f"[Discord] Message from {message.author}: '{message.content[:50]}'")
        await self.process_commands(message)

        if message.author.id in self.sessions:
            session = self.sessions[message.author.id]
            if session.is_active:
                await self._handle_conversation_response(message, session)

    async def _handle_conversation_response(
        self, message: discord.Message, session: ConversationSession
    ):
        user_input = message.content.strip()
        session.answers.append(user_input)
        session.conversation_history.append(
            {"role": "user", "content": user_input}
        )

        end_keywords = ["끝", "완료", "종료", "그만", "없어"]
        if user_input in end_keywords:
            await self._end_session(message, session)
            return

        if session.step < session.total_questions:
            session.step += 1
            if session.step < session.total_questions:
                next_q = await self._get_current_question(session)
                await message.channel.send(next_q)
                return

        if session.follow_up_count < session.max_follow_ups:
            session.follow_up_count += 1
            followup = await generate_followup_question(
                session.conversation_history
            )
            if followup:
                session.conversation_history.append(
                    {"role": "assistant", "content": followup}
                )
                await message.channel.send(followup)
                return

        await self._end_session(message, session)

    async def _get_current_question(
        self, session: ConversationSession
    ) -> str:
        if session.step < len(session.fixed_questions):
            q = session.fixed_questions[session.step]
            session.conversation_history.append(
                {"role": "assistant", "content": q}
            )
            return f"📝 **Q{session.step + 1}.** {q}"
        elif session.step == len(session.fixed_questions):
            if not session.ai_question:
                session.ai_question = await generate_daily_question()
            session.conversation_history.append(
                {"role": "assistant", "content": session.ai_question}
            )
            return f"🤖 **AI 질문.** {session.ai_question}"
        return ""

    async def start_session(self, channel: discord.TextChannel, user_id: int):
        session = ConversationSession(user_id, channel.id)

        session.ai_question = await generate_daily_question()
        self.sessions[user_id] = session

        intro = (
            "하루를 돌아보며 질문에 하나씩 답변해 주세요.\n"
            "모든 질문에 답하면 AI가 꼬리 질문을 이어갈 수도 있어요.\n"
            "답변이 끝나면 `끝` 또는 `완료`라고 입력해 주세요.\n"
            "---"
        )
        await channel.send(intro)

        first_q = await self._get_current_question(session)
        session.step += 1
        await channel.send(first_q)

    async def _end_session(self, message: discord.Message, session: ConversationSession):
        session.is_active = False
        await message.channel.send(
            "⏳ **대화를 분석하고 요약을 생성 중입니다...**"
        )

        try:
            summary_md, schedules = await summarize_and_extract_schedules(
                session.conversation_history
            )

            async with async_session() as db_session:
                today = datetime.now(timezone.utc).date()

                result = await db_session.execute(
                    select(DailyLog).where(DailyLog.date == today)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    existing.summary_markdown = summary_md
                    existing.raw_conversation_json = json.dumps(
                        session.to_dict(), ensure_ascii=False
                    )
                    daily_log = existing
                else:
                    daily_log = DailyLog(
                        date=today,
                        summary_markdown=summary_md,
                        raw_conversation_json=json.dumps(
                            session.to_dict(), ensure_ascii=False
                        ),
                    )
                    db_session.add(daily_log)
                await db_session.flush()

                calendar_sync_needed = False
                for sched_data in schedules:
                    schedule_entry = Schedule(
                        log_id=daily_log.id,
                        title=sched_data.get("title", "제목 없음"),
                        start_time=datetime.fromisoformat(
                            sched_data.get("start_time", datetime.now().isoformat())
                        ),
                        end_time=datetime.fromisoformat(
                            sched_data.get("end_time", datetime.now().isoformat())
                        ),
                        location=sched_data.get("location"),
                        description=sched_data.get("description"),
                    )
                    db_session.add(schedule_entry)
                    calendar_sync_needed = True

                await db_session.commit()

            await message.channel.send(
                "✅ **회고가 저장되었습니다!**\n\n"
                f"{summary_md}"
            )

            if calendar_sync_needed and schedules:
                try:
                    from app.services.calendar_service import sync_schedules_to_google
                    synced = await sync_schedules_to_google(schedules)
                    if synced:
                        await message.channel.send(
                            "📅 **일정이 Google Calendar에 등록되었습니다!**"
                        )
                except Exception as e:
                    print(f"[Calendar Sync Error] {e}")

        except Exception as e:
            await message.channel.send(
                f"⚠️ **오류가 발생했습니다:** {e}"
            )
            print(f"[Session End Error] {e}")
        finally:
            self.sessions.pop(session.user_id, None)

    async def send_daily_reflection(self, channel_id: int, user_id: int):
        channel = self.get_channel(channel_id)
        if not channel:
            try:
                user = await self.fetch_user(user_id)
                channel = user.dm_channel or await user.create_dm()
            except Exception:
                print(f"[Scheduler] Cannot find channel {channel_id} or user {user_id}")
                return

        if user_id in self.sessions:
            await channel.send("⏳ 이미 진행 중인 회고 세션이 있습니다. 먼저 끝내주세요.")
            return

        await self.start_session(channel, user_id)
