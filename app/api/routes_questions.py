from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import json
import re
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

_PROMPT_PREFIX = """\
You are an expert interview coach. Given a job description, generate exactly 5 behavioral and 5 technical/skills interview questions.

Behavioral questions must use STAR-method prompts (covering areas like: leadership, teamwork, conflict resolution, adaptability, and problem-solving).
Technical questions must target the specific skills, tools, languages, and responsibilities in the job description. If the description is brief, infer appropriate technical questions for the role type.

Respond ONLY with valid JSON — no explanation, no markdown fences:
{
  "behavioral": ["question1", "question2", "question3", "question4", "question5"],
  "technical": ["question1", "question2", "question3", "question4", "question5"]
}

Job Description:
"""


class QuestionRequest(BaseModel):
    job_description: str


def _parse_response(content: str) -> dict:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in AI response")
        data = json.loads(match.group())

    behavioral = data.get("behavioral", [])
    technical = data.get("technical", [])

    if not isinstance(behavioral, list) or not isinstance(technical, list):
        raise ValueError("Unexpected response structure from AI")

    placeholder = "Question not available — please try regenerating."
    behavioral = (behavioral + [placeholder] * 5)[:5]
    technical = (technical + [placeholder] * 5)[:5]

    return {"behavioral": behavioral, "technical": technical}


@router.post("/generate-questions")
async def generate_questions(body: QuestionRequest):
    jd = body.job_description.strip()

    if not jd:
        raise HTTPException(status_code=400, detail="Please enter a job description.")

    if len(jd) > 8000:
        jd = jd[:8000]

    try:
        if ANTHROPIC_API_KEY:
            return await _call_anthropic(jd)
        elif OPENAI_API_KEY:
            return await _call_openai(jd)
        else:
            raise HTTPException(
                status_code=503,
                detail="Question generation is not available on this server (no AI API key configured).",
            )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error("AI API HTTP error %s: %s", e.response.status_code, e.response.text[:300])
        raise HTTPException(status_code=502, detail="The AI service returned an error. Please try again.")
    except Exception as e:
        logger.error("Question generation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate questions. Please try again.")


async def _call_openai(jd: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": _PROMPT_PREFIX + jd}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _parse_response(content)


async def _call_anthropic(jd: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": _PROMPT_PREFIX + jd}],
            },
        )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"]
        return _parse_response(content)
