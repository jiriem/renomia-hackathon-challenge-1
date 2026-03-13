# Challenge 1: Porovnání pojistných nabídek (Insurance Offer Comparison)

Compare multiple liability insurance offers, extract key parameters from each, and rank them.

## What you need to do

Implement the `solve()` function in `main.py`. Your endpoint receives OCR-extracted text from insurance offer documents and must:

1. **Parse** each offer to extract coverage limits, deductibles, and premium
2. **Rank** offers from best to worst
3. **Identify** the single best offer

## Input format

```json
POST /solve
{
  "offers": [
    {
      "id": "generali_current",
      "insurer": "Generali ČP",
      "label": "Stávající smlouva",
      "documents": [
        {
          "filename": "nabidka_generali.pdf",
          "ocr_text": "Pojistná smlouva č. 123456\nPojištění odpovědnosti za škodu...\nLimit plnění: 50 000 000 Kč\nSpoluúčast: 10 000 Kč..."
        }
      ]
    },
    {
      "id": "csob_1",
      "insurer": "ČSOB",
      "label": "ČSOB I.",
      "documents": [
        {
          "filename": "nabidka_csob.pdf",
          "ocr_text": "Nabídka pojištění odpovědnosti...\nZákladní limit: 100 000 000 Kč..."
        }
      ]
    }
  ],
  "segment": "odpovědnost"
}
```

## Expected output

```json
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
    }
  ],
  "ranking": ["csob_1", "generali_current"],
  "best_offer_id": "csob_1"
}
```

### Fields to extract per offer

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Pass through from input |
| `insurer` | string | Pass through from input |
| `label` | string | Pass through from input |
| `covered_activities` | string | Popis pojištěných činností |
| `territorial_scope` | string | Územní rozsah |
| `basic_limit_czk` | number | Základní limit plnění (Kč) |
| `limit_multiplier_per_year` | number | Násobek limitu za rok |
| `aggregate_limit_czk` | number | Agregovaný roční limit (Kč) |
| `limit_persons_in_custody_czk` | number | Sublimit - osoby v péči (Kč) |
| `limit_pure_financial_loss_czk` | number | Sublimit - čistá finanční újma (Kč) |
| `limit_taken_items_czk` | number | Sublimit - převzaté věci (Kč) |
| `limit_cross_liability_czk` | number | Sublimit - křížová odpovědnost (Kč) |
| `limit_recourse_czk` | number | Sublimit - regres (Kč) |
| `limit_non_pecuniary_damage_czk` | number | Sublimit - nemajetková újma (Kč) |
| `basic_deductible_czk` | number | Základní spoluúčast (Kč) |
| `deductible_recourse_czk` | number | Spoluúčast - regres (Kč) |
| `deductible_non_pecuniary_czk` | number | Spoluúčast - nemajetková újma (Kč) |
| `deductible_brought_items_czk` | number | Spoluúčast - vnesené věci (Kč) |
| `deductible_financial_loss_czk` | number | Spoluúčast - finanční újma (Kč) |
| `premium_czk` | number/null | Roční pojistné (Kč) |

## Scoring

| Component | Weight | Details |
|-----------|--------|---------|
| Field extraction | 60% | Numeric fields: ±10% tolerance. String fields: fuzzy match |
| Ranking order | 25% | Correct relative ordering of offers |
| Best offer ID | 15% | Exact match on the top pick |

## Local development

```bash
# Start the app + sidecar database
docker compose up --build

# Test your endpoint
curl -X POST http://localhost:8080/solve \
  -H "Content-Type: application/json" \
  -d '{
    "offers": [
      {
        "id": "offer_a",
        "insurer": "Test Insurer",
        "label": "Test",
        "documents": [{"filename": "test.pdf", "ocr_text": "Limit plnění: 50 000 000 Kč\nSpoluúčast: 10 000 Kč\nRoční pojistné: 125 000 Kč"}]
      }
    ],
    "segment": "odpovědnost"
  }'

# Check health
curl http://localhost:8080/

# Check token usage
curl http://localhost:8080/metrics
```

## Available tools

- **Gemini API** — use the pre-configured `gemini` object: `response = gemini.generate("your prompt")`. Token usage is tracked automatically.
- **PostgreSQL sidecar** — available at `DATABASE_URL` for caching. A `cache` table (key TEXT, value JSONB) is created on startup.

## Deployment

Push to your GitHub repo — Cloud Build will automatically build and deploy to Cloud Run.

## Tips

- Send the full OCR text to Gemini with a structured extraction prompt listing all expected fields
- Czech insurance documents use terms like "limit plnění", "spoluúčast", "pojistné"
- Numbers may appear as "50 000 000 Kč" or "50.000.000,- Kč" — normalize carefully
- For ranking: higher limits + lower deductibles + lower premium = better offer
- Use the sidecar DB to cache parsed results and avoid redundant Gemini calls
- Return `null` for fields you can't find rather than guessing
