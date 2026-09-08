import os
import socket
import time

import jwt
import psycopg2
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_TTL_SECONDS = 15 * 60

DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "auth_db")
DB_USER = os.environ.get("DB_USER", "blog")
DB_PASSWORD = os.environ["DB_PASSWORD"]


def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)


def init_db():
    for attempt in range(10):
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            email TEXT UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                conn.commit()
            return
        except psycopg2.OperationalError:
            time.sleep(3)
    raise RuntimeError("could not connect to auth_db")


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify(error="email and password required"), 400

    password_hash = generate_password_hash(password)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                    (email, password_hash),
                )
                user_id = cur.fetchone()[0]
            conn.commit()
    except psycopg2.errors.UniqueViolation:
        return jsonify(error="email already registered"), 409

    return jsonify(id=user_id, email=email), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
            row = cur.fetchone()

    if not row or not check_password_hash(row[1], password):
        return jsonify(error="invalid credentials"), 401

    user_id = row[0]
    now = int(time.time())
    token = jwt.encode(
        {"sub": email, "uid": user_id, "iat": now, "exp": now + JWT_TTL_SECONDS},
        JWT_SECRET,
        algorithm="HS256",
    )
    return jsonify(token=token, expires_in=JWT_TTL_SECONDS)


@app.route("/health")
def health():
    return jsonify(status="ok", service="auth-service", hostname=socket.gethostname())


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
