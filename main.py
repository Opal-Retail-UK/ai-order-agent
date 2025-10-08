from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "AI Order Agent with Playwright is running."

@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body found"}), 400

        supplier = data.get("supplier", "unknown")
        sku = data.get("sku", "none")

        # Launch Playwright safely
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Test: visit a lightweight site
            page.goto("https://example.com")
            title = page.title()

            browser.close()

        return jsonify({
            "status": "success",
            "message": f"Playwright launched successfully. Page title: '{title}'",
            "supplier": supplier,
            "sku": sku
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
