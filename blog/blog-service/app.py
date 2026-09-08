import os
import socket
import time

import jwt
import psycopg2
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

JWT_SECRET = os.environ["JWT_SECRET"]

DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "blog_db")
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
                        CREATE TABLE IF NOT EXISTS posts (
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            body TEXT NOT NULL,
                            author TEXT NOT NULL,
                            created_at TIMESTAMPTZ DEFAULT now()
                        )
                        """
                    )
                conn.commit()
            return
        except psycopg2.OperationalError:
            time.sleep(3)
    raise RuntimeError("could not connect to blog_db")


def current_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        abort(401, description="missing bearer token")
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        abort(401, description="invalid or expired token")
    return payload["sub"]


@app.route("/posts", methods=["GET"])
def list_posts():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, body, author, created_at FROM posts ORDER BY created_at DESC")
            rows = cur.fetchall()
    posts = [
        {"id": r[0], "title": r[1], "body": r[2], "author": r[3], "created_at": r[4].isoformat()}
        for r in rows
    ]
    return jsonify(posts)


@app.route("/posts", methods=["POST"])
def create_post():
    author = current_user()
    data = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title or not body:
        return jsonify(error="title and body required"), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (title, body, author) VALUES (%s, %s, %s) RETURNING id, created_at",
                (title, body, author),
            )
            post_id, created_at = cur.fetchone()
        conn.commit()

    return jsonify(id=post_id, title=title, body=body, author=author, created_at=created_at.isoformat()), 201


@app.route("/health")
def health():
    return jsonify(status="ok", service="blog-service", hostname=socket.gethostname())


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
