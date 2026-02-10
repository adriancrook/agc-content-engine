"""
MediaAgent for v2 - Image generation using Google Imagen 3
Generates blog header images via Vertex AI Imagen API
"""

import base64
import json
import logging
import time
from typing import Dict

import requests

from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class MediaAgent(BaseAgent):
    """
    Media agent using Google Imagen 3 via Vertex AI
    Generates featured images for articles
    """

    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.google_api_key = config.get("google_api_key") if config else None

        if not self.google_api_key:
            raise ValueError("Google API key required for media agent")

    async def run(self, article) -> AgentResult:
        """
        Generate media for article (featured image)
        """
        start_time = time.time()

        title = article.title
        final_content = article.final_content or article.draft

        if not final_content:
            return AgentResult(
                success=False,
                data={},
                error="No content found for media generation"
            )

        logger.info(f"Generating media for: {title}")

        try:
            # Generate image prompt from article
            image_prompt = self._create_image_prompt(title, final_content)
            logger.info(f"Image prompt: {image_prompt[:100]}...")

            # Generate image with Imagen 3
            logger.info("Calling Imagen 3 API...")
            image_url, image_data = self._generate_image(image_prompt)

            if not image_url and not image_data:
                logger.warning("Image generation returned no result, using placeholder")
                media_data = {
                    "featured_image_prompt": image_prompt,
                    "featured_image_url": None,
                    "featured_image_base64": None,
                    "image_alt_text": f"Featured image for {title}",
                }
            else:
                logger.info(f"✓ Image generated successfully")
                media_data = {
                    "featured_image_prompt": image_prompt,
                    "featured_image_url": image_url,
                    "featured_image_base64": image_data if not image_url else None,
                    "image_alt_text": f"Professional blog header image for article: {title}",
                }

            duration = time.time() - start_time

            return AgentResult(
                success=True,
                data={"media": media_data},
                cost=0.04,  # Imagen 3 cost per image
                tokens=0,
                error=None
            )

        except Exception as e:
            logger.error(f"Media generation failed: {e}")
            # Return success with no image rather than failing the entire pipeline
            return AgentResult(
                success=True,
                data={"media": {
                    "featured_image_prompt": image_prompt if 'image_prompt' in locals() else None,
                    "featured_image_url": None,
                    "image_alt_text": f"Featured image for {title}",
                }},
                cost=0.0,
                tokens=0,
                error=f"Image generation failed: {str(e)}"
            )

    def _create_image_prompt(self, title: str, content: str) -> str:
        """Create optimized image generation prompt from article"""

        # Extract key concepts from first paragraph
        paragraphs = [p for p in content.split('\n\n') if p and not p.startswith('#')]
        first_para = paragraphs[0] if paragraphs else title

        # Create detailed Imagen-optimized prompt
        prompt = f"""Professional blog header image for article: "{title}"

Context: {first_para[:200]}

Style requirements:
- Modern, clean, professional design
- 16:9 landscape format (1920x1080)
- Vibrant colors with good contrast
- Abstract technology/business imagery
- No text or words in the image
- Eye-catching and click-worthy
- Suitable for a professional blog

Visual theme: Technology, gaming, business, and innovation"""

        return prompt

    def _generate_image(self, prompt: str) -> tuple:
        """
        Generate image using Google Imagen 3 via Vertex AI

        Returns:
            tuple: (image_url, image_base64_data)
        """
        # Imagen 3 is accessed via Vertex AI generativelanguage API
        # Using the simpler REST API with API key
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={self.google_api_key}"

        payload = {
            "instances": [{
                "prompt": prompt
            }],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "16:9",
                "safetyFilterLevel": "block_some",
                "personGeneration": "allow_adult",
            }
        }

        headers = {
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()

            # Extract image data from response
            if "predictions" in result and len(result["predictions"]) > 0:
                prediction = result["predictions"][0]

                # Imagen returns base64 encoded image
                if "bytesBase64Encoded" in prediction:
                    image_data = prediction["bytesBase64Encoded"]
                    logger.info(f"Received base64 image data ({len(image_data)} chars)")
                    return (None, image_data)

                # Or a URL
                elif "imageUrl" in prediction:
                    image_url = prediction["imageUrl"]
                    logger.info(f"Received image URL: {image_url[:50]}...")
                    return (image_url, None)

            logger.warning("No image data in Imagen response")
            return (None, None)

        except requests.exceptions.HTTPError as e:
            logger.error(f"Imagen API HTTP error: {e}")
            logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'no response'}")
            raise
        except Exception as e:
            logger.error(f"Imagen API call failed: {e}")
            raise
