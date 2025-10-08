from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import subprocess, os, random, time

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
    return "AI Order Agent – stealth mode active."

@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json()
        brand = data.get("brand", "").lower()
        sku = data.get("sku", "none")

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

        # --- Launch browser in stealth mode ---
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        ]
        ua = random.choice(user_agents)

        with sync_playwright() as p:
            # Aosom = more aggressive bot filter → run non-headless, add --no-sandbox
            headless = False if supplier == "aosom" else True
            args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            browser = p.chromium.launch(headless=headless, args=args)

            context = browser.new_context(
                user_agent=ua,
                viewport={"width": 1366, "height": 768},
                extra_http_headers={
                    "Accept-Language": "en-GB,en;q=0.9",
                    "Referer": "https://www.google.com/",
                    "DNT": "1"
                }
            )

            page = context.new_page()
            page.set_default_navigation_timeout(25000)

            # Add small human-like delay before navigation
            time.sleep(random.uniform(1.5, 3.5))

            page.goto(supplier_urls[supplier], wait_until="domcontentloaded")
            title = page.title()

            # Add delay to mimic human reading time
            time.sleep(random.uniform(1.5, 3.0))

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
