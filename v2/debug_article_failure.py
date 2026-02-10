"""
Debug script to investigate article generation failures
"""

import os
import sys
import json
from datetime import datetime

# Set up environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///agc_v2.db")

def check_failed_article():
    """Check the most recent failed article"""

    if DATABASE_URL.startswith("sqlite"):
        import sqlite3
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get most recent failed article
        cursor.execute("""
            SELECT id, title, state, error, retry_count, updated_at
            FROM articles_v2
            WHERE state = 'failed' OR error IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 1
        """)

        result = cursor.fetchone()

        if not result:
            print("❌ No failed articles found")
            return

        article_id, title, state, error, retry_count, updated_at = result

        print("="*70)
        print("FAILED ARTICLE DETAILS")
        print("="*70)
        print(f"\nID: {article_id}")
        print(f"Title: {title}")
        print(f"State: {state}")
        print(f"Retry Count: {retry_count}")
        print(f"Updated: {updated_at}")
        print(f"\n❌ Error:")
        print(f"   {error}")

        # Check what data exists
        cursor.execute("""
            SELECT research, draft, enrichment, revised_draft, fact_check
            FROM articles_v2
            WHERE id = ?
        """, (article_id,))

        data = cursor.fetchone()
        research, draft, enrichment, revised_draft, fact_check = data

        print(f"\n📊 Pipeline Progress:")
        print(f"   Research: {'✅' if research else '❌'}")
        print(f"   Draft: {'✅' if draft else '❌'} ({len(draft.split()) if draft else 0} words)")
        print(f"   Enrichment: {'✅' if enrichment else '❌'}")
        print(f"   Revised Draft: {'✅' if revised_draft else '❌'} ({len(revised_draft.split()) if revised_draft else 0} words)")
        print(f"   Fact Check: {'✅' if fact_check else '❌'}")

        # If fact check exists, show details
        if fact_check:
            try:
                fc_data = json.loads(fact_check) if isinstance(fact_check, str) else fact_check
                print(f"\n📋 Fact Check Details:")
                print(f"   Total Claims: {fc_data.get('total_claims', 'N/A')}")
                print(f"   Verified: {fc_data.get('verified_claims', 'N/A')}")
                print(f"   Accuracy: {fc_data.get('accuracy_score', 0)*100:.1f}%")

                if fc_data.get('issues'):
                    print(f"\n⚠️  Issues:")
                    for issue in fc_data['issues'][:5]:
                        print(f"      - {issue}")

                citations = fc_data.get('citations', {})
                if citations:
                    print(f"\n📎 Citations:")
                    print(f"   Total: {citations.get('total_citations', 0)}")
                    print(f"   Valid: {citations.get('valid_citations', 0)}")
                    if citations.get('issues'):
                        print(f"   Issues:")
                        for issue in citations['issues'][:3]:
                            print(f"      - {issue}")
            except Exception as e:
                print(f"   ⚠️  Could not parse fact check data: {e}")

        # Get event log
        cursor.execute("""
            SELECT event_type, data, created_at
            FROM events_v2
            WHERE article_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (article_id,))

        events = cursor.fetchall()

        if events:
            print(f"\n📜 Recent Events:")
            for event_type, event_data, created_at in events:
                try:
                    data_dict = json.loads(event_data) if isinstance(event_data, str) else event_data
                    if event_type == "state_changed":
                        print(f"   [{created_at}] {data_dict.get('from')} → {data_dict.get('to')}")
                    elif event_type == "retry":
                        print(f"   [{created_at}] RETRY #{data_dict.get('attempt')}: {data_dict.get('error')}")
                    elif event_type == "failed":
                        print(f"   [{created_at}] FAILED: {data_dict.get('error')}")
                except:
                    print(f"   [{created_at}] {event_type}")

        conn.close()

        print("\n" + "="*70)
        print("RECOMMENDATIONS")
        print("="*70)

        # Analyze the error
        if error:
            error_lower = error.lower()

            if "timeout" in error_lower:
                print("\n⏱️  TIMEOUT ERROR")
                print("   - API call took too long (>60s)")
                print("   - Check OpenRouter API status")
                print("   - Consider increasing timeout in fact_checker.py")

            elif "citation" in error_lower or "url" in error_lower:
                print("\n📎 CITATION ERROR")
                print("   - Citation format or URL mismatch")
                print("   - Check revised_draft for citation format: [[n]](url)")
                print("   - Verify URLs match research sources")

            elif "accuracy" in error_lower or "low" in error_lower:
                print("\n📊 ACCURACY ERROR")
                print("   - Less than 85% claims verified")
                print("   - Draft may have unsupported claims")
                print("   - Check if sources match article content")

            elif "api" in error_lower or "key" in error_lower:
                print("\n🔑 API ERROR")
                print("   - Check OPENROUTER_API_KEY is set")
                print("   - Verify API key is valid")
                print("   - Check OpenRouter account status")

            else:
                print(f"\n❓ UNKNOWN ERROR")
                print(f"   Error: {error}")
                print(f"   - Check server logs for full details")
                print(f"   - Review fact_checker.py line near error")

        print("\n💡 To fix:")
        print("   1. Check Railway logs for full error trace")
        print("   2. Verify all API keys are set correctly")
        print("   3. Check OpenRouter API status")
        print("   4. Consider adjusting fact checker thresholds")
        print("   5. Retry the article if it was a temporary issue")


if __name__ == "__main__":
    check_failed_article()
