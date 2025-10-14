from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import subprocess
import time
import random

app = Flask(__name__)

# --------------------------------------------------------------------
# SUPPLIER + BRAND MAPPING
# --------------------------------------------------------------------
SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
    "aosom": "https://www.aosom.co.uk/"
}

BRAND_SUPPLIER_MAP = {
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
    "vinsetto": "aosom"
}

# --------------------------------------------------------------------
# ENSURE CHROMIUM INSTALLED (fixes "Executable doesn't exist" error)
# --------------------------------------------------------------------
def ensure_chromium():
    try:
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=False,
            capture_output=True
        )
        print("✅ Chromium check complete.")
    except Exception as e:
        print(f"⚠️ Chromium install failed: {e}")

# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------
@app.route("/")
def home():
    return jsonify({"message": "AI Order Agent is live and ready."}), 200


@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json(force=True, silent=True) or {}
        brand = data.get("brand", "").lower().strip()
        sku = data.get("sku", "").strip()

        if not brand or not sku:
            return jsonify({"status": "error", "message": "Missing brand or SKU"}), 400

        supplier = BRAND_SUPPLIER_MAP.get(brand)
        if not supplier:
            return jsonify({"status": "error", "message": f"Unknown brand: {brand}"}), 400

        target = SUPPLIER_URL.get(supplier)
        if not target:
            return jsonify({"status": "error", "message": f"No URL for supplier: {supplier}"}), 400

        # ----------------------------------------------------------------
        # ENSURE CHROMIUM EXISTS BEFORE LAUNCH
        # ----------------------------------------------------------------
        ensure_chromium()

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-extensions",
                    "--single-process"
                ]
            )

            page = browser.new_page()
            page.set_default_timeout(12000)
            page.set_default_navigation_timeout(45000)

            # Simulate human behaviour
            time.sleep(random.uniform(1.5, 3.5))

            # Attempt navigation with retry logic
            max_retries = 2
            title = ""
            for attempt in range(max_retries):
                try:
                    print(f"Navigating to {target} (attempt {attempt + 1})")
                    page.goto(target, wait_until="domcontentloaded", timeout=45000)
                    title = page.title().strip()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Retrying due to: {e}")
                        time.sleep(random.uniform(3, 6))
                    else:
                        raise

            # Short delay to mimic human browsing
            time.sleep(random.uniform(1.5, 3.0))
            title = page.title().strip()
            browser.close()

        return jsonify({
            "status": "success",
            "supplier": supplier,
            "brand": brand,
            "sku": sku,
            "page_title": title,
            "message": f"Opened {target} successfully."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    # Render automatically sets PORT
    app.run(host="0.0.0.0", port=5000)
