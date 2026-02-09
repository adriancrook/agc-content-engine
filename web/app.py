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

from flask import Flask, render_template, request, jsonify, send_from_directory

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import (
    init_db, get_topics, create_topic, update_topic, approve_topic, decline_topic, delete_topic,
    count_topics_by_status, get_pending_tasks, get_active_tasks, create_task, claim_task, complete_task,
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
        # Update topic to processing status
        update_topic(topic_id, {"status": "processing"})
        result["status"] = "processing"
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


@app.route("/api/tasks/active")
def api_active_tasks():
    """Returns both pending and processing tasks for dashboard visibility"""
    limit = int(request.args.get("limit", 50))
    return jsonify(get_active_tasks(limit=limit))


@app.route("/api/tasks", methods=["POST"])
def api_create_task():
    data = request.json
    task = create_task(data.get("type"), data.get("payload", {}), data.get("article_id"))
    return jsonify(task), 201


@app.route("/api/tasks/<task_id>/claim", methods=["POST"])
def api_claim_task(task_id):
    data = request.json or {}
    worker_id = data.get("worker_id", "unknown")
    result = claim_task(task_id, worker_id)
    return jsonify(result) if result else ("Already claimed or not found", 409)


@app.route("/api/tasks/<task_id>/complete", methods=["POST"])
def api_complete_task(task_id):
    data = request.json or {}
    task_result = data.get("result", {})
    result = complete_task(task_id, task_result)
    
    if not result:
        return ("Not found", 404)
    
    # Get the task to chain to next step
    from shared.database import get_session, Task
    with get_session() as session:
        task = session.query(Task).filter_by(id=task_id).first()
        if task:
            # Chain tasks based on type
            if task.type == "research" and "research" in task_result:
                # Research done -> create write task with research data
                create_task("write", {
                    "topic": task_result.get("research", {}).get("topic", ""),
                    "research": task_result.get("research", {})
                }, task.article_id)
                
            elif task.type == "write" and "draft" in task_result:
                # Write done -> save content and create fact_check task
                if task.article_id:
                    draft_content = task_result.get("draft", "")
                    if isinstance(draft_content, dict):
                        # Extract markdown from dict if needed
                        draft_content = draft_content.get("markdown", str(draft_content))
                    update_article(task.article_id, {"draft_content": draft_content, "status": "written"})
                    create_task("fact_check", {"draft": draft_content}, task.article_id)
                    
            elif task.type == "fact_check" and "verified" in task_result:
                # Fact check done -> create SEO task
                create_task("seo", {
                    "draft": task_result.get("verified", ""),
                    "keyword": task_result.get("keyword", "")
                }, task.article_id)
    
    return jsonify(result)


@app.route("/api/tasks/<task_id>/fail", methods=["POST"])
def api_fail_task(task_id):
    data = request.json or {}
    result = fail_task(task_id, data.get("error", "Unknown error"))
    return jsonify(result) if result else ("Not found", 404)


@app.route("/api/tasks/reset-stuck", methods=["POST"])
def api_reset_stuck_tasks():
    """Reset tasks stuck in 'processing' for more than 1 hour"""
    from shared.database import get_session, Task
    from datetime import timedelta

    with get_session() as session:
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        stuck_tasks = session.query(Task).filter(
            Task.status == "processing",
            Task.started_at < cutoff_time
        ).all()

        reset_count = 0
        for task in stuck_tasks:
            task.status = "pending"
            task.worker_id = None
            task.started_at = None
            reset_count += 1

        session.commit()
        return jsonify({"reset_count": reset_count, "message": f"Reset {reset_count} stuck task(s)"})



# Articles API
@app.route("/api/articles")
def api_get_articles():
    status = request.args.get("status")
    limit = int(request.args.get("limit", 20))
    return jsonify(get_articles(status=status, limit=limit))


@app.route("/api/articles/<article_id>", methods=["GET"])
def api_get_article(article_id):
    """Get full article details including content"""
    from shared.database import get_session, Article
    with get_session() as session:
        article = session.query(Article).filter_by(id=article_id).first()
        if article:
            return jsonify({
                "id": article.id,
                "title": article.title,
                "status": article.status,
                "draft_content": article.draft_content,
                "word_count": len(article.draft_content.split()) if article.draft_content else 0
            })
        return ("Not found", 404)


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


# ========================================
# PIXEL DASHBOARD (Moltcraft-style)
# ========================================

# In Docker, working dir is /app, so dashboard is at /app/dashboard
DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"

@app.route("/debug-path")
def debug_path():
    import os
    cwd = os.getcwd()
    files = os.listdir(cwd)
    dash_exists = DASHBOARD_DIR.exists()
    dash_files = list(DASHBOARD_DIR.iterdir()) if dash_exists else []
    return f"CWD: {cwd}\nFiles: {files}\nDashboard exists: {dash_exists}\nDashboard path: {DASHBOARD_DIR}\nDashboard files: {dash_files}"

@app.route("/dashboard")
@app.route("/dashboard/")
def dashboard():
    if not DASHBOARD_DIR.exists():
        return f"Dashboard not found at {DASHBOARD_DIR}", 404
    return send_from_directory(str(DASHBOARD_DIR), "index.html")

@app.route("/dashboard/<path:filename>")
def dashboard_static(filename):
    return send_from_directory(str(DASHBOARD_DIR), filename)

# Serve dashboard assets from root paths (for relative URLs in HTML)
@app.route("/css/<path:filename>")
def dashboard_css(filename):
    return send_from_directory(str(DASHBOARD_DIR / "css"), filename)

@app.route("/js/<path:filename>")
def dashboard_js(filename):
    return send_from_directory(str(DASHBOARD_DIR / "js"), filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 AGC Content Engine")
    print(f"   http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
