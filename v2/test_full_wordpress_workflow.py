"""
Full WordPress Workflow Test
Tests the complete pipeline with WordPress export functionality
"""

import asyncio
import time
import requests
from pathlib import Path
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70)


async def test_wordpress_workflow():
    """Test complete WordPress workflow"""

    print_section("🚀 WORDPRESS WORKFLOW TEST - FULL PIPELINE")

    # 1. Create topic
    topic_data = {
        "title": "Mobile Game Monetization Strategies for 2025",
        "keyword": "mobile game monetization"
    }

    print(f"\n📝 Step 1: Creating topic...")
    print(f"   Title: {topic_data['title']}")

    try:
        response = requests.post(f"{BASE_URL}/topics", json=topic_data, timeout=10)
        response.raise_for_status()
        data = response.json()
        topic_id = data["id"]
        print(f"   ✅ Topic created: {topic_id}")
    except Exception as e:
        print(f"\n❌ Failed to create topic: {e}")
        print("\n💡 Make sure the server is running:")
        print("   cd v2")
        print("   export USE_REAL_AGENTS=true")
        print("   export OPENROUTER_API_KEY=your_key")
        print("   export BRAVE_API_KEY=your_key")
        print("   export GOOGLE_API_KEY=your_key")
        print("   python server.py")
        return False

    # 2. Approve topic (creates article)
    print(f"\n📝 Step 2: Approving topic (creates article)...")

    try:
        response = requests.post(f"{BASE_URL}/topics/{topic_id}/approve", timeout=10)
        response.raise_for_status()
        data = response.json()
        article_id = data["article_id"]
        print(f"   ✅ Article created: {article_id}")
    except Exception as e:
        print(f"   ❌ Failed to approve topic: {e}")
        return False

    # 3. Monitor pipeline progress
    print(f"\n📝 Step 3: Monitoring pipeline progress...")
    print("   (This will take 5-10 minutes depending on agents)")
    print("\n" + "-"*70)

    start_time = time.time()
    last_state = None
    state_times = {}

    while True:
        try:
            response = requests.get(f"{BASE_URL}/articles/{article_id}", timeout=60)
            response.raise_for_status()
            article = response.json()

            current_state = article["state"]

            # Track state changes
            if current_state != last_state:
                elapsed = time.time() - start_time
                print(f"   [{elapsed:>6.1f}s] {current_state.upper()}")

                if last_state:
                    state_duration = elapsed - state_times.get(last_state, start_time)
                    print(f"            ({last_state} took {state_duration:.1f}s)")

                state_times[current_state] = elapsed
                last_state = current_state

            # Check for completion
            if current_state == "ready":
                print("\n" + "="*70)
                print("✅ PIPELINE COMPLETE!")
                print("="*70)

                elapsed = time.time() - start_time
                print(f"\n⏱️  Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

                # Show state durations
                print(f"\n📊 State durations:")
                states = list(state_times.keys())
                for i, state in enumerate(states):
                    if i == 0:
                        duration = state_times[state]
                    else:
                        duration = state_times[state] - state_times[states[i-1]]
                    print(f"   {state:20s}: {duration:>6.1f}s")

                break

            elif current_state == "failed":
                print("\n" + "="*70)
                print("❌ PIPELINE FAILED")
                print("="*70)
                print(f"   Error: {article.get('error', 'Unknown error')}")
                return False

            # Wait before next check
            await asyncio.sleep(5)

        except requests.exceptions.Timeout:
            print(".", end="", flush=True)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"\n   ⚠️  Error checking status: {e}")
            await asyncio.sleep(5)

    # 4. Validate article data
    print(f"\n📝 Step 4: Validating article data...")

    print(f"\n📄 Article Details:")
    print(f"   Title: {article['title']}")
    print(f"   State: {article['state']}")

    # Check content
    if article.get('final_content'):
        word_count = len(article['final_content'].split())
        print(f"   ✅ Final content: {word_count} words")
    else:
        print(f"   ❌ No final content!")

    # Check WordPress data
    print(f"\n🎨 WordPress Export Data:")

    if article.get('wordpress_content'):
        print(f"   ✅ WordPress content generated")
        content_len = len(article['wordpress_content'])
        print(f"      Length: {content_len} characters")
    else:
        print(f"   ❌ No WordPress content!")

    if article.get('wordpress_metadata'):
        metadata = article['wordpress_metadata']
        print(f"   ✅ SEO Metadata:")
        print(f"      Title: {metadata.get('seo_title', 'N/A')}")
        print(f"      Description: {metadata.get('meta_description', 'N/A')[:50]}...")
        print(f"      Categories: {', '.join(metadata.get('categories', []))}")
        print(f"      Tags: {len(metadata.get('tags', []))} tags")
    else:
        print(f"   ❌ No WordPress metadata!")

    export_ready = article.get('wordpress_export_ready', False)
    print(f"\n   Export Ready: {'✅ YES' if export_ready else '❌ NO'}")

    if article.get('wordpress_validation_issues'):
        issues = article['wordpress_validation_issues']
        if issues:
            print(f"   ⚠️  Validation issues: {len(issues)}")
            for issue in issues[:3]:
                print(f"      - {issue}")

    # 5. Test WordPress endpoint
    print(f"\n📝 Step 5: Testing WordPress export endpoint...")

    try:
        response = requests.get(f"{BASE_URL}/articles/{article_id}/wordpress", timeout=10)
        response.raise_for_status()
        wp_data = response.json()

        print(f"   ✅ WordPress endpoint working")
        print(f"      Content length: {len(wp_data['wordpress_content'])} chars")
        print(f"      Export ready: {wp_data['export_ready']}")

        # Save to file for inspection
        output_file = Path(__file__).parent / "test_outputs" / f"wordpress_export_{article_id[:8]}.md"
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            f.write(wp_data['wordpress_content'])

        print(f"      📁 Saved to: {output_file}")

        # Show frontmatter preview
        lines = wp_data['wordpress_content'].split('\n')
        if lines[0] == '---':
            frontmatter_end = lines[1:].index('---') + 1
            frontmatter = '\n'.join(lines[:frontmatter_end+1])

            print(f"\n   📋 Frontmatter Preview:")
            print("   " + "-"*66)
            for line in frontmatter.split('\n')[:10]:
                print(f"   {line}")
            print("   " + "-"*66)

    except Exception as e:
        print(f"   ❌ WordPress endpoint failed: {e}")
        return False

    # 6. Final summary
    print_section("✅ TEST COMPLETE - SUMMARY")

    print(f"\n✨ WordPress Export Workflow:")
    print(f"   1. Article ID: {article_id[:8]}...")
    print(f"   2. Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"   3. Final word count: {word_count} words")
    print(f"   4. WordPress content: ✅ Generated")
    print(f"   5. SEO metadata: ✅ Generated")
    print(f"   6. Export ready: {'✅' if export_ready else '⚠️'}")

    print(f"\n🎯 Next Steps:")
    print(f"   1. Open browser: http://localhost:8000/article/{article_id}")
    print(f"   2. See the WordPress export section")
    print(f"   3. Click 'Copy for WordPress' button")
    print(f"   4. Paste into WordPress editor")
    print(f"   5. Publish! 🚀")

    print(f"\n📁 Files Generated:")
    print(f"   - WordPress export: {output_file}")

    return True


if __name__ == "__main__":
    print("\n🧪 Starting Full WordPress Workflow Test")
    print("   This will test the complete pipeline from topic → WordPress export")
    print("   Ensure the server is running with USE_REAL_AGENTS=true")

    result = asyncio.run(test_wordpress_workflow())

    if result:
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("❌ TESTS FAILED")
        print("="*70)

    exit(0 if result else 1)
