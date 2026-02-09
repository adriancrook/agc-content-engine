"""
Test the complete v2 pipeline
Creates a topic and article, watches it progress through all stages
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def create_topic():
    """Create a test topic"""
    topic = {
        "title": "The Future of AI Agents in Software Development",
        "keyword": "AI agents software development"
    }

    response = requests.post(f"{BASE_URL}/topics", json=topic)
    response.raise_for_status()
    return response.json()["id"]

def approve_topic(topic_id):
    """Approve topic and create article"""
    response = requests.post(f"{BASE_URL}/topics/{topic_id}/approve")
    response.raise_for_status()
    return response.json()["article_id"]

def get_article(article_id):
    """Get article details"""
    response = requests.get(f"{BASE_URL}/articles/{article_id}")
    response.raise_for_status()
    return response.json()

def watch_progress(article_id):
    """Watch article progress through pipeline"""
    print(f"\n🎯 Watching article {article_id[:8]}...\n")

    last_state = None
    while True:
        article = get_article(article_id)
        current_state = article["state"]

        # Print state changes
        if current_state != last_state:
            print(f"[{time.strftime('%H:%M:%S')}] {current_state.upper()}")

            # Print progress details
            if current_state == "researching" and article.get("research"):
                sources = len(article["research"].get("sources", []))
                print(f"  → Found {sources} sources")

            elif current_state == "writing" and article.get("draft"):
                words = len(article["draft"].split())
                print(f"  → Generated {words} words")

            elif current_state == "fact_checking" and article.get("fact_check"):
                accuracy = article["fact_check"].get("accuracy_score", 0)
                print(f"  → Accuracy: {accuracy:.0%}")

            elif current_state == "seo_optimizing" and article.get("seo"):
                score = article["seo"].get("seo_score", 0)
                print(f"  → SEO Score: {score}/100")

            elif current_state == "humanizing" and article.get("final_content"):
                words = len(article["final_content"].split())
                print(f"  → Humanized {words} words")

            elif current_state == "media_generating" and article.get("media"):
                print(f"  → Image prompt ready")

            last_state = current_state

        # Exit conditions
        if current_state in ["ready", "published", "failed"]:
            print(f"\n{'✅' if current_state == 'ready' else '❌'} Final state: {current_state}")

            if current_state == "failed":
                print(f"Error: {article.get('error_message')}")
            else:
                # Print final stats
                print("\n📊 Final Stats:")
                print(f"  Words: {len(article.get('final_content', '').split())}")
                print(f"  Sources: {len(article.get('research', {}).get('sources', []))}")
                print(f"  Accuracy: {article.get('fact_check', {}).get('accuracy_score', 0):.0%}")
                print(f"  SEO Score: {article.get('seo', {}).get('seo_score', 0)}/100")

                # Save content to file
                filename = f"article_{article_id[:8]}.md"
                with open(filename, "w") as f:
                    f.write(article.get("final_content", ""))
                print(f"\n💾 Content saved to: {filename}")

            break

        time.sleep(3)

if __name__ == "__main__":
    print("🚀 AGC v2 Pipeline Test")
    print("=" * 50)

    try:
        # Create topic
        print("\n📝 Creating topic...")
        topic_id = create_topic()
        print(f"✓ Topic created: {topic_id[:8]}")

        # Approve topic (creates article)
        print("\n✅ Approving topic...")
        article_id = approve_topic(topic_id)
        print(f"✓ Article created: {article_id[:8]}")

        # Watch progress
        watch_progress(article_id)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
