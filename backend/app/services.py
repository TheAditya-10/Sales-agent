import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx

from .config import Settings

logger = logging.getLogger(__name__)


HANDOFF_RE = re.compile(
    r"\b(call|callback|consultant|sales\s*(person|advisor)|human|agent|dealer|test drive|book|contact me|phone)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    content: str


@dataclass(frozen=True)
class DoubtDetection:
    category: str
    extracted_query: str


retrieval_cache: dict[tuple[str, str], list[SearchResult]] = {}


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


async def answer_doubts_with_retrieval(
    car_context: str,
    doubts: list[str],
    settings: Settings,
    *,
    on_status: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
) -> list[dict[str, str]]:
    answers: list[dict[str, str]] = []
    for index, doubt in enumerate(doubts, start=1):
        normalized = normalize_query(doubt)
        cache_key = (car_context.strip().lower(), normalized)

        if on_status:
            await on_status(
                {
                    "status": "searching_web",
                    "doubt": doubt,
                    "index": index,
                    "total": len(doubts),
                }
            )

        if cache_key in retrieval_cache:
            results = retrieval_cache[cache_key]
        else:
            try:
                results = await retrieve_web(car_context, doubt, settings)
            except Exception:
                results = []
            retrieval_cache[cache_key] = results

        if on_status:
            await on_status({"status": "comparing_specs", "doubt": doubt})
            await on_status({"status": "synthesizing", "doubt": doubt})

        answer = await synthesize_answer(car_context, doubt, results, settings)
        answers.append({"doubt": doubt, "answer": answer})

    return answers


async def detect_car_buying_doubt(text: str, settings: Settings) -> DoubtDetection | None:
    prompt = (
        "You are listening to a car-buying call. Decide whether the transcript "
        "contains a recognizable car-buying doubt or objection. Examples include "
        "price, EMI, mileage, safety, ADAS, space, resale, maintenance, delivery, "
        "comparison, variant confusion, features, or trust objections. Return only "
        "JSON: null if there is no clear doubt; otherwise "
        "{\"category\":\"short_snake_case_category\",\"extracted_query\":\"the buyer's concrete doubt\"}.\n\n"
        f"Transcript window:\n{text}"
    )
    raw = await call_gemini(prompt, settings, expect_json=True)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    category = str(parsed.get("category") or "").strip().lower()
    extracted_query = str(parsed.get("extracted_query") or "").strip()
    if not category or not extracted_query:
        return None
    category = re.sub(r"[^a-z0-9_]+", "_", category).strip("_")[:80]
    if not category:
        return None
    return DoubtDetection(category=category, extracted_query=extracted_query)


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

    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 700,
            # Gemini 2.5 models default to spending most of maxOutputTokens on
            # internal "thinking" tokens, which was silently truncating every
            # synthesized answer to a sentence fragment. These calls are simple
            # classification/synthesis tasks that don't need extended reasoning.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    if expect_json:
        body["generationConfig"]["responseMimeType"] = "application/json"

    async with httpx.AsyncClient(timeout=30) as client:
        for model in gemini_model_candidates(settings.gemini_model):
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={settings.gemini_api_key}"
            )
            try:
                response = await client.post(url, json=body)
                if response.status_code == 404:
                    logger.warning("Gemini model %s is unavailable; trying fallback", model)
                    continue
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {400, 404}:
                    logger.warning(
                        "Gemini model %s failed with %s; trying fallback",
                        model,
                        exc.response.status_code,
                    )
                    continue
                return ""
            except httpx.HTTPError:
                return ""

            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                return ""

    return ""


def gemini_model_candidates(configured_model: str) -> list[str]:
    configured = configured_model.removeprefix("models/").strip()
    candidates = [
        configured,
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash",
    ]
    return list(dict.fromkeys(model for model in candidates if model))
