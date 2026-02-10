"""
MediaAgent for v2 - Header image generation using Google Gemini
Generates contextual header images for articles via Google Gemini API
"""

import base64
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class MediaAgent(BaseAgent):
    """
    Media agent using Google Gemini API
    Generates header images for articles using Gemini 2.5 Flash Image
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.google_api_key = config.get("google_api_key") if config else None
        self.model = "gemini-2.5-flash-image"  # Google's image generation model
        self.output_dir = config.get("output_dir", "generated_images")

        if not self.google_api_key:
            raise ValueError("Google API key required for media agent")

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    async def run(self, article) -> AgentResult:
        """
        Generate header image for article
        """
        start_time = time.time()

        title = article.title
        draft = article.draft
        research = article.research

        if not title:
            return AgentResult(
                success=False,
                data={},
                error="No title provided for image generation"
            )

        logger.info(f"Generating header image for: {title}")

        try:
            # Generate detailed image prompt from article context
            image_prompt = self._generate_image_prompt(title, draft, research)

            logger.info(f"Image prompt: {image_prompt[:200]}...")

            # Generate image via OpenRouter
            image_data = self._generate_image(image_prompt)

            # Save image to disk
            image_path = self._save_image(image_data, title)

            logger.info(f"Header image saved to: {image_path}")

            # Estimate cost (Gemini 2.0 Flash is free tier, but track for monitoring)
            cost = 0.0  # Free tier

            return AgentResult(
                success=True,
                data={
                    "header_image_path": image_path,
                    "image_prompt": image_prompt,
                    "image_url": f"file://{os.path.abspath(image_path)}"
                },
                cost=cost,
                tokens=0,
                error=None
            )

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error=str(e)
            )

    def _generate_image_prompt(self, title: str, draft: str = None, research: Dict = None) -> str:
        """
        Generate a detailed image prompt from article context
        """
        # Extract key themes from title and draft
        themes = []

        # Common mobile gaming themes
        if any(word in title.lower() for word in ["monetization", "revenue", "iap", "ads"]):
            themes.append("mobile game monetization and revenue charts")
        if any(word in title.lower() for word in ["retention", "engagement", "churn"]):
            themes.append("player engagement and retention metrics")
        if any(word in title.lower() for word in ["onboarding", "ftue", "tutorial"]):
            themes.append("mobile game onboarding and user interface")
        if any(word in title.lower() for word in ["analytics", "data", "metrics", "kpi"]):
            themes.append("analytics dashboards and data visualization")
        if any(word in title.lower() for word in ["design", "gameplay", "mechanics"]):
            themes.append("mobile game design and gameplay")
        if any(word in title.lower() for word in ["user acquisition", "marketing", "ua"]):
            themes.append("user acquisition and marketing")

        # Default to generic mobile gaming if no themes found
        if not themes:
            themes.append("mobile gaming industry")

        # Build comprehensive prompt
        prompt = f"""Create a professional header image for an article titled: "{title}"

The image should:
- Be abstract and modern, suitable for a mobile gaming industry blog
- Use a clean, professional color palette (blues, purples, oranges, gradients)
- Include visual elements related to: {', '.join(themes)}
- Be 16:9 aspect ratio (1200x675px ideal)
- Have a subtle gradient or geometric background
- NO TEXT or words in the image
- NO logos or branding
- Focus on abstract shapes, icons, or symbolic representations

Style: Modern, clean, professional blog header
Mood: Authoritative, data-driven, engaging
Composition: Centered focal point with breathing room for text overlay"""

        return prompt

    def _generate_image(self, prompt: str) -> bytes:
        """
        Generate image using Google Gemini API
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.google_api_key,
        }

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
            # Note: Gemini image generation models return images by default
            # No need to specify responseMimeType
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()

            # Extract image from response
            # Gemini returns image in candidates[0].content.parts[0].inlineData
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate:
                    parts = candidate["content"].get("parts", [])
                    for part in parts:
                        if "inlineData" in part:
                            # Decode base64 image data
                            mime_type = part["inlineData"].get("mimeType", "")
                            image_data = part["inlineData"].get("data", "")

                            if image_data:
                                logger.info(f"Received {mime_type} image data")
                                return base64.b64decode(image_data)

            logger.error(f"Unexpected response format: {json.dumps(data, indent=2)[:500]}")
            raise ValueError("No image data found in Gemini response")

        except requests.exceptions.HTTPError as e:
            logger.error(f"Gemini API HTTP error: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response: {e.response.text[:500]}")
            raise
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    def _save_image(self, image_data: bytes, title: str) -> str:
        """
        Save image to disk with sanitized filename
        """
        # Sanitize filename from title
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = filename.replace(' ', '_').lower()[:50]  # Limit length

        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename}_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(image_data)

        return filepath
