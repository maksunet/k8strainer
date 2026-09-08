import os
import socket
from itertools import count

from flask import Flask, jsonify

app = Flask(__name__)
_counter = count(1)

@app.route("/")
def index():
    return jsonify(
        hits=next(_counter),
        hostname=socket.gethostname(),
        version=os.environ.get("APP_VERSION", "dev"),
    )

@app.route("/health")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
