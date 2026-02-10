"""
Simple test to verify Key Takeaways and FAQ generation formats
"""

import asyncio
import os
from agents.writer import WriterAgent

async def test_simple():
    config = {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
    }

    writer = WriterAgent(config)

    # Mock data
    topic = "Mobile Gaming Monetization"
    outline = {
        "title": "Mobile Gaming Monetization Strategies 2025",
        "sections": [
            {"h2": "IAP Strategies"},
            {"h2": "Ad Monetization"},
            {"h2": "Hybrid Models"}
        ]
    }
    sources = [
        {
            "title": "Gaming Revenue Report",
            "url": "https://example.com/report",
            "key_stats": ["Market worth $180B", "IAP = 72% of revenue"]
        }
    ]

    print("=" * 60)
    print("Generating Key Takeaways...")
    print("=" * 60)
    kt = writer._generate_key_takeaways(topic, outline, sources)
    print(kt)
    print()

    print("=" * 60)
    print("Generating FAQ...")
    print("=" * 60)
    faq = writer._generate_faq(topic, outline, sources)
    print(faq)

if __name__ == "__main__":
    asyncio.run(test_simple())
