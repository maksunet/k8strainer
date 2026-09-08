import os
import socket

from flask import Flask, jsonify, abort

app = Flask(__name__)

PRODUCTS = {
    "1": {"id": "1", "name": "Mekanik Klavye", "price": 1200},
    "2": {"id": "2", "name": "Kablosuz Mouse", "price": 350},
    "3": {"id": "3", "name": "27 inch Monitor", "price": 4500},
    "4": {"id": "4", "name": "USB-C Hub", "price": 280},
    "5": {"id": "5", "name": "Webcam 1080p", "price": 600},
}


@app.route("/products")
def list_products():
    return jsonify(list(PRODUCTS.values()))


@app.route("/products/<product_id>")
def get_product(product_id):
    product = PRODUCTS.get(product_id)
    if not product:
        abort(404, description="product not found")
    return jsonify(product)


@app.route("/health")
def health():
    return jsonify(status="ok", service="catalog-service", hostname=socket.gethostname())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
