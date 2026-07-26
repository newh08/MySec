# MySecretary — Development Guide

## Project Overview

Mini PC에서 24시간 Docker 기반으로 동작하는 개인 AI 비서 & 회고 대시보드 시스템.

- **매일 밤 23:00** Discord로 회고 질문 전송
- Gemini AI가 멀티턴 대화로 하루를 요약
- 추출된 일정을 Google Calendar에 자동 등록
- 웹 대시보드에서 회고록과 일정을 타임라인으로 조회

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async) |
| Database | SQLite (via aiosqlite) |
| Bot | discord.py 2.4 |
| LLM | Google Gemini 2.5 Flash API |
| Scheduler | APScheduler (AsyncIOScheduler) |
| Calendar | Google Calendar API v3 |
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui |
| Infra | Docker Compose |

---

## Project Structure

```
MySecretary/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint, bot + scheduler launch
│   │   ├── config.py              # pydantic-settings (.env)
│   │   ├── database.py            # SQLAlchemy async engine + session
│   │   ├── models/
│   │   │   ├── daily_log.py       # daily_logs table
│   │   │   └── schedule.py        # schedules table
│   │   └── services/
│   │       ├── discord_bot.py     # Discord bot + session management
│   │       ├── llm_service.py     # Gemini API (question, follow-up, summary)
│   │       ├── scheduler.py       # APScheduler daily cron (23:00)
│   │       └── calendar_service.py# Google Calendar sync
│   ├── data/                      # SQLite DB (volume mount)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   ├── components/ui/         # shadcn/ui components
│   │   └── lib/utils.ts
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── DEVELOPMENT.md
└── .gitignore
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Description |
|----------|-------------|
| `DISCORD_BOT_TOKEN` | Discord bot token (from Dev Portal) |
| `DISCORD_CHANNEL_ID` | Channel ID for reflection messages |
| `DISCORD_USER_ID` | User ID for DM fallback |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `GEMINI_MODEL` | Gemini model name (default: `gemini-2.5-flash`) |
| `GOOGLE_CALENDAR_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REFRESH_TOKEN` | OAuth refresh token for Calendar API |
| `GOOGLE_CALENDAR_ID` | Calendar ID (default: `primary`) |
| `DATABASE_URL` | SQLite connection string |
| `TIMEZONE` | Timezone (default: `Asia/Seoul`) |
| `FIXED_QUESTION_COUNT` | Number of fixed questions (default: 5) |
| `MAX_FOLLOW_UPS` | Max AI follow-up questions (default: 3) |

---

## Running Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose

```bash
docker compose up --build
```

---

## Discord Bot Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `!회고` | `!start`, `!시작` | Start a reflection session immediately |
| `!취소` | `!cancel` | Cancel the current session |

During a session, users reply to questions normally. Type `끝` / `완료` / `종료` to end early.

---

## Architecture: Conversation Flow

```
23:00 KST (APScheduler)
       │
       ▼
Discord Bot sends intro + Q1..Q5 + AI question
       │
       ▼  (user replies)
Bot receives answer → stores in session history
       │
       ▼  (follow-up rounds, max 3)
Bot generates AI follow-up question via Gemini
       │
       ▼  (user replies or says "끝")
Bot sends to Gemini for:
  1. Markdown summary
  2. JSON schedule list
       │
       ├──▶ Save DailyLog + Schedule to SQLite
       └──▶ Sync schedules to Google Calendar
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + bot status |

---

## Git Workflow

```bash
# Develop branch
git checkout develop
git add -A && git commit -m "..."
git push origin develop

# Merge to master
git checkout master
git merge develop
git push origin master
git checkout develop
```

---

## Troubleshooting

### "No module named 'discord'"
```bash
pip install -r requirements.txt
```

### Bot not responding
- Check `DISCORD_BOT_TOKEN` in `.env`
- Ensure bot has `MESSAGE CONTENT INTENT` enabled in Discord Developer Portal

### Google Calendar auth
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Desktop app)
3. Run Google's OAuth playground once to get refresh token

### Database lock errors
SQLite allows one writer at a time. Ensure only one backend instance runs.
