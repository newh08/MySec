import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import google.generativeai as genai

from app.config import settings

executor = ThreadPoolExecutor(max_workers=2)

FIXED_QUESTIONS = [
    "오늘 하루 중 가장 기억에 남는 순간은 무엇인가요?",
    "오늘 처리한 가장 중요한 업무나 할 일은 무엇인가요?",
    "오늘 감사했던 일이나 사람이 있었다면 알려주세요.",
    "오늘 아쉬웠던 점이나 내일 더 잘하고 싶은 점은 무엇인가요?",
    "내일 꼭 해야 할 일이나 예정된 일정이 있나요?",
]


def _init_genai():
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


def _call_gemini(prompt: str) -> str:
    model = _init_genai()
    response = model.generate_content(prompt)
    return response.text.strip()


FALLBACK_QUESTIONS = [
    "오늘 하루 중 가장 의미 있었던 순간은 언제였나요?",
    "오늘 새롭게 배운 것이나 깨달은 점이 있다면 무엇인가요?",
    "오늘의 에너지 레벨을 10점 만점으로 표현한다면 몇 점인가요?",
]


async def generate_daily_question() -> str:
    import random
    prompt = (
        "너는 사용자의 하루를 돌아보게 하는 AI 비서야.\n"
        "사용자의 지난 답변은 아직 없으니, 날씨나 요일 등 일반적인 맥락을 고려해서\n"
        "오늘 하루에 대해 자연스럽게 생각해볼 수 있는 질문을 1개만 생성해줘.\n"
        "질문은 2~3문장 이내로 간결하게 해줘."
    )
    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _call_gemini, prompt),
            timeout=10,
        )
        return result
    except Exception as e:
        print(f"[LLM] generate_daily_question failed: {e}")
        return random.choice(FALLBACK_QUESTIONS)


async def generate_followup_question(
    conversation_history: list[dict[str, str]]
) -> str | None:
    history_text = "\n".join(
        f"{'AI' if msg['role'] == 'assistant' else '사용자'}: {msg['content']}"
        for msg in conversation_history
    )
    prompt = (
        "다음은 사용자와의 회고 대화 내역이야.\n"
        f"{history_text}\n\n"
        "사용자의 답변을 바탕으로 자연스러운 꼬리 질문을 1개만 생성해줘.\n"
        "사용자가 이미 충분히 자세히 답변했다면 'END'라고만 응답하고,\n"
        "더 대화를 이어갈 가치가 있다면 1~2문장의 질문을 해줘.\n"
        "답변은 질문만 출력해줘 (따옴표 없이)."
    )
    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _call_gemini, prompt),
            timeout=10,
        )
    except Exception as e:
        print(f"[LLM] generate_followup_question failed: {e}")
        return None
    if result.strip().upper() == "END":
        return None
    return result


async def summarize_and_extract_schedules(
    conversation_history: list[dict[str, str]]
) -> tuple[str, list[dict[str, Any]]]:
    history_text = "\n".join(
        f"{'AI' if msg['role'] == 'assistant' else '사용자'}: {msg['content']}"
        for msg in conversation_history
    )
    prompt = (
        "다음은 사용자의 하루 회고 대화 내역이야.\n"
        "---\n"
        f"{history_text}\n"
        "---\n"
        "위 내용을 분석해서 아래 2가지를 JSON 형식으로 출력해줘.\n"
        "```json\n"
        "{\n"
        '  "summary_markdown": "### 오늘의 회고\\n\\n**기억에 남는 순간**\\n- ...\\n\\n**업무/할 일**\\n- ...\\n\\n**감사한 일**\\n- ...\\n\\n**아쉬운 점**\\n- ...\\n\\n**내일 일정**\\n- ...",\n'
        '  "schedules": [\n'
        '    {\n'
        '      "title": "일정 제목",\n'
        '      "start_time": "2025-01-01T09:00:00",\n'
        '      "end_time": "2025-01-01T10:00:00",\n'
        '      "location": "장소 (없으면 null)",\n'
        '      "description": "설명 (없으면 null)"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n"
        "규칙:\n"
        "- summary_markdown은 한국어 Markdown 형식으로 작성해줘.\n"
        "- schedules 배열은 일정이 없으면 빈 배열([])로 해줘.\n"
        "- start_time, end_time은 ISO 8601 형식 (yyyy-MM-ddTHH:mm:ss).\n"
        "- 오늘이나 내일 날짜로 추정해서 채워줘.\n"
        "- JSON 외의 다른 텍스트는 출력하지 마."
    )
    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _call_gemini, prompt),
            timeout=15,
        )
    except Exception as e:
        print(f"[LLM] summarize_and_extract_schedules failed: {e}")
        return _fallback_summary(history_text), []

    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_str = result.strip()

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return _fallback_summary(history_text), []

    summary_md = data.get("summary_markdown", _fallback_summary(history_text))
    schedules = data.get("schedules", [])
    return summary_md, schedules


def _fallback_summary(history_text: str) -> str:
    return f"### 오늘의 회고\n\n{history_text[:500]}\n\n*자동 요약 실패 - 원본 대화를 참고하세요.*"


import asyncio


def get_fixed_questions() -> list[str]:
    count = settings.fixed_question_count
    return FIXED_QUESTIONS[:count]
