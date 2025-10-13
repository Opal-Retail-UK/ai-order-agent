from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import subprocess, os, time, random

app = Flask(__name__)

# --- Brand → Supplier mapping (from your note) ---
BRAND_TO_SUPPLIER = {
    # Songmics group
    "vasagle": "songmics",
    "songmics": "songmics",
    "feandrea": "songmics",
    # Aosom group
    "homcom": "aosom",
    "outsunny": "aosom",
    "pawhut": "aosom",
    "zonekiz": "aosom",
    "aiyaplay": "aosom",
    "kleankin": "aosom",
    "vinsetto": "aosom",
}

SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
    "aosom":    "https://www.aosom.co.uk/",
}

# Install Chromium if missing (don’t pin the path/version)
def ensure_chromium():
    try:
        subprocess.run(
            ["python", "-m", "playwright", "install", "chromium"],
            check=False, capture_output=True
        )
    except Exception:
        pass

@app.route("/", methods=["GET"])
def home():
    return "AI Order Agent – Render-optimised launcher ready."

@app.route("/order", methods=["POST"])
def order():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        brand = (payload.get("brand") or "").strip().lower()
        sku   = (payload.get("sku") or "").strip()

        supplier = BRAND_TO_SUPPLIER.get(brand)
        if not supplier:
            return jsonify({"status":"error",
                            "message": f"Unknown brand '{brand}' — no supplier mapping."}), 400

        # Make sure Chromium exists (first call after cold start may need this)
        ensure_chromium()

        # Lightweight launch args for Render free tier
        chrome_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-features=IsolateOrigins,site-per-process",
            "--single-process",
            "--disable-blink-features=AutomationControlled",
        ]

        # Subtle realism without going non-headless (keeps memory lower)
        ua_pool = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        ]
        ua = random.choice(ua_pool)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=chrome_args)

            context = browser.new_context(
                user_agent=ua,
                viewport={"width": 1280, "height": 720},
                extra_http_headers={
                    "Accept-Language": "en-GB,en;q=0.9",
                    "Referer": "https://www.google.com/",
                    "DNT": "1",
                },
            )
            page = context.new_page()
            # Keep waits tight so we don’t hang on heavy assets
            page.set_default_timeout(12000)
            page.set_default_navigation_timeout(18000)

            # Tiny pause to look less botty
            time.sleep(random.uniform(0.8, 1.6))

            target = SUPPLIER_URL[supplier]
            page.goto(target, wait_until="domcontentloaded", timeout=18000)

            # If a hard block page loads, title will expose it
            title = page.title().strip()

            browser.close()

        return jsonify({
            "status": "success",
            "supplier": supplier,
            "brand": brand,
            "sku": sku,
            "page_title": title,
            "message": f"Opened {SUPPLIER_URL[supplier]} successfully."
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Render binds port via PORT env; Flask default 5000 is fine for us
    app.run(host="0.0.0.0", port=5000)
