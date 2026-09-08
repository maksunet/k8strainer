import json
import os
import socket
import time
import uuid

import redis
import requests
from flask import Flask, jsonify, abort

app = Flask(__name__)

CATALOG_URL = os.environ.get("CATALOG_SERVICE_URL", "http://catalog-service")
CART_URL = os.environ.get("CART_SERVICE_URL", "http://cart-service")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def orders_key(user):
    return f"orders:{user}"


@app.route("/orders/<user>", methods=["GET"])
def list_orders(user):
    raw = r.lrange(orders_key(user), 0, -1)
    return jsonify([json.loads(o) for o in raw])


@app.route("/orders/<user>/checkout", methods=["POST"])
def checkout(user):
    cart_resp = requests.get(f"{CART_URL}/cart/{user}", timeout=5)
    cart_resp.raise_for_status()
    cart = cart_resp.json()

    if not cart:
        abort(400, description="cart is empty")

    items = []
    total = 0
    for product_id, qty in cart.items():
        product_resp = requests.get(f"{CATALOG_URL}/products/{product_id}", timeout=5)
        if product_resp.status_code != 200:
            continue
        product = product_resp.json()
        subtotal = product["price"] * qty
        total += subtotal
        items.append({"product": product, "qty": qty, "subtotal": subtotal})

    order = {
        "id": str(uuid.uuid4())[:8],
        "user": user,
        "items": items,
        "total": total,
        "created_at": int(time.time()),
    }

    r.lpush(orders_key(user), json.dumps(order))
    requests.delete(f"{CART_URL}/cart/{user}", timeout=5)

    return jsonify(order), 201


@app.route("/health")
def health():
    return jsonify(status="ok", service="order-service", hostname=socket.gethostname())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
