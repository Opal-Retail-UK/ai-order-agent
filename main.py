from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import requests
import openai
import os

app = Flask(__name__)

MAKE_CALLBACK_URL = os.getenv("MAKE_CALLBACK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


def send_to_make(payload):
    try:
        requests.post(MAKE_CALLBACK_URL, json=payload, timeout=15)
    except Exception as e:
        print("Error sending to Make:", e)


def interpret_page(content):
    prompt = f"""
    The following HTML/text is from a supplier website.
    Detect if it indicates one of the following statuses:
    1. out_of_stock
    2. payment_required
    3. success
    Respond only with one of those options.
    ----
    {content[:6000]}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print("AI interpretation error:", e)
        return "unknown_error"


def place_order(order):
    supplier = order.get("supplier")
    sku = order.get("sku")
    result = {"status": "error", "exception": "unknown_error", "message": ""}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            if supplier == "Songmics":
                page.goto("https://www.songmics.co.uk")
                page.fill("input[name='q']", sku)
                page.press("input[name='q']", "Enter")
                page.wait_for_selector(".product-grid-item", timeout=8000)
                verdict = interpret_page(page.content())
                if verdict == "out_of_stock":
                    result.update({"status": "error", "exception": "out_of_stock", "message": "Item unavailable"})
                else:
                    page.click(".product-grid-item")
                    page.click("button[name='add']")
                    result.update({"status": "success", "exception": "none", "message": "Order placed"})
            elif supplier == "Aosom":
                page.goto("https://www.aosom.co.uk")
                page.fill("input[name='search']", sku)
                page.press("input[name='search']", "Enter")
                page.wait_for_selector("body", timeout=8000)
                verdict = interpret_page(page.content())
                if verdict == "out_of_stock":
                    result.update({"status": "error", "exception": "out_of_stock", "message": "Out of stock"})
                else:
                    result.update({"status": "success", "exception": "none", "message": "Order placed"})
        except Exception as e:
            result["message"] = str(e)
        finally:
            browser.close()

    return result


@app.route("/order", methods=["POST"])
def handle_order():
    order = request.json
    print("Received order:", order)
    res = place_order(order)
    send_to_make(res)
    return jsonify(res)


@app.route("/", methods=["GET"])
def home():
    return "AI Order Agent is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
