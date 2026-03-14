"""
Challenge 1: Porovnání pojistných nabídek (Insurance Offer Comparison)

Input:  Multiple insurance offers with OCR text, plus a list of fields to extract
Output: Parsed fields per offer, ranking, best offer identification
"""

import os
import threading
import time

import google.generativeai as genai
import psycopg2
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Challenge 1: Insurance Offer Comparison")

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://hackathon:hackathon@localhost:5432/hackathon"
)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


class GeminiTracker:
    """Wrapper around Gemini that tracks token usage."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.enabled = bool(api_key)
        if self.enabled:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.request_count = 0
        self._lock = threading.Lock()

    def generate(self, prompt, **kwargs):
        if not self.enabled:
            raise RuntimeError("Gemini API key not configured")
        response = self.model.generate_content(prompt, **kwargs)
        with self._lock:
            self.request_count += 1
            meta = getattr(response, "usage_metadata", None)
            if meta:
                self.prompt_tokens += getattr(meta, "prompt_token_count", 0)
                self.completion_tokens += getattr(meta, "candidates_token_count", 0)
                self.total_tokens += getattr(meta, "total_token_count", 0)
        return response

    def get_metrics(self):
        with self._lock:
            return {
                "gemini_request_count": self.request_count,
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
            }

    def reset(self):
        with self._lock:
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0
            self.request_count = 0


gemini = GeminiTracker(GEMINI_API_KEY)


def get_db():
    return psycopg2.connect(DATABASE_URL)


@app.on_event("startup")
def init_db():
    for _ in range(15):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )"""
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception:
            time.sleep(1)


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return gemini.get_metrics()


@app.post("/metrics/reset")
def reset_metrics():
    gemini.reset()
    return {"status": "reset"}


@app.post("/solve")
def solve(payload: dict):
    """
    Compare insurance offers and identify the best option.

    The input contains:
    - segment: insurance segment (odpovědnost, auta, lodě, majetek, ...)
    - fields_to_extract: list of field names to extract from each offer
    - field_types: dict mapping field name → "number" or "string"
    - offers: list of offers, each with id, insurer, label, and documents
    - rfp: (optional) request for proposal document

    Expected output:
    {
        "offers_parsed": [
            {
                "id": "allianz",
                "insurer": "Allianz",
                "fields": {
                    "Roční pojistné": "125000",
                    "Povinné ručení – limit": "100000000",
                    ...
                }
            }
        ],
        "ranking": ["allianz", "generali", ...],
        "best_offer_id": "allianz"
    }
    """
    # TODO: Implement your solution here
    #
    # Suggested approach:
    # 1. Read fields_to_extract and field_types from the input
    # 2. For each offer, send OCR text + field list to Gemini to extract values
    # 3. Compare offers across all fields
    # 4. Rank by value (coverage vs. cost vs. deductibles)
    # 5. Return structured comparison

    offers = payload.get("offers", [])
    segment = payload.get("segment", "")
    fields_to_extract = payload.get("fields_to_extract", [])
    field_types = payload.get("field_types", {})

    result = {
        "offers_parsed": [],
        "ranking": [],
        "best_offer_id": None,
    }

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
