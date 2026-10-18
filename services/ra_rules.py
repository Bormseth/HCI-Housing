"""Shared rules and sample content for the RA class prototype (not UNH policy)."""

import re

from pydantic import BaseModel, ConfigDict, Field

CLASS_YEARS = ["First-year", "Sophomore", "Junior", "Senior", "Graduate student"]
MIN_WORDS = 25
MAX_WORDS = 200
CYCLE = {
    "term": "2027–2028",
    "deadline": "November 30, 2026 at 11:59 PM ET",
    "estimate": "15–20 minutes",
    "sample": True,
}
PROMPTS = {
    "motivation": "Why do you want to be an RA?",
    "scenario": "A resident feels left out. How would you help?",
}


class ApplicationData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=200)
    class_year: str = Field(default="", max_length=40)
    major: str = Field(default="", max_length=160)
    enrolled: bool = False
    expectations: bool = False
    motivation: str = Field(default="", max_length=8000)
    scenario: str = Field(default="", max_length=8000)
    experience: str = Field(default="", max_length=2000)
    certify: bool = False


def word_count(text: str) -> int:
    return len(text.split())


def validate_step(data: dict, step: int) -> dict[str, str]:
    """Return actionable field errors; drafts may remain incomplete."""
    errors = {}
    if step == 1:
        if len(data.get("full_name", "").strip()) < 2:
            errors["full_name"] = "Enter your full name (at least 2 characters)."
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", data.get("email", "").strip()):
            errors["email"] = "Enter a valid email, such as name@unh.edu."
        if data.get("class_year") not in CLASS_YEARS:
            errors["class_year"] = "Choose your class year."
        if not data.get("enrolled"):
            errors["enrolled"] = "Confirm that you expect to be enrolled during the appointment."
        if not data.get("expectations"):
            errors["expectations"] = "Review and acknowledge the sample role expectations."
    if step == 2:
        for key, prompt in PROMPTS.items():
            count = word_count(data.get(key, ""))
            if not MIN_WORDS <= count <= MAX_WORDS:
                errors[key] = f'{prompt} Write {MIN_WORDS}–{MAX_WORDS} words; you have {count}.'
    if step == 3 and not data.get("certify"):
        errors["certify"] = "Confirm that you have reviewed your application before submitting."
    return errors


def validate_application(data: dict) -> dict[str, str]:
    return {key: message for step in (1, 2, 3) for key, message in validate_step(data, step).items()}
