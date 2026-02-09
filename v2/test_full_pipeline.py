"""
Test the full pipeline end-to-end
Creates an article and monitors it through all states
"""

import asyncio
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_full_pipeline():
    print("\n" + "="*70)
    print("TESTING FULL PIPELINE END-TO-END")
    print("="*70)
    
    # Create a test topic
    topic_data = {
        "title": "Why Mobile RPG Retention Drops After Day 7 (And How to Fix It)",
        "format": "conceptual_deepdive"
    }
    
    print(f"\n📝 Creating topic: {topic_data['title']}")
    print(f"   Format: {topic_data['format']}")
    
    try:
        # Step 1: Create topic
        response = requests.post(f"{BASE_URL}/topics", json=topic_data, timeout=10)
        response.raise_for_status()
        data = response.json()
        topic_id = data["id"]
        print(f"✅ Topic created: {topic_id}")

        # Step 2: Approve topic to create article
        response = requests.post(f"{BASE_URL}/topics/{topic_id}/approve", timeout=10)
        response.raise_for_status()
        data = response.json()
        article_id = data["article_id"]
        print(f"✅ Article created: {article_id}")
    except Exception as e:
        print(f"❌ Failed to create article: {e}")
        print("\n💡 Make sure the server is running:")
        print("   cd v2")
        print("   export USE_REAL_AGENTS=true")
        print("   export OPENROUTER_API_KEY=your_key")
        print("   export BRAVE_API_KEY=your_key")
        print("   python server.py")
        return
    
    # Monitor progress
    print(f"\n📊 Monitoring article progress...")
    print("-" * 70)
    
    last_state = None
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/articles/{article_id}", timeout=60)
            response.raise_for_status()
            article = response.json()

            current_state = article["state"]

            if current_state != last_state:
                elapsed = time.time() - start_time
                print(f"[{elapsed:>6.1f}s] {current_state}")
                last_state = current_state

            # Check if complete or failed
            if current_state == "ready":
                print("\n" + "="*70)
                print("✅ PIPELINE COMPLETE!")
                print("="*70)

                # Show results
                print(f"\nArticle: {article['title']}")
                print(f"State: {article['state']}")

                if article.get('draft'):
                    print(f"Draft: {len(article['draft'].split())} words")

                if article.get('enrichment'):
                    enr = article['enrichment']
                    print(f"\nEnrichment:")
                    print(f"  Citations: {len(enr.get('citations', []))}")
                    print(f"  Metrics: {len(enr.get('metrics', []))}")
                    print(f"  Testimonials: {len(enr.get('testimonials', []))}")

                if article.get('revised_draft'):
                    print(f"\nRevised Draft: {len(article['revised_draft'].split())} words")
                    word_change = len(article['revised_draft'].split()) - len(article.get('draft', '').split())
                    print(f"Change: +{word_change} words")

                if article.get('final_content'):
                    print(f"\nFinal Content: {len(article['final_content'].split())} words")

                    # Save final article
                    output_file = Path(__file__).parent / "test_outputs" / f"full_pipeline_{article_id[:8]}.md"
                    output_file.parent.mkdir(exist_ok=True)
                    with open(output_file, 'w') as f:
                        f.write(article['final_content'])
                    print(f"\n📄 Final article saved to: {output_file}")

                break

            elif current_state == "failed":
                print("\n" + "="*70)
                print("❌ PIPELINE FAILED")
                print("="*70)
                print(f"Error: {article.get('error', 'Unknown error')}")
                break

            # Wait before checking again
            await asyncio.sleep(5)

        except requests.exceptions.Timeout:
            # Continue monitoring even if request times out
            print(".", end="", flush=True)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"\n❌ Error checking status: {e}")
            await asyncio.sleep(5)  # Continue monitoring
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    
    print("\n" + "="*70)
    print("VALIDATION CHECKLIST:")
    print("="*70)
    print("[ ] Article matches blog style (mobile gaming focus)")
    print("[ ] Citations properly numbered [1], [2], etc.")
    print("[ ] Metrics integrated naturally")
    print("[ ] Testimonial placement makes sense")
    print("[ ] Sources section at bottom")
    print("[ ] SEO metadata added")
    print("[ ] Humanization applied")
    print("[ ] Images/media generated")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
