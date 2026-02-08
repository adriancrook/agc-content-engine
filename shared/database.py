"""
Shared database module - connects to Supabase
Used by both Railway frontend and Mac Mini worker
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }


def _request(method, table, params="", data=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}{params}"
    try:
        r = requests.request(method, url, headers=_headers(), json=data, timeout=10)
        if r.status_code in (200, 201):
            return r.json()
        print(f"DB error: {r.status_code} - {r.text}")
        return None
    except Exception as e:
        print(f"DB exception: {e}")
        return None


# Topics
def get_topics(status: Optional[str] = None, limit: int = 50) -> List[Dict]:
    params = f"?order=created_at.desc&limit={limit}"
    if status:
        params += f"&status=eq.{status}"
    return _request("GET", "topics", params) or []


def create_topic(title: str, keyword: str = None) -> Optional[Dict]:
    return _request("POST", "topics", "", {
        "title": title,
        "keyword": keyword or title.lower().replace(" ", "-"),
        "status": "pending"
    })


def update_topic(topic_id: str, updates: Dict) -> Optional[Dict]:
    updates["updated_at"] = datetime.utcnow().isoformat()
    result = _request("PATCH", "topics", f"?id=eq.{topic_id}", updates)
    return result[0] if result else None


def approve_topic(topic_id: str) -> Optional[Dict]:
    return update_topic(topic_id, {
        "status": "approved",
        "approved_at": datetime.utcnow().isoformat()
    })


def decline_topic(topic_id: str) -> Optional[Dict]:
    return update_topic(topic_id, {"status": "declined"})


def count_topics_by_status() -> Dict[str, int]:
    topics = get_topics(limit=1000)
    counts = {"pending": 0, "approved": 0, "declined": 0, "processing": 0, "completed": 0}
    for t in topics:
        status = t.get("status", "pending")
        counts[status] = counts.get(status, 0) + 1
    return counts


# Tasks
def create_task(task_type: str, payload: Dict, article_id: str = None) -> Optional[Dict]:
    return _request("POST", "tasks", "", {
        "type": task_type,
        "payload": json.dumps(payload),
        "article_id": article_id,
        "status": "pending"
    })


def get_pending_tasks(limit: int = 10) -> List[Dict]:
    return _request("GET", "tasks", f"?status=eq.pending&order=created_at&limit={limit}") or []


def update_task(task_id: str, status: str, result: Dict = None) -> Optional[Dict]:
    data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
    if result:
        data["result"] = json.dumps(result)
    if status == "processing":
        data["started_at"] = datetime.utcnow().isoformat()
    if status in ("completed", "failed"):
        data["completed_at"] = datetime.utcnow().isoformat()
    res = _request("PATCH", "tasks", f"?id=eq.{task_id}", data)
    return res[0] if res else None


# Articles
def create_article(topic_id: str, title: str) -> Optional[Dict]:
    return _request("POST", "articles", "", {
        "topic_id": topic_id,
        "title": title,
        "status": "draft",
        "stage": "research"
    })


def get_articles(status: Optional[str] = None, limit: int = 20) -> List[Dict]:
    params = f"?order=created_at.desc&limit={limit}"
    if status:
        params += f"&status=eq.{status}"
    return _request("GET", "articles", params) or []


def update_article(article_id: str, updates: Dict) -> Optional[Dict]:
    updates["updated_at"] = datetime.utcnow().isoformat()
    res = _request("PATCH", "articles", f"?id=eq.{article_id}", updates)
    return res[0] if res else None
