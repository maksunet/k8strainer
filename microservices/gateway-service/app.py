import os
import socket

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

CATALOG_URL = os.environ.get("CATALOG_SERVICE_URL", "http://catalog-service")
CART_URL = os.environ.get("CART_SERVICE_URL", "http://cart-service")
ORDER_URL = os.environ.get("ORDER_SERVICE_URL", "http://order-service")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api")
def api_info():
    return jsonify(
        service="gateway-service",
        hostname=socket.gethostname(),
        routes=[
            "GET  /products",
            "GET  /products/<id>",
            "GET  /cart/<user>",
            "POST /cart/<user>/add {product_id, qty}",
            "POST /checkout/<user>",
            "GET  /orders/<user>",
        ],
    )


@app.route("/products")
def products():
    resp = requests.get(f"{CATALOG_URL}/products", timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/products/<product_id>")
def product(product_id):
    resp = requests.get(f"{CATALOG_URL}/products/{product_id}", timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/cart/<user>", methods=["GET"])
def get_cart(user):
    resp = requests.get(f"{CART_URL}/cart/{user}", timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/cart/<user>/add", methods=["POST"])
def add_to_cart(user):
    resp = requests.post(f"{CART_URL}/cart/{user}/add", json=request.get_json(force=True), timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/checkout/<user>", methods=["POST"])
def checkout(user):
    resp = requests.post(f"{ORDER_URL}/orders/{user}/checkout", timeout=10)
    return jsonify(resp.json()), resp.status_code


@app.route("/orders/<user>")
def orders(user):
    resp = requests.get(f"{ORDER_URL}/orders/{user}", timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/health")
def health():
    return jsonify(status="ok", service="gateway-service", hostname=socket.gethostname())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
