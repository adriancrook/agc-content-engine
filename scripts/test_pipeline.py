#!/usr/bin/env python3
"""
Quick test of the content pipeline.
"""

import sys
sys.path.insert(0, '..')

from pipeline import ContentPipeline


def main():
    print("🚀 Testing AGC Content Engine Pipeline")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = ContentPipeline(
        config_path="../.config/default.json",
        output_dir="../outputs",
    )
    
    # Test topic from SEObot queue
    topic = "Best Free-to-Play Mobile Games 2025"
    keywords = ["f2p games", "mobile gaming", "gacha games", "free mobile games"]
    
    print(f"\nTopic: {topic}")
    print(f"Keywords: {', '.join(keywords)}")
    print("\nStarting pipeline...")
    print("-" * 50)
    
    result = pipeline.run(
        topic=topic,
        keywords=keywords,
        primary_keyword="free-to-play mobile games",
    )
    
    print("\n" + "=" * 50)
    if result["success"]:
        print("✅ SUCCESS!")
        print(f"   Score: {result['metadata']['overall_score']}/100")
        print(f"   Words: {result['metadata']['word_count']}")
        print(f"   Approved: {result['metadata']['approved']}")
        print(f"   Output: {result['workspace']}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown')}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
