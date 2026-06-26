from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import httpx
import os
import io
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


_RESUME_PROMPT = """\
You are a resume keyword analyzer. Given a job description and a resume, extract technical skills, tools, technologies, frameworks, languages, and domain keywords.

Categorize them into exactly three groups:
- "matching": skills/technologies present in BOTH the resume AND the job description
- "missing": important skills/technologies mentioned in the JD that are NOT found in the resume
- "somewhat_related": skills that are adjacent or partially overlapping (e.g., "AWS vs GCP", "React vs Vue.js", "Postgres vs MySQL")

Rules:
- Focus only on technical skills, tools, languages, frameworks, certifications, and domain-specific keywords. Ignore generic soft skills.
- For "somewhat_related", write each item as a short comparison string like "AWS (resume) vs GCP (JD)".
- Limit each list to the 15 most important items.
- If a category has no items, return an empty array.

Respond ONLY with valid JSON — no explanation, no markdown fences:
{{
  "matching": ["Python", "SQL"],
  "missing": ["Kubernetes", "Terraform"],
  "somewhat_related": ["AWS (resume) vs GCP (JD)"]
}}

Job Description:
{jd}

Resume:
{resume}
"""


def _extract_pdf_text(content: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx_text(content: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)


def _parse_resume_response(content: str) -> dict:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in AI response")
        data = json.loads(match.group())

    return {
        "matching": [str(k) for k in data.get("matching", [])],
        "missing": [str(k) for k in data.get("missing", [])],
        "somewhat_related": [str(k) for k in data.get("somewhat_related", [])],
    }


@router.post("/analyze-resume")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    filename = resume.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    content = await resume.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 5MB.")

    try:
        resume_text = _extract_pdf_text(content) if ext == "pdf" else _extract_docx_text(content)
    except Exception as e:
        logger.error("Resume parsing error: %s", e)
        raise HTTPException(status_code=400, detail="Could not read the file. Ensure it is a valid PDF or DOCX.")

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted. The file may be image-based or empty.")

    jd = job_description.strip()
    if not jd:
        raise HTTPException(status_code=400, detail="Please provide a job description before analyzing.")

    prompt = _RESUME_PROMPT.format(jd=jd[:4000], resume=resume_text[:6000])

    try:
        if ANTHROPIC_API_KEY:
            return await _call_anthropic_prompt(prompt)
        elif OPENAI_API_KEY:
            return await _call_openai_prompt(prompt)
        else:
            raise HTTPException(status_code=503, detail="Resume analysis unavailable (no AI API key configured).")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        logger.error("AI API error %s: %s", e.response.status_code, e.response.text[:300])
        raise HTTPException(status_code=502, detail="The AI service returned an error. Please try again.")
    except Exception as e:
        logger.error("Resume analysis failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to analyze resume. Please try again.")


async def _call_openai_prompt(prompt: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        return _parse_resume_response(resp.json()["choices"][0]["message"]["content"])


async def _call_anthropic_prompt(prompt: str) -> dict:
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
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return _parse_resume_response(resp.json()["content"][0]["text"])


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
