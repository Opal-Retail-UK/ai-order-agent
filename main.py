from flask import Flask, request, jsonify

# Create the Flask app
app = Flask(__name__)

# Health check / root route
@app.route("/", methods=["GET"])
def home():
    return "AI Order Agent is running."

# Order endpoint
@app.route("/order", methods=["POST"])
def handle_order():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON body found"}), 400

        # Extract basic info
        supplier = data.get("supplier", "unknown")
        sku = data.get("sku", "none")

        # Simulate success response
        return jsonify({
            "status": "success",
            "message": f"Order received for {supplier}, SKU: {sku}"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Standard Flask boot line
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

