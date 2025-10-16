import os
import time
import random
import subprocess
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

# Ensure Playwright browsers are installed (safety fallback)
try:
    subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
except Exception as e:
    print("Warning: Browser install skipped or failed:", e)

app = Flask(__name__)

SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
    "aosom": "https://www.aosom.co.uk/"
}

@app.route("/")
def home():
    return "AI Order Agent is running successfully 🚀", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json(force=True)
        brand = data.get("brand", "").strip().lower()
        sku = data.get("sku", "").strip().upper()

        # Identify supplier based on brand
        if brand in ["vasagle", "songmics", "feandrea"]:
            supplier = "songmics"
        elif brand in ["homcom", "outsunny", "pawhut", "zonekiz", "aiyaplay", "kleankin", "vinsetto"]:
            supplier = "aosom"
        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown brand: {brand}"
            }), 400

        result = place_order(supplier, brand, sku)
        return result

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def place_order(supplier, brand, sku):
    with sync_playwright() as p:
        # Force headless mode for Render, even if not specified
        headless_mode = True

        browser = p.chromium.launch(
            headless=headless_mode,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
            ]
        )

        page = browser.new_page()

        # Add natural delay before navigation (looks more human)
        time.sleep(random.uniform(1.0, 2.5))

        target = SUPPLIER_URL[supplier]
        page.goto(target, wait_until="domcontentloaded", timeout=30000)

        # Let page load properly
        time.sleep(random.uniform(1.0, 2.0))
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


if __name__ == "__main__":
    # Render binds port dynamically, so we use PORT if available
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
