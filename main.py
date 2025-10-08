from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import subprocess, os

app = Flask(__name__)

# --- Brand to supplier mapping ---
brand_to_supplier = {
    "vasagle": "songmics",
    "songmics": "songmics",
    "feandrea": "songmics",
    "homcom": "aosom",
    "outsunny": "aosom",
    "pawhut": "aosom",
    "zonekiz": "aosom",
    "aiyaplay": "aosom",
    "kleankin": "aosom",
    "vinsetto": "aosom"
}

supplier_urls = {
    "songmics": "https://www.songmics.co.uk/",
    "aosom": "https://www.aosom.co.uk/"
}

@app.route("/", methods=["GET"])
def home():
    return "AI Order Agent with supplier routing is running."

@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json()
        brand = data.get("brand", "").lower()
        sku = data.get("sku", "none")

        # Determine supplier based on brand
        supplier = brand_to_supplier.get(brand, "unknown")

        if supplier == "unknown":
            return jsonify({
                "status": "error",
                "message": f"Brand '{brand}' not recognised — no supplier mapping found."
            }), 400

        # Ensure Chromium is installed
        chromium_path = "/opt/render/.cache/ms-playwright/chromium_headless_shell-1187/chrome-linux/headless_shell"
        if not os.path.exists(chromium_path):
            subprocess.run(["playwright", "install", "chromium"], check=False)

        # Launch Playwright and open supplier site
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(supplier_urls[supplier])
            title = page.title()
            browser.close()

        return jsonify({
            "status": "success",
            "supplier": supplier,
            "brand": brand,
            "sku": sku,
            "page_title": title,
            "message": f"Opened {supplier_urls[supplier]} successfully."
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
