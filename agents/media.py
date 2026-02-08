"""
Media Agent - Generates header images and finds YouTube embeds.

Model: Gemini 3 Pro Image (via nano-banana-pro) + YouTube API
"""

import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

from .base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class MediaAgent(BaseAgent):
    """
    Media agent that generates images and finds videos.
    
    Uses Gemini 3 Pro Image for header images.
    """
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        youtube_api_key: Optional[str] = None,
        nano_banana_path: str = "/Users/kitwren/clawd/skills/nano-banana-pro",
    ):
        # Media agent doesn't use base LLM, but we need the structure
        super().__init__(
            name="media",
            model="gemini-3-pro-image",
            model_type="google",
        )
        self.google_api_key = google_api_key
        self.youtube_api_key = youtube_api_key
        self.nano_banana_path = Path(nano_banana_path)
    
    def run(self, input: AgentInput) -> AgentOutput:
        """
        Generate media for an article.
        
        Input data:
            - article: str - The article markdown
            - title: str - Article title
            - primary_keyword: str - Main keyword
            - workspace: Path - Where to save images
        """
        start_time = time.time()
        errors = []
        
        article = input.data.get("article", "")
        title = input.data.get("title", "")
        primary_keyword = input.data.get("primary_keyword", "")
        
        workspace = input.workspace / "media"
        workspace.mkdir(exist_ok=True)
        
        logger.info(f"Generating media for: {title}")
        
        # Step 1: Generate header image
        header_image_path = self._generate_header_image(
            title=title,
            keyword=primary_keyword,
            workspace=workspace,
        )
        
        if not header_image_path:
            errors.append("Failed to generate header image")
        
        # Step 2: Find relevant YouTube videos
        youtube_embeds = self._find_youtube_videos(
            topic=title,
            keyword=primary_keyword,
            max_results=3,
        )
        
        if not youtube_embeds:
            errors.append("No relevant YouTube videos found")
        
        # Step 3: Determine where to place media in article
        media_placements = self._suggest_placements(article, youtube_embeds)
        
        # Step 4: Generate article with media embedded
        article_with_media = self._embed_media(
            article=article,
            header_image=header_image_path,
            youtube_embeds=youtube_embeds,
            placements=media_placements,
        )
        
        duration = time.time() - start_time
        
        output_data = {
            "article_with_media": article_with_media,
            "header_image": str(header_image_path) if header_image_path else None,
            "youtube_embeds": youtube_embeds,
            "media_placements": media_placements,
        }
        
        success = header_image_path is not None
        
        return AgentOutput(
            data=output_data,
            success=success,
            errors=errors,
            duration_seconds=duration,
        )
    
    def validate_output(self, output: AgentOutput) -> bool:
        """Check if media generation meets quality gate."""
        data = output.data
        
        # Must have header image
        if not data.get("header_image"):
            return False
        
        return True
    
    def _generate_header_image(
        self,
        title: str,
        keyword: str,
        workspace: Path,
    ) -> Optional[Path]:
        """Generate header image using nano-banana-pro."""
        
        # Create image prompt
        prompt = f"""Professional blog header image for article: "{title}"
        
Style: Modern, clean, digital illustration
Theme: {keyword}
Colors: Vibrant but professional
Aspect: 16:9 landscape
No text or watermarks"""

        output_path = workspace / "header.png"
        
        # Try using nano-banana-pro CLI if available
        script_path = self.nano_banana_path / "generate.sh"
        
        if script_path.exists():
            try:
                result = subprocess.run(
                    [str(script_path), prompt, str(output_path)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                
                if result.returncode == 0 and output_path.exists():
                    logger.info(f"Generated header image: {output_path}")
                    return output_path
                else:
                    logger.warning(f"nano-banana-pro failed: {result.stderr}")
            
            except Exception as e:
                logger.warning(f"nano-banana-pro error: {e}")
        
        # Fallback: try direct Gemini API
        if self.google_api_key:
            try:
                return self._generate_via_gemini(prompt, output_path)
            except Exception as e:
                logger.error(f"Gemini image gen failed: {e}")
        
        return None
    
    def _generate_via_gemini(self, prompt: str, output_path: Path) -> Optional[Path]:
        """Generate image via Gemini API directly."""
        # This would require the Google GenAI SDK
        # For now, return None and log
        logger.warning("Direct Gemini API not implemented - use nano-banana-pro skill")
        return None
    
    def _find_youtube_videos(
        self,
        topic: str,
        keyword: str,
        max_results: int = 3,
    ) -> List[Dict]:
        """Find relevant YouTube videos via API or search."""
        videos = []
        
        # Try YouTube API if available
        if self.youtube_api_key:
            try:
                videos = self._search_youtube_api(
                    query=f"{keyword} {topic}",
                    max_results=max_results,
                )
            except Exception as e:
                logger.warning(f"YouTube API failed: {e}")
        
        # Fallback: use web search
        if not videos:
            videos = self._search_youtube_web(
                query=f"{keyword} {topic}",
                max_results=max_results,
            )
        
        return videos
    
    def _search_youtube_api(self, query: str, max_results: int) -> List[Dict]:
        """Search YouTube using API."""
        url = "https://www.googleapis.com/youtube/v3/search"
        
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": self.youtube_api_key,
            "videoDuration": "medium",  # 4-20 minutes
            "order": "relevance",
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            
            videos.append({
                "id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:200],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            })
        
        return videos
    
    def _search_youtube_web(self, query: str, max_results: int) -> List[Dict]:
        """Fallback: find videos via web search patterns."""
        # This would search for YouTube URLs in web search results
        # For MVP, return empty and log
        logger.warning("YouTube web search fallback not implemented")
        return []
    
    def _suggest_placements(
        self,
        article: str,
        youtube_embeds: List[Dict],
    ) -> List[Dict]:
        """Suggest where to place media in article."""
        placements = []
        
        # Header image goes at top
        placements.append({
            "type": "header_image",
            "position": "after_title",
            "section": None,
        })
        
        # Find H2 sections
        h2_matches = list(re.finditer(r'^## (.+)$', article, re.MULTILINE))
        
        # Place YouTube videos after relevant H2 sections
        for i, video in enumerate(youtube_embeds[:2]):  # Max 2 videos
            if i < len(h2_matches):
                placements.append({
                    "type": "youtube",
                    "position": "after_section",
                    "section": h2_matches[i].group(1),
                    "video_id": video.get("id"),
                })
        
        return placements
    
    def _embed_media(
        self,
        article: str,
        header_image: Optional[Path],
        youtube_embeds: List[Dict],
        placements: List[Dict],
    ) -> str:
        """Embed media into article markdown."""
        lines = article.split('\n')
        result_lines = []
        
        title_found = False
        current_h2 = None
        video_index = 0
        
        for line in lines:
            result_lines.append(line)
            
            # Add header image after title
            if line.startswith('# ') and not title_found:
                title_found = True
                if header_image:
                    result_lines.append("")
                    result_lines.append(f"![Header Image]({header_image})")
                    result_lines.append("")
            
            # Track H2 sections for video placement
            if line.startswith('## '):
                current_h2 = line[3:].strip()
            
            # Add YouTube after certain sections
            if current_h2 and line == "" and video_index < len(youtube_embeds):
                # Check if this is a good place for a video
                for placement in placements:
                    if (placement.get("type") == "youtube" and 
                        placement.get("section") == current_h2 and
                        placement.get("video_id") == youtube_embeds[video_index].get("id")):
                        
                        video = youtube_embeds[video_index]
                        result_lines.append("")
                        result_lines.append(f"### Related Video")
                        result_lines.append("")
                        result_lines.append(f"<iframe width=\"560\" height=\"315\" ")
                        result_lines.append(f"src=\"{video.get('embed_url')}\" ")
                        result_lines.append(f"title=\"{video.get('title', '')}\" ")
                        result_lines.append(f"frameborder=\"0\" allowfullscreen></iframe>")
                        result_lines.append("")
                        
                        video_index += 1
                        current_h2 = None  # Reset to avoid double-adding
                        break
        
        return '\n'.join(result_lines)
