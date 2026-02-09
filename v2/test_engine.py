#!/usr/bin/env python3
"""
Test script to demo the state machine engine
Creates a test article and watches it flow through the pipeline
"""

import time
import requests
import sys

BASE_URL = "http://localhost:8000"


def print_status(status):
    """Pretty print status"""
    print("\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)

    print("\n📊 Articles by State:")
    for state, count in status["articles"].items():
        print(f"  {state:20s}: {count}")

    print("\n🤖 Agent Status:")
    for agent, state in status["agents"].items():
        emoji = "🔴" if state == "working" else "⚪"
        print(f"  {emoji} {agent:20s}: {state}")

    print(f"\n📝 Total Articles: {status['total']}")
    print("="*60)


def main():
    print("🧪 AGC v2 State Machine Test")
    print("="*60)

    # 1. Create a topic
    print("\n1️⃣  Creating test topic...")
    response = requests.post(f"{BASE_URL}/topics", json={
        "title": "How to Build a State Machine in Python",
        "keyword": "python-state-machine"
    })
    topic = response.json()
    print(f"✓ Topic created: {topic['id'][:8]}... - {topic['title']}")

    # 2. Approve topic (creates article in 'pending' state)
    print("\n2️⃣  Approving topic (creates article)...")
    response = requests.post(f"{BASE_URL}/topics/{topic['id']}/approve")
    article = response.json()
    print(f"✓ Article created: {article['article_id'][:8]}... - State: {article['state']}")

    # 3. Watch it progress through pipeline
    print("\n3️⃣  Watching article progress through pipeline...")
    print("   (State machine runs every 5 seconds)")
    print("   (Each agent takes ~1 second to process)")

    article_id = article['article_id']
    last_state = None

    for i in range(60):  # Watch for up to 60 seconds
        time.sleep(1)

        # Get current article state
        response = requests.get(f"{BASE_URL}/articles/{article_id}")
        article_data = response.json()
        current_state = article_data['state']

        # Print state changes
        if current_state != last_state:
            print(f"\n   [{i:2d}s] State: {current_state}")
            if article_data.get('research'):
                print(f"        ✓ Research completed")
            if article_data.get('draft'):
                print(f"        ✓ Draft written ({len(article_data['draft'])} chars)")
            if article_data.get('fact_check'):
                print(f"        ✓ Fact checked")
            if article_data.get('seo'):
                print(f"        ✓ SEO optimized")
            if article_data.get('final_content'):
                print(f"        ✓ Humanized ({len(article_data['final_content'])} chars)")
            if article_data.get('media'):
                print(f"        ✓ Media generated")

            last_state = current_state

        # Check if done
        if current_state in ['ready', 'published', 'failed']:
            print(f"\n✅ Article reached terminal state: {current_state}")
            break
    else:
        print("\n⏰ Timeout reached")

    # 4. Show final status
    print("\n4️⃣  Final System Status:")
    response = requests.get(f"{BASE_URL}/status")
    print_status(response.json())

    print("\n✅ Test complete!")
    print(f"\n🔗 View article: {BASE_URL}/articles/{article_id}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(0)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server")
        print(f"   Make sure the server is running: python server.py")
        sys.exit(1)
