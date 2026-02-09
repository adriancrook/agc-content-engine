#!/usr/bin/env python3
"""
AGC Local Worker - Runs on Mac Mini
Polls Railway API for tasks, processes with local Ollama, updates results
"""

import os
import sys
import json
import time
import socket
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

# Railway API config
API_URL = os.getenv("AGC_API_URL", "https://web-production-c28a3.up.railway.app")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
WORKER_ID = os.getenv("WORKER_ID", socket.gethostname())

# Local Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")


class LocalWorker:
    def __init__(self):
        print(f"Initializing agents...")
        self.research_agent = None
        self.writer_agent = None
        self.fact_checker = None
        self.seo_agent = None
        self.topic_agent = None
        self._init_agents()
        
    def _init_agents(self):
        """Lazy init agents"""
        brave_api_key = os.getenv("BRAVE_API_KEY", "")
        try:
            self.research_agent = ResearchAgent(brave_api_key=brave_api_key)
            self.writer_agent = WriterAgent()
            self.fact_checker = FactCheckerAgent()
            self.seo_agent = SEOAgent()
            self.topic_agent = TopicDiscoveryAgent(
                brave_api_key=brave_api_key,
                niche="mobile gaming and game design",
                blog_url="https://adriancrook.com"
            )
            print("✅ Agents initialized")
        except Exception as e:
            print(f"⚠️ Agent init error: {e}")
            import traceback
            traceback.print_exc()
        
    def check_ollama(self):
        """Verify Ollama is running"""
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            models = r.json().get("models", [])
            model_names = [m.get("name") for m in models]
            print(f"   Ollama models: {', '.join(model_names)}")
            return r.status_code == 200
        except Exception as e:
            print(f"   Ollama error: {e}")
            return False
    
    def check_api(self):
        """Verify Railway API is reachable"""
        try:
            r = requests.get(f"{API_URL}/api/health", timeout=10)
            return r.status_code == 200
        except Exception as e:
            print(f"   API error: {e}")
            return False
    
    def poll_tasks(self):
        """Get pending tasks from Railway API"""
        try:
            r = requests.get(f"{API_URL}/api/tasks/pending?limit=5", timeout=10)
            return r.json() if r.status_code == 200 else []
        except Exception as e:
            print(f"Error polling tasks: {e}")
            return []
    
    def claim_task(self, task_id):
        """Claim a task for processing"""
        try:
            r = requests.post(
                f"{API_URL}/api/tasks/{task_id}/claim",
                json={"worker_id": WORKER_ID},
                timeout=10
            )
            return r.json() if r.status_code == 200 else None
        except:
            return None
    
    def complete_task(self, task_id, result, article_id=None):
        """Mark task as completed and save article content to Railway API"""
        try:
            print(f"   DEBUG: article_id={article_id}, keys in result={list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
            
            requests.post(
                f"{API_URL}/api/tasks/{task_id}/complete",
                json={"result": result},
                timeout=30
            )
            
            # Save article content directly to Railway API
            if article_id and "draft" in result:
                draft = result["draft"]
                print(f"   DEBUG: draft type={type(draft)}, len={len(str(draft))}")
                if isinstance(draft, dict):
                    draft = draft.get("markdown", str(draft))
                r = requests.put(
                    f"{API_URL}/api/articles/{article_id}",
                    json={"draft_content": draft, "status": "written"},
                    timeout=10
                )
                print(f"   📝 Article PUT response: {r.status_code} - {len(draft)} chars")
            else:
                print(f"   DEBUG: Not saving article - article_id={article_id}, 'draft' in result={'draft' in result if isinstance(result, dict) else False}")
        except Exception as e:
            import traceback
            print(f"Error completing task: {e}")
            traceback.print_exc()
    
    def fail_task(self, task_id, error):
        """Mark task as failed"""
        try:
            requests.post(
                f"{API_URL}/api/tasks/{task_id}/fail",
                json={"error": str(error)},
                timeout=10
            )
        except:
            pass
    
    def save_topics(self, topics):
        """Save generated topics to Railway"""
        for topic in topics:
            try:
                # Generate SEO-friendly slug from title
                keyword = topic.lower().replace(" ", "-").replace(":", "").replace("'", "")
                requests.post(
                    f"{API_URL}/api/topics",
                    json={"title": topic, "keyword": keyword},
                    timeout=10
                )
            except:
                pass
    
    def process_task(self, task):
        """Process a single task with local agents"""
        task_type = task.get("type")
        task_id = task.get("id")
        payload = task.get("payload", {})
        
        if isinstance(payload, str):
            payload = json.loads(payload)
        
        print(f"\n{'='*50}")
        print(f"Processing: {task_type} (ID: {task_id[:8]}...)")
        print(f"🖥️  Model: qwen2.5:14b (LOCAL Ollama)")
        print(f"💰 Cost: $0.00 (free local processing)")
        print(f"{'='*50}")
        
        # Claim the task
        claimed = self.claim_task(task_id)
        if not claimed:
            print("❌ Could not claim task (already taken?)")
            return
        
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
                
            # Pass article_id for write tasks
            article_id = task.get("article_id")
            self.complete_task(task_id, result, article_id)
            print(f"✅ Task completed")
            
        except Exception as e:
            print(f"❌ Task failed: {e}")
            self.fail_task(task_id, str(e))
    
    def generate_topics(self, payload):
        """Generate topic suggestions using local model"""
        count = payload.get("count", 20)
        focus_areas = payload.get("focus_areas", [
            "mobile game monetization",
            "freemium game design", 
            "game economy modeling",
            "player retention strategies",
            "in-app purchase optimization"
        ])
        
        print(f"Generating {count} topics for: {', '.join(focus_areas)}")
        
        if self.topic_agent:
            agent_input = AgentInput(
                data={
                    "topic": f"Generate {count} unique, SEO-optimized blog topic ideas for a mobile game consulting blog. Focus areas: {', '.join(focus_areas)}. Each topic should target a specific long-tail keyword.",
                    "focus_areas": focus_areas,
                    "count": count
                },
                workspace=Path("/tmp/agc")
            )
            
            result = self.topic_agent.run(agent_input)
            
            # Extract topics from AgentOutput.data
            topics = []
            if hasattr(result, 'data') and isinstance(result.data, dict):
                raw_topics = result.data.get("topics", [])
                for t in raw_topics:
                    if isinstance(t, dict):
                        title = t.get("title", "")
                        if title:
                            topics.append(title)
                    elif isinstance(t, str):
                        topics.append(t)
            
            print(f"Generated {len(topics)} topics")
            
            # Save topics to Railway
            self.save_topics(topics[:count])
            
            return {"topics_generated": len(topics[:count]), "topics": topics[:count]}
        else:
            return {"error": "Topic agent not initialized"}
    
    def do_research(self, payload):
        """Research a topic using local model"""
        topic = payload.get("topic", "")
        print(f"Researching: {topic}")
        
        if self.research_agent:
            agent_input = AgentInput(data={"topic": topic, **payload}, workspace=Path("/tmp/agc"))
            result = self.research_agent.run(agent_input)
            return {"research": result.data if hasattr(result, 'data') else str(result)}
        return {"error": "Research agent not initialized"}
    
    def do_write(self, payload):
        """Write article draft using local model"""
        topic = payload.get("topic", "")
        research = payload.get("research", "")
        print(f"Writing draft for: {topic}")
        
        if self.writer_agent:
            agent_input = AgentInput(data={"topic": topic, "research": research}, workspace=Path("/tmp/agc"))
            result = self.writer_agent.run(agent_input)
            return {"draft": result.data if hasattr(result, 'data') else str(result)}
        return {"error": "Writer agent not initialized"}
    
    def do_fact_check(self, payload):
        """Fact check draft using local model"""
        draft = payload.get("draft", "")
        print("Fact checking draft...")
        
        if self.fact_checker:
            agent_input = AgentInput(data={"topic": "Fact check", "draft": draft}, workspace=Path("/tmp/agc"))
            result = self.fact_checker.run(agent_input)
            return {"verified": result.data if hasattr(result, 'data') else str(result)}
        return {"error": "Fact checker not initialized"}
    
    def do_seo(self, payload):
        """SEO optimize using local model"""
        draft = payload.get("draft", "")
        keyword = payload.get("keyword", "")
        print(f"SEO optimizing for: {keyword}")
        
        if self.seo_agent:
            agent_input = AgentInput(data={"topic": keyword, "draft": draft}, workspace=Path("/tmp/agc"))
            result = self.seo_agent.run(agent_input)
            return {"optimized": result.data if hasattr(result, 'data') else str(result)}
        return {"error": "SEO agent not initialized"}
    
    def run(self):
        """Main worker loop"""
        print("\n" + "="*60)
        print("   AGC LOCAL WORKER")
        print("="*60)
        print(f"   Worker ID: {WORKER_ID}")
        print(f"   API URL: {API_URL}")
        print(f"   Ollama: {OLLAMA_URL}")
        print(f"   Poll interval: {POLL_INTERVAL}s")
        print("="*60 + "\n")
        
        # Check connections
        print("Checking connections...")
        ollama_ok = self.check_ollama()
        api_ok = self.check_api()
        
        if not ollama_ok:
            print("⚠️  WARNING: Ollama not running! Start with: ollama serve")
        if not api_ok:
            print("⚠️  WARNING: Cannot reach Railway API!")
        
        if ollama_ok and api_ok:
            print("\n✅ All systems ready. Waiting for tasks...\n")
        
        while True:
            try:
                tasks = self.poll_tasks()
                
                if tasks:
                    print(f"\n📥 Found {len(tasks)} pending task(s)")
                    for task in tasks:
                        self.process_task(task)
                else:
                    now = datetime.now().strftime('%H:%M:%S')
                    print(f"[{now}] No pending tasks. Waiting {POLL_INTERVAL}s...", end='\r')
                
            except KeyboardInterrupt:
                print("\n\nShutting down worker...")
                break
            except Exception as e:
                print(f"\nError in main loop: {e}")
            
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    worker = LocalWorker()
    worker.run()
