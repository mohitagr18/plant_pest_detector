#!/usr/bin/env python3
"""
benchmark_queries.py
Run 8 test queries per image (2 images = 16 total) against the Plant Doctor
backend (no Streamlit needed). Records latency and token usage, then exports
a CSV to results/.

Usage:
    python benchmark_queries.py          # full run  (16 queries, both images)
    python benchmark_queries.py --test   # smoke test (1 query, 1 image)
"""

# ── Load .env FIRST ──────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

import os, sys, csv, time, datetime
from io import BytesIO
from PIL import Image
import google.generativeai as genai

# ── Make sure src/ is on the path ────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from qa_engine_agentic import get_weather, get_soil_type, search_amazon_products

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════

MODEL      = "gemini-2.5-flash"
ZIPCODE    = "94533"
INFESTATION = "medium"

IMAGES = [
    {"path": "samples/test_img.png",       "plant": "lemon",  "label": "Lemon/Caterpillar"},
    {"path": "samples/citrus-aphids.jpg",  "plant": "citrus", "label": "Citrus/Aphids"},
]

RESULTS_DIR = "results"

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

records = []   # list of dicts accumulate across both images

def _configure():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        print("❌  GOOGLE_API_KEY not set in .env"); sys.exit(1)
    genai.configure(api_key=key)


def _record(label: str, image_label: str, elapsed: float, response):
    usage   = getattr(response, "usage_metadata", None)
    in_tok  = getattr(usage, "prompt_token_count",     0) if usage else 0
    out_tok = getattr(usage, "candidates_token_count", 0) if usage else 0
    records.append({
        "image":   image_label,
        "query":   label,
        "latency": round(elapsed, 3),
        "in_tok":  in_tok,
        "out_tok": out_tok,
    })
    print(f"  ✓ {label:<45} {elapsed:5.1f}s  in={in_tok:>5}  out={out_tok:>4}")
    return in_tok, out_tok


def timed_generate(label: str, image_label: str, model_obj, *args, **kwargs):
    t0 = time.perf_counter()
    response = model_obj.generate_content(*args, **kwargs)
    return response, *_record(label, image_label, time.perf_counter() - t0, response)


def timed_chat(label: str, image_label: str, chat, message: str):
    t0 = time.perf_counter()
    response = chat.send_message(message)
    _record(label, image_label, time.perf_counter() - t0, response)
    return response


def _extract(text, key):
    for line in text.splitlines():
        if line.strip().upper().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return "Unknown"


def _load_image(path):
    if not os.path.exists(path):
        print(f"❌  Image not found: {path}"); sys.exit(1)
    pil = Image.open(path)
    buf = BytesIO()
    pil.save(buf, format="JPEG")
    return Image.open(BytesIO(buf.getvalue()))   # fresh PIL for Gemini


# ════════════════════════════════════════════════════════════════════════════
# SINGLE IMAGE FLOW  (8 queries)
# ════════════════════════════════════════════════════════════════════════════

DETECT_PROMPT = """You are an agricultural AI expert. Analyze this image quickly and provide ONLY essential information.

Respond in EXACTLY this format (one item per line):

DETECTED: [Name of pest, disease, or health issue - be specific]
SEVERITY: [Mild/Moderate/Severe]
PLANT: [Specific plant or crop type if visible, or "Unknown" if not identifiable]
TYPE: [pest/disease/healthy]

Keep it brief - detailed analysis comes later."""


def run_image_flow(img_cfg: dict, test_only: bool = False):
    img_label = img_cfg["label"]
    plant     = img_cfg["plant"]
    zip_code  = ZIPCODE

    print(f"\n{'─'*70}")
    print(f"  IMAGE: {img_label}  ({img_cfg['path']})")
    print(f"{'─'*70}")

    pil_image = _load_image(img_cfg["path"])
    plain_model = genai.GenerativeModel(MODEL)

    # ── Q1: Image Detection ──────────────────────────────────────────────────
    resp1, *_ = timed_generate(
        "Q1: Image Detection", img_label,
        plain_model, [DETECT_PROMPT, pil_image]
    )
    raw      = resp1.text.strip()
    pest     = _extract(raw, "DETECTED")
    severity = _extract(raw, "SEVERITY")
    plant_det = _extract(raw, "PLANT")
    print(f"     → Detected: {pest} | Severity: {severity} | Plant: {plant_det}")

    if test_only:
        print("  [--test mode] stopping after Q1.")
        return

    # ── Chat session (tools enabled) ─────────────────────────────────────────
    tools      = [get_weather, get_soil_type, search_amazon_products]
    chat_model = genai.GenerativeModel(MODEL, tools=tools)
    chat       = chat_model.start_chat(enable_automatic_function_calling=True)

    # ── Q2: Brief Risk Assessment ────────────────────────────────────────────
    timed_chat("Q2: Brief Risk Assessment", img_label, chat, f"""Provide a VERY BRIEF 1-2 sentence risk assessment for:
Pest/Disease: {pest}
Severity: {severity}
Plant: {plant_det}

One sentence, under 25 words. Be concise and urgent.""")

    # ── Q3: Treatment Advice (calls weather + soil tools) ────────────────────
    timed_chat("Q3: Treatment Advice (weather+soil tools)", img_label, chat, f"""You are an agricultural expert.

Context:
- Pest/Disease: {pest}
- Plant: {plant}
- Infestation Level: {INFESTATION}
- Location: Zip code {zip_code}

Task:
1. Call get_weather("{zip_code}") and get_soil_type("{zip_code}")
2. Write ONLY treatment advice (no products yet) in 1-2 short paragraphs.""")

    # ── Q4: Product Recommendations (calls Amazon search) ───────────────────
    timed_chat("Q4: Product Recommendations (Amazon)", img_label, chat, f"""Based on the treatment advice you just gave for {pest} on {plant},
call search_amazon_products() 2-3 times and list the best products.

Format as:
### 🛒 Recommended Products on Amazon
**1. [Product Name](url)**
**2. [Product Name](url)**
**3. [Product Name](url)**""")

    # ── Q5: Soil Impact Analysis ─────────────────────────────────────────────
    timed_chat("Q5: Soil Impact Analysis", img_label, chat, f"""In exactly 2 paragraphs:
1. What this soil type means for {plant} cultivation.
2. How soil conditions affect treatment for {pest}.""")

    # ── Q6: Weather-Based Timing ─────────────────────────────────────────────
    timed_chat("Q6: Weather-Based Timing", img_label, chat, f"""In exactly 2 paragraphs:
1. Best application window in the next 3 days for treating {pest}.
2. Why timing matters (rain, temperature, wind).""")

    # ── Q7: Monitoring & Prevention ──────────────────────────────────────────
    timed_chat("Q7: Monitoring & Prevention", img_label, chat, f"""Provide monitoring and prevention advice for {pest} on {plant}:
1. How often to check plants.
2. Signs of treatment success/failure.
3. Prevention tips.
Keep it to 2 paragraphs.""")

    # ── Q8: Custom Question ───────────────────────────────────────────────────
    timed_chat("Q8: Custom Question", img_label, chat,
        f"What are the top 3 mistakes gardeners make when treating {pest} on {plant}, "
        f"and how do I avoid them?")


# ════════════════════════════════════════════════════════════════════════════
# CSV EXPORT
# ════════════════════════════════════════════════════════════════════════════

def export_csv():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(RESULTS_DIR, f"benchmark_{ts}.csv")

    fieldnames = ["image", "query", "latency_s", "input_tokens", "output_tokens"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in records:
            w.writerow({
                "image":         r["image"],
                "query":         r["query"],
                "latency_s":     r["latency"],
                "input_tokens":  r["in_tok"],
                "output_tokens": r["out_tok"],
            })

        # ── append summary rows ──────────────────────────────────────────────
        f.write("\n")
        lats   = [r["latency"] for r in records]
        in_t   = [r["in_tok"]  for r in records]
        out_t  = [r["out_tok"] for r in records]
        n      = len(records)
        w.writerow({"image": "AVERAGE", "query": f"({n} queries)",
                    "latency_s": round(sum(lats)/n, 3),
                    "input_tokens": round(sum(in_t)/n, 1),
                    "output_tokens": round(sum(out_t)/n, 1)})

    print(f"\n  📄 CSV saved → {csv_path}")
    return csv_path


# ════════════════════════════════════════════════════════════════════════════
# SUMMARY PRINT
# ════════════════════════════════════════════════════════════════════════════

def print_summary():
    lats   = [r["latency"] for r in records]
    in_t   = [r["in_tok"]  for r in records]
    out_t  = [r["out_tok"] for r in records]
    n      = len(records)

    print("\n" + "═" * 70)
    print("  RESULTS SUMMARY")
    print("═" * 70)
    print(f"\n  Total queries     : {n}")
    print(f"  Total time        : {sum(lats):.1f}s")
    print(f"\n  ┌─────────────────────────────────────────────┐")
    print(f"  │  Avg response latency  : {sum(lats)/n:>6.2f} s        │")
    print(f"  │  Avg input  tokens     : {sum(in_t)/n:>6.1f}          │")
    print(f"  │  Avg output tokens     : {sum(out_t)/n:>6.1f}          │")
    print(f"  └─────────────────────────────────────────────┘")

    print(f"\n  Per-query breakdown:")
    print(f"  {'#':<3}  {'Image':<20} {'Query':<45} {'Latency':>8}  {'InTok':>6}  {'OutTok':>6}")
    print(f"  {'─'*3}  {'─'*20} {'─'*45} {'─'*8}  {'─'*6}  {'─'*6}")
    for i, r in enumerate(records, 1):
        print(f"  {i:<3}  {r['image']:<20} {r['query']:<45} {r['latency']:>7.2f}s  {r['in_tok']:>6}  {r['out_tok']:>6}")
    print()


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_mode = "--test" in sys.argv

    print("\n" + "═" * 70)
    if test_mode:
        print("  PLANT DOCTOR – SMOKE TEST (Q1 only, 1 image)")
    else:
        print("  PLANT DOCTOR – FULL BENCHMARK (8 queries × 2 images = 16 total)")
    print("═" * 70)

    _configure()

    print(f"\n  {'Label':<47} {'Time':>6}  {'InTok':>6}  {'OutTok':>6}")
    print(f"  {'─'*47} {'─'*6}  {'─'*6}  {'─'*6}")

    if test_mode:
        run_image_flow(IMAGES[0], test_only=True)
        if records:
            print("\n  ✅ Smoke test passed — API key is valid, image loaded fine.")
            print(f"     Latency: {records[0]['latency']}s  |  "
                  f"Input tokens: {records[0]['in_tok']}  |  "
                  f"Output tokens: {records[0]['out_tok']}")
    else:
        for img_cfg in IMAGES:
            run_image_flow(img_cfg, test_only=False)
        print_summary()
        export_csv()
        print("  Done! 🎉\n")
