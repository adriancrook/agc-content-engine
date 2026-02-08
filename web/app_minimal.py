#!/usr/bin/env python3
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>AGC Content Engine</h1><p>Minimal test OK</p>"

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
