#!/usr/bin/env python3
"""
AGC Content Engine - Web Interface

Simple Flask UI for generating articles without shell commands.
"""

import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import ContentPipeline

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Store active jobs
active_jobs = {}
completed_jobs = {}

# Initialize pipeline
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = ContentPipeline(
            config_path=str(Path(__file__).parent.parent / ".config" / "default.json"),
            output_dir=str(Path(__file__).parent.parent / "outputs"),
        )
    return pipeline


def run_pipeline_async(job_id, topic, keywords, primary_keyword):
    """Run pipeline in background thread."""
    try:
        active_jobs[job_id]["status"] = "running"
        active_jobs[job_id]["stage"] = "Starting..."
        
        p = get_pipeline()
        result = p.run(
            topic=topic,
            keywords=keywords,
            primary_keyword=primary_keyword,
        )
        
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["result"] = result
        completed_jobs[job_id] = active_jobs[job_id]
        
    except Exception as e:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)


@app.route("/")
def index():
    """Main page with article generation form."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """Start article generation."""
    data = request.json
    
    topic = data.get("topic", "").strip()
    keywords_raw = data.get("keywords", "").strip()
    primary_keyword = data.get("primary_keyword", "").strip() or topic
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400
    
    # Parse keywords
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
    
    # Create job
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    active_jobs[job_id] = {
        "id": job_id,
        "topic": topic,
        "keywords": keywords,
        "primary_keyword": primary_keyword,
        "status": "queued",
        "stage": "Initializing...",
        "started_at": datetime.now().isoformat(),
    }
    
    # Start background thread
    thread = threading.Thread(
        target=run_pipeline_async,
        args=(job_id, topic, keywords, primary_keyword),
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id, "status": "started"})


@app.route("/status/<job_id>")
def status(job_id):
    """Get job status."""
    if job_id in active_jobs:
        job = active_jobs[job_id]
        response = {
            "id": job_id,
            "status": job["status"],
            "stage": job.get("stage", ""),
            "topic": job["topic"],
        }
        
        if job["status"] == "completed" and "result" in job:
            result = job["result"]
            response["success"] = result.get("success", False)
            response["score"] = result.get("metadata", {}).get("overall_score", 0)
            response["word_count"] = result.get("metadata", {}).get("word_count", 0)
            response["workspace"] = result.get("workspace", "")
            
        elif job["status"] == "failed":
            response["error"] = job.get("error", "Unknown error")
            
        return jsonify(response)
    
    return jsonify({"error": "Job not found"}), 404


@app.route("/article/<job_id>")
def get_article(job_id):
    """Get the generated article content."""
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = active_jobs[job_id]
    if job["status"] != "completed":
        return jsonify({"error": "Article not ready"}), 400
    
    result = job.get("result", {})
    workspace = result.get("workspace", "")
    
    if not workspace:
        return jsonify({"error": "No workspace found"}), 400
    
    article_path = Path(workspace) / "FINAL_ARTICLE.md"
    if not article_path.exists():
        return jsonify({"error": "Article file not found"}), 404
    
    article_content = article_path.read_text()
    metadata = result.get("metadata", {})
    
    return jsonify({
        "article": article_content,
        "metadata": metadata,
    })


@app.route("/jobs")
def list_jobs():
    """List all jobs."""
    jobs = []
    for job_id, job in sorted(active_jobs.items(), reverse=True):
        jobs.append({
            "id": job_id,
            "topic": job["topic"],
            "status": job["status"],
            "started_at": job["started_at"],
        })
    return jsonify({"jobs": jobs})


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    """Serve output files."""
    outputs_dir = Path(__file__).parent.parent / "outputs"
    return send_from_directory(outputs_dir, filename)


if __name__ == "__main__":
    # Ensure templates directory exists
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    print("🚀 AGC Content Engine Web UI")
    print("   http://localhost:8080")
    print("   Press Ctrl+C to stop")
    
    app.run(host="0.0.0.0", port=8080, debug=False)
