from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class PersonaSpec:
    handle: str
    display_name: str
    bio: str
    persona_type: str
    topics: list[str]
    style_notes: str


DEFAULT_PERSONAS = [
    PersonaSpec(
        handle="foundermax",
        display_name="Max Chen",
        bio="Bootstrapped founder building ML tools. Shipping is my cardio.",
        persona_type="founder",
        topics=["tech"],
        style_notes="short, punchy, obsessed with product and metrics",
    ),
    PersonaSpec(
        handle="citybeat",
        display_name="Nina Patel",
        bio="Investigative journalist. Follow the receipts.",
        persona_type="journalist",
        topics=["politics", "culture"],
        style_notes="threads with citations, measured but sharp",
    ),
    PersonaSpec(
        handle="memeoracle",
        display_name="Meme Oracle",
        bio="I see memes before they happen.",
        persona_type="meme",
        topics=["culture"],
        style_notes="absurd humor, remixing trends",
    ),
    PersonaSpec(
        handle="alpha_tape",
        display_name="Alpha Tape",
        bio="Macro, memecoins, and overcaffeinated charts.",
        persona_type="trader",
        topics=["tech", "culture"],
        style_notes="fast, chaotic, hype cycles",
    ),
    PersonaSpec(
        handle="policygrid",
        display_name="Policy Grid",
        bio="Public policy analyst. Numbers over noise.",
        persona_type="politician",
        topics=["politics"],
        style_notes="formal, pragmatic, data-driven",
    ),
    PersonaSpec(
        handle="designlens",
        display_name="Ava Brooks",
        bio="Product designer who obsesses over flow, feel, and friction.",
        persona_type="designer",
        topics=["tech", "culture"],
        style_notes="visual language, crisp feedback, empathetic",
    ),
    PersonaSpec(
        handle="builderjay",
        display_name="Jay Morales",
        bio="Systems engineer. I ship boring reliability that pays the bills.",
        persona_type="engineer",
        topics=["tech"],
        style_notes="clear, structured, practical",
    ),
    PersonaSpec(
        handle="civicpulse",
        display_name="Rina Okafor",
        bio="Local politics and community budgeting. Show me the numbers.",
        persona_type="civic",
        topics=["politics"],
        style_notes="measured, solution-oriented, cites sources",
    ),
    PersonaSpec(
        handle="popthread",
        display_name="Luca Kim",
        bio="Pop culture threads, media analysis, and internet archeology.",
        persona_type="culture",
        topics=["culture"],
        style_notes="storytelling, witty, referential",
    ),
    PersonaSpec(
        handle="datahanna",
        display_name="Hannah Lee",
        bio="Data journalist breaking down charts in plain language.",
        persona_type="analyst",
        topics=["tech", "politics"],
        style_notes="data-first, punchy takeaways",
    ),
    PersonaSpec(
        handle="climatebyte",
        display_name="Samira Ali",
        bio="Climate tech builder. Transition stories > doom.",
        persona_type="climate",
        topics=["tech", "politics"],
        style_notes="optimistic, concrete examples, avoids hype",
    ),
]


@dataclass
class LLMClient:
    client: OpenAI
    model: str
    extra_headers: dict[str, str] | None = None


def get_llm() -> LLMClient | None:
    # Ensure local backend/.env is loaded when running scripts or uvicorn without --env-file.
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path, override=False)

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not api_key:
        return None
    referer = os.getenv("OPENROUTER_SITE_URL")
    title = os.getenv("OPENROUTER_SITE_NAME")
    extra_headers = {}
    if referer:
        extra_headers["HTTP-Referer"] = referer
    if title:
        extra_headers["X-Title"] = title
    return LLMClient(
        client=OpenAI(api_key=api_key, base_url=base_url),
        model=model,
        extra_headers=extra_headers or None,
    )


def generate_post(llm: LLMClient | None, persona: PersonaSpec, topic: str) -> str:
    if llm is None:
        return (
            f"[{persona.persona_type}] {persona.display_name}: "
            f"One thought on {topic} today—clarity beats noise."
        )

    response = llm.client.chat.completions.create(
        model=llm.model,
        extra_headers=llm.extra_headers,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are simulating a user on X. Write a single post (max 240 chars). "
                    "No hashtags. Stay in character."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Persona: {persona.display_name} (@{persona.handle})\n"
                    f"Bio: {persona.bio}\n"
                    f"Style: {persona.style_notes}\n"
                    f"Topic: {topic}\n"
                    "Write the post."
                ),
            },
        ],
    )
    message = response.choices[0].message
    return (message.content or "").strip()


def generate_reply(llm: LLMClient | None, persona: PersonaSpec, parent_content: str) -> str:
    if llm is None:
        return f"{persona.display_name} replies: interesting point — here’s the twist."

    response = llm.client.chat.completions.create(
        model=llm.model,
        extra_headers=llm.extra_headers,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are simulating a reply on X. Keep it under 180 chars. "
                    "No hashtags. Stay in character."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Persona: {persona.display_name} (@{persona.handle})\n"
                    f"Bio: {persona.bio}\n"
                    f"Style: {persona.style_notes}\n"
                    f"Parent post: {parent_content}\n"
                    "Write the reply."
                ),
            },
        ],
    )
    message = response.choices[0].message
    return (message.content or "").strip()
