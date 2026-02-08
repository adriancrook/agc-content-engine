#!/usr/bin/env python3
"""
AGC Content Engine Pipeline

Main orchestrator that runs the full content generation pipeline.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from agents import (
    AgentInput,
    ResearchAgent,
    WriterAgent,
    FactCheckerAgent,
    SEOAgent,
    MediaAgent,
    HumanizerAgent,
    SupervisorAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Orchestrates the full content generation pipeline.
    
    Pipeline stages:
    1. Research - Gather sources and create outline
    2. Write - Generate initial draft
    3. Fact Check - Verify claims
    4. SEO - Optimize for search
    5. Media - Add images and videos
    6. Humanize - Make AI-undetectable
    7. Supervise - Final QA
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        output_dir: str = "outputs",
    ):
        self.config = self._load_config(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize agents
        self._init_agents()
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration."""
        default_config = {
            "ollama_url": "http://localhost:11434",
            "brave_api_key": os.getenv("BRAVE_API_KEY", ""),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
            "models": {
                "research": "qwen2.5:14b",
                "writer": "qwen2.5:14b",
                "fact_checker": "qwen2.5:14b",  # Use same model if deepseek not available
                "seo": "qwen2.5:14b",
                "humanizer": "claude-sonnet-4-20250514",
                "supervisor": "claude-opus-4-20250514",
            },
            "target_word_count": 2500,
            "max_sources": 20,
            "author_voice": "knowledgeable but approachable tech writer who explains complex topics clearly",
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        # Load API keys from files if not in env
        credentials_dir = Path.home() / ".credentials"
        
        if not default_config["brave_api_key"]:
            brave_file = credentials_dir / "brave-api.txt"
            if brave_file.exists():
                default_config["brave_api_key"] = brave_file.read_text().strip()
        
        if not default_config["anthropic_api_key"]:
            anthropic_file = credentials_dir / "anthropic.txt"
            if anthropic_file.exists():
                default_config["anthropic_api_key"] = anthropic_file.read_text().strip()
        
        return default_config
    
    def _init_agents(self):
        """Initialize all agents."""
        
        self.research_agent = ResearchAgent(
            brave_api_key=self.config["brave_api_key"],
            ollama_url=self.config["ollama_url"],
            model=self.config["models"]["research"],
        )
        
        self.writer_agent = WriterAgent(
            ollama_url=self.config["ollama_url"],
            model=self.config["models"]["writer"],
        )
        
        self.fact_checker_agent = FactCheckerAgent(
            ollama_url=self.config["ollama_url"],
            model=self.config["models"]["fact_checker"],
        )
        
        self.seo_agent = SEOAgent(
            ollama_url=self.config["ollama_url"],
            model=self.config["models"]["seo"],
        )
        
        self.media_agent = MediaAgent(
            google_api_key=self.config.get("google_api_key"),
        )
        
        self.humanizer_agent = HumanizerAgent(
            api_key=self.config["anthropic_api_key"],
            model=self.config["models"]["humanizer"],
        )
        
        self.supervisor_agent = SupervisorAgent(
            api_key=self.config["anthropic_api_key"],
            model=self.config["models"]["supervisor"],
        )
        
        logger.info("All agents initialized")
    
    def run(
        self,
        topic: str,
        keywords: List[str] = None,
        primary_keyword: Optional[str] = None,
        existing_articles: List[Dict] = None,
    ) -> Dict:
        """
        Run the full pipeline for a topic.
        
        Args:
            topic: Main article topic
            keywords: Related keywords for research
            primary_keyword: Main SEO keyword (defaults to topic)
            existing_articles: List of existing blog articles for internal linking
        
        Returns:
            Dict with final article and all stage outputs
        """
        start_time = datetime.now()
        
        # Create workspace for this run
        workspace = self.output_dir / start_time.strftime("%Y%m%d_%H%M%S")
        workspace.mkdir(exist_ok=True)
        
        logger.info(f"Starting pipeline for: {topic}")
        logger.info(f"Workspace: {workspace}")
        
        keywords = keywords or []
        primary_keyword = primary_keyword or topic
        existing_articles = existing_articles or []
        
        all_outputs = []
        
        try:
            # Stage 1: Research
            logger.info("=== Stage 1: Research ===")
            research_output = self._run_stage(
                agent=self.research_agent,
                input_data={
                    "topic": topic,
                    "keywords": keywords,
                    "max_sources": self.config.get("max_sources", 20),
                },
                workspace=workspace,
                stage=1,
            )
            all_outputs.append(research_output.data)
            
            if not research_output.success:
                return self._failure_result("Research failed", all_outputs, workspace)
            
            # Stage 2: Write
            logger.info("=== Stage 2: Write ===")
            writer_output = self._run_stage(
                agent=self.writer_agent,
                input_data={
                    "research": research_output.data,
                    "tone": self.config.get("author_voice", "informative"),
                    "target_word_count": self.config.get("target_word_count", 2500),
                },
                workspace=workspace,
                stage=2,
            )
            all_outputs.append(writer_output.data)
            
            if not writer_output.success:
                return self._failure_result("Writing failed", all_outputs, workspace)
            
            article = writer_output.data.get("article_markdown", "")
            
            # Stage 3: Fact Check
            logger.info("=== Stage 3: Fact Check ===")
            fact_output = self._run_stage(
                agent=self.fact_checker_agent,
                input_data={
                    "article": article,
                    "sources": research_output.data.get("sources", []),
                },
                workspace=workspace,
                stage=3,
            )
            all_outputs.append(fact_output.data)
            
            # Use corrected article if available
            if fact_output.data.get("corrected_article"):
                article = fact_output.data["corrected_article"]
            
            # Stage 4: SEO
            logger.info("=== Stage 4: SEO ===")
            seo_output = self._run_stage(
                agent=self.seo_agent,
                input_data={
                    "article": article,
                    "primary_keyword": primary_keyword,
                    "secondary_keywords": keywords,
                    "existing_articles": existing_articles,
                },
                workspace=workspace,
                stage=4,
            )
            all_outputs.append(seo_output.data)
            
            # Use SEO-optimized article
            article = seo_output.data.get("optimized_article", article)
            meta_description = seo_output.data.get("meta_description", "")
            
            # Stage 5: Media
            logger.info("=== Stage 5: Media ===")
            media_output = self._run_stage(
                agent=self.media_agent,
                input_data={
                    "article": article,
                    "title": writer_output.data.get("title", topic),
                    "primary_keyword": primary_keyword,
                },
                workspace=workspace,
                stage=5,
            )
            all_outputs.append(media_output.data)
            
            # Use article with media
            if media_output.data.get("article_with_media"):
                article = media_output.data["article_with_media"]
            
            # Stage 6: Humanize
            logger.info("=== Stage 6: Humanize ===")
            humanize_output = self._run_stage(
                agent=self.humanizer_agent,
                input_data={
                    "article": article,
                    "author_voice": self.config.get("author_voice", ""),
                    "intensity": "medium",
                },
                workspace=workspace,
                stage=6,
            )
            all_outputs.append(humanize_output.data)
            
            # Use humanized article
            article = humanize_output.data.get("humanized_article", article)
            
            # Stage 7: Supervisor QA
            logger.info("=== Stage 7: Supervisor QA ===")
            supervisor_output = self._run_stage(
                agent=self.supervisor_agent,
                input_data={
                    "final_article": article,
                    "research_data": research_output.data,
                    "all_outputs": [{"cost_usd": o.cost_usd, "duration_seconds": o.duration_seconds} 
                                   for o in [research_output, writer_output, fact_output, 
                                           seo_output, media_output, humanize_output]],
                },
                workspace=workspace,
                stage=7,
            )
            all_outputs.append(supervisor_output.data)
            
            # Calculate totals
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Save final article
            final_path = workspace / "FINAL_ARTICLE.md"
            with open(final_path, "w") as f:
                f.write(article)
            
            # Save metadata
            metadata = {
                "topic": topic,
                "primary_keyword": primary_keyword,
                "keywords": keywords,
                "meta_description": meta_description,
                "word_count": len(article.split()),
                "approved": supervisor_output.data.get("approved_for_publishing", False),
                "overall_score": supervisor_output.data.get("overall_score", 0),
                "duration_seconds": duration,
                "workspace": str(workspace),
                "timestamp": end_time.isoformat(),
            }
            
            meta_path = workspace / "metadata.json"
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Pipeline complete! Score: {metadata['overall_score']}")
            logger.info(f"Final article: {final_path}")
            
            return {
                "success": True,
                "article": article,
                "metadata": metadata,
                "workspace": str(workspace),
                "all_outputs": all_outputs,
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return self._failure_result(str(e), all_outputs, workspace)
    
    def _run_stage(
        self,
        agent,
        input_data: Dict,
        workspace: Path,
        stage: int,
    ):
        """Run a single pipeline stage."""
        agent_input = AgentInput(
            data=input_data,
            workspace=workspace,
            config=self.config,
        )
        
        output = agent.run(agent_input)
        
        # Save stage output
        agent.save_output(output, workspace, stage)
        
        logger.info(f"Stage {stage} ({agent.name}): {'SUCCESS' if output.success else 'FAILED'}")
        if output.errors:
            for error in output.errors:
                logger.warning(f"  - {error}")
        
        return output
    
    def _failure_result(self, error: str, outputs: List, workspace: Path) -> Dict:
        """Generate failure result."""
        return {
            "success": False,
            "error": error,
            "workspace": str(workspace),
            "all_outputs": outputs,
        }


def main():
    parser = argparse.ArgumentParser(description="AGC Content Engine Pipeline")
    parser.add_argument("topic", help="Article topic")
    parser.add_argument("--keywords", "-k", nargs="+", help="Related keywords")
    parser.add_argument("--primary-keyword", "-p", help="Primary SEO keyword")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output-dir", "-o", default="outputs", help="Output directory")
    
    args = parser.parse_args()
    
    pipeline = ContentPipeline(
        config_path=args.config,
        output_dir=args.output_dir,
    )
    
    result = pipeline.run(
        topic=args.topic,
        keywords=args.keywords or [],
        primary_keyword=args.primary_keyword,
    )
    
    if result["success"]:
        print(f"\n✅ Article generated successfully!")
        print(f"   Score: {result['metadata']['overall_score']}/100")
        print(f"   Words: {result['metadata']['word_count']}")
        print(f"   Output: {result['workspace']}")
    else:
        print(f"\n❌ Pipeline failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
