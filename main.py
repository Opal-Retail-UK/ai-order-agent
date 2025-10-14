from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import time
import random

app = Flask(__name__)

# Supplier URLs (brand mapping)
SUPPLIER_URL = {
    "songmics": "https://www.songmics.co.uk/",
    "aosom": "https://www.aosom.co.uk/"
}

BRAND_SUPPLIER_MAP = {
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


@app.route('/')
def home():
    return jsonify({"message": "AI Order Agent is running."}), 200


@app.route('/order', methods=['POST'])
def handle_order():
    try:
        data = request.get_json()
        brand = data.get('brand', '').lower().strip()
        sku = data.get('sku', '').strip()

        if not brand or not sku:
            return jsonify({"status": "error", "message": "Missing brand or SKU"}), 400

        # Identify supplier from brand
        supplier = BRAND_SUPPLIER_MAP.get(brand)
        if not supplier:
            return jsonify({"status": "error", "message": f"Unknown brand: {brand}"}), 400

        target = SUPPLIER_URL.get(supplier)
        if not target:
            return jsonify({"status": "error", "message": f"No URL configured for supplier: {supplier}"}), 400

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Tight waits to avoid hanging too long
            page.set_default_timeout(12000)
            page.set_default_navigation_timeout(45000)

            # Add a short, human-like delay before navigating
            time.sleep(random.uniform(1.5, 3.5))

            # Attempt navigation with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    page.goto(target, wait_until="domcontentloaded", timeout=45000)
                    title = page.title().strip()
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Retrying ({attempt + 1}/{max_retries}) due to: {e}")
                        time.sleep(random.uniform(2.5, 5.0))
                    else:
                        raise

            # Mimic human reading time before exit
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
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # Render binds PORT automatically; Flask defaults to 5000
    app.run(host="0.0.0.0", port=5000)
