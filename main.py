from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import random
import time

app = Flask(__name__)

# ---------------------------------------
# CONFIG
# ---------------------------------------
SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
}

LOGIN_URLS = {
    "songmics": "https://www.songmics.co.uk/account/login",
}

# Environment variables (set in Render dashboard)
SONGMICS_EMAIL = os.getenv("SONGMICS_EMAIL")
SONGMICS_PASSWORD = os.getenv("SONGMICS_PASSWORD")

# ---------------------------------------
# ROUTES
# ---------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "AI Order Agent running successfully 🚀"}), 200


@app.route("/order", methods=["POST"])
def place_order():
    try:
        data = request.get_json()
        brand = data.get("brand", "").lower()
        sku = data.get("sku", "").strip()

        # Determine supplier from brand
        if brand in ["vasagle", "feandrea", "songmics"]:
            supplier = "songmics"
        else:
            return jsonify({"status": "error", "message": f"Unknown brand: {brand}"}), 400

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context()
            page = context.new_page()

            # Simulate human-like timing
            time.sleep(random.uniform(1.0, 2.5))

            # Navigate to login page
            login_url = LOGIN_URLS[supplier]
            page.goto(login_url, wait_until="domcontentloaded", timeout=25000)

            # Fill login form
            page.fill("input[name='customer[email]']", SONGMICS_EMAIL)
            page.fill("input[name='customer[password]']", SONGMICS_PASSWORD)

            # Submit login form
            page.click("button[type='submit']")

            # Wait for successful login
            page.wait_for_selector("a[href*='/account']", timeout=10000)

            # Verify login success
            title = page.title().strip()
            print(f"✅ Logged in successfully. Page title: {title}")

            # Go to home or test page (for now)
            target = SUPPLIER_URL[supplier]
            page.goto(target, wait_until="domcontentloaded")

            time.sleep(random.uniform(1.5, 2.5))

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
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# ENTRY POINT
# ---------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
