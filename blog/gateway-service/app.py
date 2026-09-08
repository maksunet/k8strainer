import os
import socket

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

AUTH_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth-service")
BLOG_URL = os.environ.get("BLOG_SERVICE_URL", "http://blog-service")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/register", methods=["POST"])
def register():
    resp = requests.post(f"{AUTH_URL}/register", json=request.get_json(force=True), timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/api/login", methods=["POST"])
def login():
    resp = requests.post(f"{AUTH_URL}/login", json=request.get_json(force=True), timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/api/posts", methods=["GET"])
def list_posts():
    resp = requests.get(f"{BLOG_URL}/posts", timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/api/posts", methods=["POST"])
def create_post():
    headers = {}
    auth = request.headers.get("Authorization")
    if auth:
        headers["Authorization"] = auth
    resp = requests.post(f"{BLOG_URL}/posts", json=request.get_json(force=True), headers=headers, timeout=5)
    return jsonify(resp.json()), resp.status_code


@app.route("/health")
def health():
    return jsonify(status="ok", service="gateway-service", hostname=socket.gethostname())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
