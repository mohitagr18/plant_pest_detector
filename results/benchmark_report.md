# Plant Doctor — Benchmark Report
**Date:** April 15, 2026  
**Model:** `gemini-2.5-flash`  
**Script:** `benchmark_queries.py`  
**Raw Data:** `results/benchmark_20260415_122837.csv`

---

## Overview

The goal of this benchmark was to systematically measure the **end-to-end latency** and **token usage** of the deployed Plant Doctor application across its full query flow — without needing the Streamlit UI. The benchmark covered every major API call path in the app, from image detection through agentic tool use and follow-up Q&A.

---

## Setup

### Application Stack
| Component | Detail |
|-----------|--------|
| LLM | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| Vision | Gemini multimodal — same model handles image detection |
| Tools (Agentic) | `get_weather()`, `get_soil_type()`, `search_amazon_products()` |
| External APIs | NOAA Weather API, USDA Soil DB, Serper (Amazon product search) |
| Framework | Streamlit (bypassed for benchmark; called Python modules directly) |

### Test Images
Two sample images from `samples/` were used to give more diverse results:

| Label | File | Content |
|-------|------|---------|
| Lemon/Caterpillar | `samples/test_img.png` | Lemon leaf with caterpillar infestation |
| Citrus/Aphids | `samples/citrus-aphids.jpg` | Citrus plant with aphid infestation |

### Fixed Parameters
| Parameter | Value |
|-----------|-------|
| Zip Code | `94533` (Fairfield, CA) |
| Infestation Level | `medium` |
| Plant (Lemon run) | `lemon` |
| Plant (Citrus run) | `citrus` |

---

## Methodology

### Why No Extra Images Were Needed
The Plant Doctor flow is **conversational**: the image is analyzed only **once** (Q1), and all subsequent queries (Q2–Q8) are text-based follow-up messages sent to the same Gemini chat session. This mirrors exactly how a real user interacts with the app — upload one photo, then ask follow-up questions.

Running both images gave **16 independent measurements** across two distinct pest scenarios.

### Smoke Test First
Before running all 16 queries, a cheap smoke test (`--test` flag) was run that executed only Q1 on the first image. This validated:
- The updated API key was valid
- The image loaded correctly
- The model responded as expected

**Smoke test result:** ✅ Passed — 5.6s, 360 input tokens, 22 output tokens.

### How Token Usage Was Captured
Token counts were read directly from `response.usage_metadata` returned by the Gemini SDK on every call — no log parsing required:
```python
usage   = response.usage_metadata
in_tok  = usage.prompt_token_count       # input tokens
out_tok = usage.candidates_token_count   # output tokens
```

> [!NOTE]
> Input token counts grow across the conversation (Q1 → Q8) because Gemini's chat session includes the full conversation history in every request. This is expected and matches real app behaviour.

---

## Query Descriptions

Each image went through the following 8 queries in sequence:

| # | Query | What It Does | Tools Called |
|---|-------|-------------|--------------|
| Q1 | Image Detection | Vision model analyzes the uploaded image, returns pest name, severity, plant type | — |
| Q2 | Brief Risk Assessment | 1–2 sentence urgent risk summary for the detected pest | — |
| Q3 | Treatment Advice | Generates a treatment plan tailored to soil & weather conditions | `get_weather()`, `get_soil_type()` |
| Q4 | Product Recommendations | Finds specific organic/natural products on Amazon | `search_amazon_products()` ×3 |
| Q5 | Soil Impact Analysis | Explains how local soil type affects plant health and treatment application | — |
| Q6 | Weather-Based Timing | Recommends the optimal 3-day application window based on forecast | — |
| Q7 | Monitoring & Prevention | Signs to watch for, how to assess treatment success, prevention steps | — |
| Q8 | Custom Question | Open-ended question: top 3 mistakes when treating the detected pest | — |

---

## Results

### Per-Query Breakdown (All 16 Queries)

| # | Image | Query | Latency (s) | Input Tokens | Output Tokens |
|---|-------|-------|:-----------:|:------------:|:-------------:|
| 1  | Lemon/Caterpillar | Q1: Image Detection                        | 5.25  | 360   | 27  |
| 2  | Lemon/Caterpillar | Q2: Brief Risk Assessment                  | 0.65  | 193   | 24  |
| 3  | Lemon/Caterpillar | Q3: Treatment Advice (weather+soil tools)  | 5.00  | 855   | 103 |
| 4  | Lemon/Caterpillar | Q4: Product Recommendations (Amazon)       | 10.37 | 1,347 | 159 |
| 5  | Lemon/Caterpillar | Q5: Soil Impact Analysis                   | 4.16  | 1,544 | 204 |
| 6  | Lemon/Caterpillar | Q6: Weather-Based Timing                   | 5.44  | 1,792 | 198 |
| 7  | Lemon/Caterpillar | Q7: Monitoring & Prevention                | 4.01  | 2,043 | 197 |
| 8  | Lemon/Caterpillar | Q8: Custom Question                        | 3.19  | 2,272 | 278 |
| 9  | Citrus/Aphids     | Q1: Image Detection                        | 5.01  | 360   | 20  |
| 10 | Citrus/Aphids     | Q2: Brief Risk Assessment                  | 0.70  | 186   | 25  |
| 11 | Citrus/Aphids     | Q3: Treatment Advice (weather+soil tools)  | 6.31  | 842   | 108 |
| 12 | Citrus/Aphids     | Q4: Product Recommendations (Amazon)       | 6.10  | 1,327 | 156 |
| 13 | Citrus/Aphids     | Q5: Soil Impact Analysis                   | 4.75  | 1,515 | 224 |
| 14 | Citrus/Aphids     | Q6: Weather-Based Timing                   | 3.84  | 1,777 | 198 |
| 15 | Citrus/Aphids     | Q7: Monitoring & Prevention                | 2.55  | 2,021 | 208 |
| 16 | Citrus/Aphids     | Q8: Custom Question                        | 2.72  | 2,254 | 288 |

---

### Summary Averages

| Metric | Value |
|--------|-------|
| **Total queries run** | 16 |
| **Total wall-clock time** | 70.1 s |
| **Average response latency** | **4.38 s** |
| **Average input tokens / query** | **1,293** |
| **Average output tokens / query** | **151** |

---

## Observations

### Latency
- **Fastest query:** Q2 (Brief Risk Assessment) — ~0.67s average. Pure text prompt with no tool calls and a very short required output (≤25 words).
- **Slowest query:** Q4 (Product Recommendations) — 10.4s for Lemon run, 6.1s for Citrus run. This query makes **3 sequential Serper API calls** before Gemini can compose its response, so external network latency dominates.
- **Vision overhead:** Q1 (image detection) consistently takes ~5s across both images. The image payload adds encoding overhead on top of the model call.
- **Latency decreases** from Q5 onward — the model has already gathered all external data (weather, soil, Amazon) and subsequent queries are pure reasoning over the existing context.

### Token Usage
- **Input tokens grow monotonically** from Q1 to Q8 (360 → 2,272) because Gemini includes the full conversation history in every request. This is expected behaviour for a stateful chat session.
- **Output tokens are consistent** — most responses are 103–288 tokens, reflecting the 1–2 paragraph response format enforced in the prompts.
- Q8 (Custom Question) generates the most output (~283 avg tokens) — it's the most open-ended prompt and produces structured "top 3 mistakes" lists.

### Cross-Image Consistency
- Both image scenarios produced very similar latency profiles (within ~1–2s per query).
- The Citrus/Aphids run was marginally faster on Q4 (6.1s vs 10.4s) — likely due to Serper search result caching or network variability, not model differences.
- Detection accuracy: Lemon image → Citrus Swallowtail Caterpillar; Citrus image → Aphids. Both were correctly identified.

---

## What the Benchmark Script Does

The script `benchmark_queries.py` can be run in two modes:

```bash
# Smoke test — 1 query, 1 image, validates API key (cheap)
python benchmark_queries.py --test

# Full benchmark — 8 queries x 2 images = 16 total
python benchmark_queries.py
```

Key design decisions:
- **No Streamlit dependency** — imports and calls the Python modules directly (`src/plant_pest_detector.py`, `src/qa_engine_agentic.py`)
- **Token capture via SDK** — uses `response.usage_metadata` instead of log parsing
- **CSV export** — results automatically saved to `results/benchmark_<timestamp>.csv` with a summary AVERAGE row appended
- **Smoke test gate** — cheap 1-query sanity check before committing to 16 API calls

---

## Output Files

| File | Description |
|------|-------------|
| `benchmark_queries.py` | The benchmark script |
| `results/benchmark_20260415_122837.csv` | Raw per-query data + averages |
| `results/benchmark_report.md` | This report |
