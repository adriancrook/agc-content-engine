#!/usr/bin/env python3
"""
AGC Content Engine - Web Interface + API
Railway frontend with API for Mac Mini worker
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import (
    init_db, get_topics, create_topic, update_topic, approve_topic, decline_topic, delete_topic,
    count_topics_by_status, get_pending_tasks, create_task, claim_task, complete_task,
    fail_task, get_articles, create_article, update_article, get_setting, set_setting
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database on startup
with app.app_context():
    init_db()


# ============ WEB UI ROUTES ============

@app.route("/")
def index():
    """Main dashboard"""
    topic_counts = count_topics_by_status()
    pending_topics = get_topics(status="pending", limit=20)
    recent_articles = get_articles(limit=10)
    
    return render_template("index.html",
        topic_counts=topic_counts,
        pending_topics=pending_topics,
        recent_articles=recent_articles
    )


@app.route("/topics")
def topics_page():
    """Topic management page"""
    status_filter = request.args.get("status", None)
    topics = get_topics(status=status_filter, limit=100)
    counts = count_topics_by_status()
    return render_template("topics.html", topics=topics, counts=counts, current_status=status_filter)


@app.route("/articles")
def articles_page():
    """Articles list page"""
    articles = get_articles(limit=50)
    return render_template("articles.html", articles=articles)


# ============ API ROUTES (for Mac Mini worker) ============

@app.route("/api/health")
def api_health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


# Topics API
@app.route("/api/topics", methods=["GET"])
def api_get_topics():
    status = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    return jsonify(get_topics(status=status, limit=limit))


@app.route("/api/topics", methods=["POST"])
def api_create_topic():
    data = request.json
    result = create_topic(data.get("title"), data.get("keyword"))
    return jsonify(result), 201


@app.route("/api/topics/<topic_id>", methods=["PATCH"])
def api_update_topic(topic_id):
    data = request.json
    result = update_topic(topic_id, data)
    return jsonify(result) if result else ("Not found", 404)


@app.route("/api/topics/<topic_id>/approve", methods=["POST"])
def api_approve_topic(topic_id):
    result = approve_topic(topic_id)
    if result:
        # Auto-create article and research task for approved topics
        article = create_article(topic_id, result.get("title"))
        create_task("research", {"topic": result.get("title"), "keyword": result.get("keyword")}, article.get("id"))
    return jsonify(result) if result else ("Not found", 404)


@app.route("/api/topics/<topic_id>/decline", methods=["POST"])
def api_decline_topic(topic_id):
    result = decline_topic(topic_id)
    return jsonify(result) if result else ("Not found", 404)


@app.route("/api/topics/<topic_id>", methods=["DELETE"])
def api_delete_topic(topic_id):
    result = delete_topic(topic_id)
    return jsonify({"deleted": True}) if result else ("Not found", 404)


@app.route("/api/topics/counts")
def api_topic_counts():
    return jsonify(count_topics_by_status())


@app.route("/api/topics/generate", methods=["POST"])
def api_generate_topics():
    """Queue topic generation task"""
    data = request.json or {}
    count = data.get("count", 20)
    focus_areas = data.get("focus_areas", [])
    
    task = create_task("generate_topics", {
        "count": count,
        "focus_areas": focus_areas
    })
    return jsonify(task), 201


# Tasks API (for worker)
@app.route("/api/tasks/pending")
def api_pending_tasks():
    limit = int(request.args.get("limit", 10))
    return jsonify(get_pending_tasks(limit=limit))


@app.route("/api/tasks/<task_id>/claim", methods=["POST"])
def api_claim_task(task_id):
    data = request.json or {}
    worker_id = data.get("worker_id", "unknown")
    result = claim_task(task_id, worker_id)
    return jsonify(result) if result else ("Already claimed or not found", 409)


@app.route("/api/tasks/<task_id>/complete", methods=["POST"])
def api_complete_task(task_id):
    data = request.json or {}
    result = complete_task(task_id, data.get("result", {}))
    return jsonify(result) if result else ("Not found", 404)


@app.route("/api/tasks/<task_id>/fail", methods=["POST"])
def api_fail_task(task_id):
    data = request.json or {}
    result = fail_task(task_id, data.get("error", "Unknown error"))
    return jsonify(result) if result else ("Not found", 404)


# Articles API
@app.route("/api/articles")
def api_get_articles():
    status = request.args.get("status")
    limit = int(request.args.get("limit", 20))
    return jsonify(get_articles(status=status, limit=limit))


@app.route("/api/articles/<article_id>", methods=["PATCH"])
def api_update_article(article_id):
    data = request.json
    result = update_article(article_id, data)
    return jsonify(result) if result else ("Not found", 404)


# Settings API
@app.route("/api/settings/<key>")
def api_get_setting(key):
    value = get_setting(key)
    return jsonify({"key": key, "value": value}) if value else ("Not found", 404)


@app.route("/api/settings/<key>", methods=["PUT"])
def api_set_setting(key):
    data = request.json
    set_setting(key, data.get("value", {}))
    return jsonify({"key": key, "status": "updated"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 AGC Content Engine")
    print(f"   http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
