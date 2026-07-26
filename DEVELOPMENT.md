# MySecretary — 개발 가이드

## 프로젝트 개요

미니 PC에서 24시간 Docker 기반으로 동작하는 개인 AI 비서 & 회고 대시보드 시스템.

- **매일 밤 23:00** Discord로 회고 질문 전송
- Gemini AI가 멀티턴 대화로 하루를 요약
- 추출된 일정을 Google Calendar에 자동 등록
- 웹 대시보드에서 회고록과 일정을 타임라인으로 조회

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 백엔드 | Python 3.12, FastAPI, SQLAlchemy (async) |
| 데이터베이스 | SQLite (aiosqlite) |
| 봇 | discord.py 2.4 |
| LLM | Google Gemini 2.5 Flash API |
| 스케줄러 | APScheduler (AsyncIOScheduler) |
| 캘린더 | Google Calendar API v3 |
| 프론트엔드 | Next.js 14, Tailwind CSS, shadcn/ui |
| 인프라 | Docker Compose |

---

## 프로젝트 구조

```
MySecretary/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 진입점, bot + 스케줄러 실행
│   │   ├── config.py              # pydantic-settings (.env)
│   │   ├── database.py            # SQLAlchemy async 엔진 + 세션
│   │   ├── models/
│   │   │   ├── daily_log.py       # daily_logs 테이블
│   │   │   └── schedule.py        # schedules 테이블
│   │   └── services/
│   │       ├── discord_bot.py     # Discord 봇 + 세션 관리
│   │       ├── llm_service.py     # Gemini API (질문, 꼬리 질문, 요약)
│   │       ├── scheduler.py       # APScheduler 일일 크론 (23:00)
│   │       └── calendar_service.py# Google Calendar 연동
│   ├── data/                      # SQLite DB (볼륨 마운트)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                   # Next.js App Router
│   │   ├── components/ui/         # shadcn/ui 컴포넌트
│   │   └── lib/utils.ts
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── DEVELOPMENT.md
└── .gitignore
```

---

## 환경 변수

`backend/.env.example`을 `backend/.env`로 복사 후 값을 입력하세요:

| 변수명 | 설명 |
|--------|------|
| `DISCORD_BOT_TOKEN` | Discord 봇 토큰 (Dev Portal) |
| `DISCORD_CHANNEL_ID` | 회고 메시지를 보낼 채널 ID |
| `DISCORD_USER_ID` | DM 폴백용 사용자 ID |
| `GEMINI_API_KEY` | Google AI Studio API 키 |
| `GEMINI_MODEL` | Gemini 모델명 (기본값: `gemini-2.5-flash`) |
| `GOOGLE_CALENDAR_CLIENT_ID` | Google OAuth 클라이언트 ID |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 |
| `GOOGLE_REFRESH_TOKEN` | Calendar API용 OAuth refresh 토큰 |
| `GOOGLE_CALENDAR_ID` | 캘린더 ID (기본값: `primary`) |
| `DATABASE_URL` | SQLite 연결 문자열 |
| `TIMEZONE` | 시간대 (기본값: `Asia/Seoul`) |
| `FIXED_QUESTION_COUNT` | 고정 질문 개수 (기본값: 5) |
| `MAX_FOLLOW_UPS` | 최대 AI 꼬리 질문 수 (기본값: 3) |

---

## 로컬 실행

### 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 입력 필요
uvicorn app.main:app --reload
```

### 프론트엔드

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

## Discord 봇 명령어

| 명령어 | 별칭 | 설명 |
|--------|------|------|
| `!회고` | `!start`, `!시작` | 회고 세션 즉시 시작 |
| `!취소` | `!cancel` | 진행 중인 세션 취소 |

세션 중에는 질문에 일반 채팅으로 답변하면 됩니다. `끝` / `완료` / `종료`를 입력하면 조기 종료됩니다.

---

## 아키텍처: 대화 흐름

```
23:00 KST (APScheduler)
       │
       ▼
Discord 봇 → 인사말 + 질문 5개 + AI 질문 1개 전송
       │
       ▼  (사용자 답변)
봇이 답변 수신 → 세션 히스토리에 저장
       │
       ▼  (꼬리 질문, 최대 3회)
Gemini로 꼬리 질문 생성 → 사용자에게 전송
       │
       ▼  (사용자 답변 또는 "끝")
Gemini로 최종 요청:
  1. Markdown 요약문
  2. JSON 일정 목록
       │
       ├──▶ DailyLog + Schedule → SQLite 저장
       └──▶ Schedule → Google Calendar 동기화 (실패해도 DB 저장은 유지)
```

---

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스 체크 + 봇 상태 |

---

## Git 워크플로우

```bash
# Develop 브랜치
git checkout develop
git add -A && git commit -m "..."
git push origin develop

# Master에 머지
git checkout master
git merge develop
git push origin master
git checkout develop
```

---

## 트러블슈팅

### "No module named 'discord'"
```bash
pip install -r requirements.txt
```

### 봇이 응답하지 않음
- `.env`의 `DISCORD_BOT_TOKEN` 확인
- Discord Developer Portal에서 봇의 `MESSAGE CONTENT INTENT` 활성화 필요

### Google Calendar 인증
1. Google Cloud Console → APIs & Services → Credentials
2. OAuth 2.0 클라이언트 ID (Desktop app) 생성
3. Google OAuth Playground에서 refresh token 발급

### 데이터베이스 lock 오류
SQLite는 한 번에 하나의 쓰기만 허용합니다. 백엔드 인스턴스가 하나만 실행 중인지 확인하세요.

### Calendar 동기오류 (DB 저장에는 영향 없음)
Calendar API 키/토큰이 없거나 오류가 발생해도 `daily_logs` 저장은 정상 완료됩니다.
일정 동기화만 건너뛰고 로그가 출력되므로 안심하세요.
