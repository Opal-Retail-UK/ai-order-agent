# AI Order Agent (Free Version)

A free, lightweight AI-powered agent for automating supplier order placement (Songmics, Aosom) integrated with Make.com.

## Features
- Free hosting on Render.com
- GPT-4o-mini interprets page content for "Out of stock" / "Payment required" / "Success"
- Uses Playwright for real browser automation
- Sends results back to Make via webhook

## Quick Start

1. **Deploy to Render**
   - Create a free account at [https://render.com](https://render.com).
   - Create a new Web Service.
   - Upload this project or connect it via GitHub.
   - Choose the free plan.
   - Add environment variables from `.env.example`.

2. **In Make.com**
   - Add a HTTP module → POST → your Render URL `/order`
   - Add a Custom Webhook module for the callback.
   - Router by `exception`:
       - success → WhatsApp ✅
       - payment_required → WhatsApp ⚠️
       - out_of_stock → WhatsApp 🚫
       - error → WhatsApp ❗

3. **Local Testing**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   python main.py
   ```

Then POST an order JSON to http://localhost:5000/order

```json
{
  "supplier": "Songmics",
  "sku": "ABC123",
  "address": {
    "name": "Rob Murphy",
    "address1": "123 Example St",
    "city": "Saltburn",
    "postcode": "TS12 1AA"
  }
}
```

The agent will browse the site, interpret results, and send a callback to your Make webhook.
