import os
import socket

import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def cart_key(user):
    return f"cart:{user}"


@app.route("/cart/<user>", methods=["GET"])
def get_cart(user):
    items = r.hgetall(cart_key(user))
    return jsonify({pid: int(qty) for pid, qty in items.items()})


@app.route("/cart/<user>/add", methods=["POST"])
def add_to_cart(user):
    data = request.get_json(force=True)
    product_id = str(data["product_id"])
    qty = int(data.get("qty", 1))
    r.hincrby(cart_key(user), product_id, qty)
    items = r.hgetall(cart_key(user))
    return jsonify({pid: int(q) for pid, q in items.items()})


@app.route("/cart/<user>", methods=["DELETE"])
def clear_cart(user):
    r.delete(cart_key(user))
    return jsonify(cleared=True)


@app.route("/health")
def health():
    try:
        r.ping()
        redis_ok = True
    except redis.exceptions.RedisError:
        redis_ok = False
    return jsonify(status="ok" if redis_ok else "degraded", service="cart-service", hostname=socket.gethostname(), redis=redis_ok)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
