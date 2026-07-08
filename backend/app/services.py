import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings


HANDOFF_RE = re.compile(
    r"\b(call|callback|consultant|sales\s*(person|advisor)|human|agent|dealer|test drive|book|contact me|phone)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    content: str


def normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", query.lower())).strip()


async def classify_intent(message: str, settings: Settings) -> str:
    if HANDOFF_RE.search(message):
        return "wants_consultant"

    prompt = (
        "Classify the buyer message as exactly one label: normal_query or "
        "wants_consultant. wants_consultant means the user asks for a human, "
        "call, callback, dealer contact, booking, or test drive.\n"
        f"Message: {message}"
    )
    label = await call_gemini(prompt, settings, expect_json=False)
    label = (label or "").strip().lower()
    return "wants_consultant" if "wants_consultant" in label else "normal_query"


async def split_doubts(message: str, settings: Settings) -> list[str]:
    prompt = (
        "Split this car-buyer message into 1 to 3 concrete doubts. "
        "Return only a JSON array of short strings.\n"
        f"Message: {message}"
    )
    raw = await call_gemini(prompt, settings, expect_json=True)
    try:
        parsed = json.loads(raw or "[]")
        doubts = [str(item).strip() for item in parsed if str(item).strip()]
        if doubts:
            return doubts[:3]
    except json.JSONDecodeError:
        pass

    parts = re.split(r"\?|(?:\s+and\s+)|(?:\s*,\s*)", message)
    doubts = [part.strip(" .?!") for part in parts if len(part.strip(" .?!")) > 2]
    return (doubts or [message.strip()])[:3]


async def retrieve_web(
    car_context: str,
    doubt: str,
    settings: Settings,
) -> list[SearchResult]:
    if not settings.tavily_api_key:
        return []

    query = (
        f"{car_context} {doubt} India official Mahindra CarWale CarDekho "
        "ZigWheels latest price specs"
    )
    payload: dict[str, Any] = {
        "query": query,
        "search_depth": "advanced",
        "include_answer": False,
        "max_results": 5,
        "include_domains": [
            "mahindra.com",
            "auto.mahindra.com",
            "carwale.com",
            "cardekho.com",
            "zigwheels.com",
        ],
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json=payload,
            headers={"Authorization": f"Bearer {settings.tavily_api_key}"},
        )
        if response.status_code in {401, 403, 422}:
            legacy_payload = {"api_key": settings.tavily_api_key, **payload}
            response = await client.post(
                "https://api.tavily.com/search",
                json=legacy_payload,
            )
        response.raise_for_status()
        data = response.json()

    return [
        SearchResult(
            title=str(item.get("title") or "Source"),
            url=str(item.get("url") or ""),
            content=str(item.get("content") or item.get("raw_content") or ""),
        )
        for item in data.get("results", [])
        if item.get("content") or item.get("raw_content")
    ]


async def synthesize_answer(
    car_context: str,
    doubt: str,
    results: list[SearchResult],
    settings: Settings,
) -> str:
    if not results:
        return (
            "I couldn't confirm this from live sources right now. For this demo, "
            "I won't invent specs or prices. Please try again in a moment or ask "
            "for a consultant callback."
        )

    source_block = "\n\n".join(
        f"Source: {result.title}\nURL: {result.url}\nExcerpt: {result.content[:900]}"
        for result in results[:5]
    )
    prompt = (
        "You are an AI sales assistant for an Indian car dealership. "
        "Use only the retrieved source excerpts. If a number or claim is not "
        "confirmed by sources, say it cannot be confirmed. Write a persuasive "
        "but factual sales story in 3-5 short sentences, then include source "
        "names in parentheses.\n\n"
        f"Car context: {car_context}\n"
        f"Customer doubt: {doubt}\n\n"
        f"Retrieved sources:\n{source_block}"
    )
    answer = await call_gemini(prompt, settings, expect_json=False)
    if not answer:
        return (
            "I found live sources, but couldn't synthesize a reliable answer at "
            "the moment. I won't guess on specifications or prices."
        )
    return answer.strip()


async def call_gemini(
    prompt: str,
    settings: Settings,
    *,
    expect_json: bool,
) -> str:
    if not settings.gemini_api_key:
        return ""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 700,
        },
    }
    if expect_json:
        body["generationConfig"]["responseMimeType"] = "application/json"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=body)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError:
        return ""

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return ""
