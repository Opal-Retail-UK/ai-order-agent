from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import random
import time
import subprocess
try:
    subprocess.run(["playwright", "install", "chromium"], check=True)
except Exception as e:
    print("Warning: Browser install skipped or failed:", e)

app = Flask(__name__)

# --------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------
SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
}

LOGIN_URLS = {
    "songmics": "https://www.songmics.co.uk/account/login",
}

# Environment variables stored in Render
SONGMICS_EMAIL = os.getenv("SONGMICS_EMAIL")
SONGMICS_PASSWORD = os.getenv("SONGMICS_PASSWORD")

# --------------------------------------------------------
# HEALTH CHECK ROUTE
# --------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


# --------------------------------------------------------
# ROOT ROUTE
# --------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "AI Order Agent running successfully 🚀"}), 200


# --------------------------------------------------------
# ORDER ROUTE
# --------------------------------------------------------
@app.route("/order", methods=["POST"])
def place_order():
    try:
        data = request.get_json()
        brand = data.get("brand", "").lower()
        sku = data.get("sku", "").strip()

        # Determine supplier
        if brand in ["vasagle", "feandrea", "songmics"]:
            supplier = "songmics"
        else:
            return jsonify({"status": "error", "message": f"Unknown brand: {brand}"}), 400

        with sync_playwright() as p:
            # Headless = False for local debug (set True before deploying to Render)
        import os

        browser = p.chromium.launch(
            headless=os.getenv("RENDER", "false").lower() == "true" or True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process"
             ]
        )

            context = browser.new_context()
            page = context.new_page()

            # Set timeouts
            page.set_default_timeout(30000)
            page.set_default_navigation_timeout(30000)

            # Simulate human delay
            time.sleep(random.uniform(1.0, 2.5))

            # Navigate to login page
            login_url = LOGIN_URLS[supplier]
            page.goto(login_url, wait_until="domcontentloaded")

            # Fill login form
            page.fill("input[name='customer[email]']", SONGMICS_EMAIL)
            page.fill("input[name='customer[password]']", SONGMICS_PASSWORD)

            # Submit
            page.click("button[type='submit']")

            # Wait for successful login
            page.wait_for_selector("a[href*='/account']", timeout=15000)

            # Go to homepage
            page.goto(SUPPLIER_URL[supplier], wait_until="domcontentloaded")

            # Add a small pause for realism
            time.sleep(random.uniform(1.5, 3.0))

            title = page.title().strip()
            browser.close()

            return jsonify({
                "status": "success",
                "supplier": supplier,
                "brand": brand,
                "sku": sku,
                "page_title": title,
                "message": f"✅ Logged into {supplier} successfully."
            }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# --------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
