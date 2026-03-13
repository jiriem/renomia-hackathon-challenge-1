"""
Challenge 1: Porovnání pojistných nabídek (Insurance Offer Comparison)
Domain: Odpovědnost (Liability Insurance)

Input:  Multiple insurance offers with OCR text from documents
Output: Parsed parameters per offer, ranking, best offer identification
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

    Input example:
    {
        "offers": [
            {
                "id": "generali_current",
                "insurer": "Generali ČP",
                "label": "Stávající smlouva",
                "documents": [
                    {
                        "filename": "nabidka_generali.pdf",
                        "ocr_text": "... OCR extracted text ..."
                    }
                ]
            },
            {
                "id": "csob_1",
                "insurer": "ČSOB",
                "label": "ČSOB I.",
                "documents": [{"filename": "...", "ocr_text": "..."}]
            }
        ],
        "segment": "odpovědnost"
    }

    Expected output:
    {
        "offers_parsed": [
            {
                "id": "generali_current",
                "insurer": "Generali ČP",
                "label": "Stávající smlouva",
                "covered_activities": "Výpis + výluky IT a poradenské činnosti",
                "territorial_scope": "ČR, SR, Polsko",
                "basic_limit_czk": 50000000,
                "limit_multiplier_per_year": 1,
                "aggregate_limit_czk": 50000000,
                "limit_persons_in_custody_czk": 5000000,
                "limit_pure_financial_loss_czk": 20000000,
                "limit_taken_items_czk": 2000000,
                "limit_cross_liability_czk": 50000000,
                "limit_recourse_czk": 25000000,
                "limit_non_pecuniary_damage_czk": 15000000,
                "basic_deductible_czk": 10000,
                "deductible_recourse_czk": 10000,
                "deductible_non_pecuniary_czk": 10000,
                "deductible_brought_items_czk": 1000,
                "deductible_financial_loss_czk": 5000,
                "premium_czk": null
            },
            ...
        ],
        "ranking": ["csob_1", "generali_current", ...],
        "best_offer_id": "csob_1"
    }
    """
    # TODO: Implement your solution here
    #
    # Suggested approach:
    # 1. For each offer, send OCR text to Gemini to extract structured parameters
    # 2. Compare offers across all fields
    # 3. Rank by value (coverage vs. cost vs. deductibles)
    # 4. Return structured comparison

    offers = payload.get("offers", [])
    segment = payload.get("segment", "")

    result = {
        "offers_parsed": [],
        "ranking": [],
        "best_offer_id": None,
    }

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
