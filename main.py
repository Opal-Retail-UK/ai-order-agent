from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import subprocess
import time
import random

app = Flask(__name__)

# --- Safety Fallback: Ensure Playwright browser is installed ---
try:
    subprocess.run(["playwright", "install", "chromium"], check=True)
except Exception as e:
    print("Warning: Playwright browser install skipped or failed:", e)

# --- Supplier URLs ---
SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
    "aosom": "https://www.aosom.co.uk/"
}

# --- Health Check Route ---
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# --- Main Order Endpoint ---
@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json()
        brand = data.get("brand", "").lower()
        sku = data.get("sku", "").upper()

        # --- Determine Supplier ---
        if brand in ["vasagle", "songmics", "feandrea"]:
            supplier = "songmics"
        elif brand in ["homcom", "outsunny", "pawhut", "zonekiz", "aiyaplay", "kleankin", "vinsetto"]:
            supplier = "aosom"
        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown brand: {brand}"
            }), 400

        # --- Launch Playwright ---
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process"
                ]
            )
            context = browser.new_context()
            page = context.new_page()

            # --- Timeout Settings ---
            page.set_default_timeout(60000)
            page.set_default_navigation_timeout(60000)

            target = SUPPLIER_URL[supplier]

            # --- Retry Navigation Logic (2 attempts) ---
            for attempt in range(2):
                try:
                    page.goto(target, wait_until="load", timeout=60000)
                    page.wait_for_selector("body", timeout=10000)
                    title = page.title().strip()
                    break
                except Exception as inner_error:
                    if attempt == 0:
                        print(f"[Retry {attempt+1}] Error navigating to {target}: {inner_error}")
                        time.sleep(5)
                    else:
                        raise inner_error

            # --- Add human-like delay to mimic browsing ---
            time.sleep(random.uniform(1.5, 3.5))

            browser.close()

        # --- Response ---
        return jsonify({
            "status": "success",
            "supplier": supplier,
            "brand": brand,
            "sku": sku,
            "page_title": title,
            "message": f"Opened {target} successfully."
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Flask Entrypoint ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
