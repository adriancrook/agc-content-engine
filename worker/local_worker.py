#!/usr/bin/env python3
"""
AGC Local Worker - Runs on Mac Mini
Polls Supabase for tasks, processes with local Ollama, updates results
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research import ResearchAgent
from agents.writer import WriterAgent
from agents.fact_checker import FactCheckerAgent
from agents.seo import SEOAgent
from agents.topic_discovery import TopicDiscoveryAgent
from agents.base import AgentInput

# Supabase config (will be set via env vars)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))  # seconds

# Local Ollama config
OLLAMA_URL = "http://localhost:11434"


class LocalWorker:
    def __init__(self):
        self.research_agent = ResearchAgent()
        self.writer_agent = WriterAgent()
        self.fact_checker = FactCheckerAgent()
        self.seo_agent = SEOAgent()
        self.topic_agent = TopicDiscoveryAgent(
            brave_api_key=os.getenv("BRAVE_API_KEY", ""),
            niche="mobile gaming and game design",
            blog_url="https://adriancrook.com"
        )
        
    def check_ollama(self):
        """Verify Ollama is running"""
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def poll_tasks(self):
        """Get pending tasks from Supabase"""
        if not SUPABASE_URL:
            print("No Supabase URL configured")
            return []
            
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        
        try:
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/tasks?status=eq.pending&order=created_at",
                headers=headers,
                timeout=10
            )
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"Error polling tasks: {e}")
            return []
    
    def update_task(self, task_id, status, result=None):
        """Update task status in Supabase"""
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        if result:
            data["result"] = json.dumps(result)
            
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/tasks?id=eq.{task_id}",
            headers=headers,
            json=data
        )
    
    def process_task(self, task):
        """Process a single task with local agents"""
        task_type = task.get("type")
        task_id = task.get("id")
        payload = json.loads(task.get("payload", "{}"))
        
        print(f"Processing task {task_id}: {task_type}")
        self.update_task(task_id, "processing")
        
        try:
            if task_type == "generate_topics":
                result = self.generate_topics(payload)
            elif task_type == "research":
                result = self.do_research(payload)
            elif task_type == "write":
                result = self.do_write(payload)
            elif task_type == "fact_check":
                result = self.do_fact_check(payload)
            elif task_type == "seo":
                result = self.do_seo(payload)
            else:
                result = {"error": f"Unknown task type: {task_type}"}
                
            self.update_task(task_id, "completed", result)
            print(f"Task {task_id} completed")
            
        except Exception as e:
            self.update_task(task_id, "failed", {"error": str(e)})
            print(f"Task {task_id} failed: {e}")
    
    def generate_topics(self, payload):
        """Generate topic suggestions"""
        count = payload.get("count", 20)
        focus_areas = payload.get("focus_areas", [])
        
        agent_input = AgentInput(
            topic=f"Generate {count} SEO-optimized blog topic ideas",
            context={"focus_areas": focus_areas}
        )
        
        result = self.topic_agent.run(agent_input)
        return {"topics": result.content if hasattr(result, 'content') else str(result)}
    
    def do_research(self, payload):
        """Research a topic"""
        topic = payload.get("topic", "")
        agent_input = AgentInput(topic=topic, context=payload)
        result = self.research_agent.run(agent_input)
        return {"research": result.content if hasattr(result, 'content') else str(result)}
    
    def do_write(self, payload):
        """Write article draft"""
        topic = payload.get("topic", "")
        research = payload.get("research", "")
        agent_input = AgentInput(topic=topic, context={"research": research})
        result = self.writer_agent.run(agent_input)
        return {"draft": result.content if hasattr(result, 'content') else str(result)}
    
    def do_fact_check(self, payload):
        """Fact check draft"""
        draft = payload.get("draft", "")
        agent_input = AgentInput(topic="Fact check", context={"draft": draft})
        result = self.fact_checker.run(agent_input)
        return {"verified": result.content if hasattr(result, 'content') else str(result)}
    
    def do_seo(self, payload):
        """SEO optimize"""
        draft = payload.get("draft", "")
        keyword = payload.get("keyword", "")
        agent_input = AgentInput(topic=keyword, context={"draft": draft})
        result = self.seo_agent.run(agent_input)
        return {"optimized": result.content if hasattr(result, 'content') else str(result)}
    
    def run(self):
        """Main worker loop"""
        print("=" * 50)
        print("AGC Local Worker Starting")
        print(f"Ollama: {OLLAMA_URL}")
        print(f"Supabase: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "Supabase: Not configured")
        print(f"Poll interval: {POLL_INTERVAL}s")
        print("=" * 50)
        
        if not self.check_ollama():
            print("WARNING: Ollama not running!")
        
        while True:
            tasks = self.poll_tasks()
            
            for task in tasks:
                self.process_task(task)
            
            if not tasks:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No pending tasks")
            
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    worker = LocalWorker()
    worker.run()
