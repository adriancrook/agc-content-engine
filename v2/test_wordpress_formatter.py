"""
Test WordPress Formatter
Quick validation of metadata generation and formatting
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from formatters.wordpress import WordPressFormatter


def test_wordpress_formatter():
    """Test WordPress formatter with sample article"""

    print("\n" + "=" * 70)
    print("WORDPRESS FORMATTER TEST")
    print("=" * 70)

    # Sample article data
    article_data = {
        "title": "Mobile Game Monetization Strategies for 2025",
        "final_content": """# Mobile Game Monetization Strategies for 2025

The mobile gaming industry continues to evolve, with monetization becoming increasingly sophisticated[[1]](https://example.com/source1). Free-to-play games dominate the market, generating billions in revenue through in-app purchases and advertising.

**Key Takeaways:**
- **Hybrid monetization** combines IAP with rewarded video ads for maximum revenue
- **Battle pass systems** drive engagement and recurring revenue
- **Player segmentation** enables targeted monetization strategies

## In-App Purchase Optimization

In-app purchases remain the primary revenue driver for mobile games[[2]](https://example.com/source2). Successful games implement tiered pricing strategies that cater to different player segments, from casual spenders to whales.

> "The key is balancing monetization with player satisfaction"
> — Industry Expert[[3]](https://example.com/source3)

Games must carefully balance progression systems with monetization touchpoints[[4]](https://example.com/source4). Too aggressive and players churn; too passive and revenue suffers.

## Advertising Integration

Rewarded video ads have become the preferred ad format[[5]](https://example.com/source5). Players voluntarily engage with ads in exchange for in-game rewards, maintaining user experience while generating revenue.

Statistics show that 80% of players prefer rewarded ads over interstitials[[6]](https://example.com/source6). This format respects player agency and provides tangible value.

## Player Analytics and Metrics

Understanding your game's KPIs is essential[[7]](https://example.com/source7). Key metrics include ARPU, LTV, retention rates, and conversion funnel analysis. Data-driven decisions enable continuous optimization[[8]](https://example.com/source8).

## Game Economy Design

Virtual economy design directly impacts monetization success[[9]](https://example.com/source9). Currency sinks, pricing psychology, and perceived value all influence player spending behavior[[10]](https://example.com/source10).

## Live Operations Strategy

Ongoing content updates and events drive retention and monetization[[11]](https://example.com/source11). Seasonal events, limited-time offers, and battle passes create urgency and recurring revenue streams.

## Conclusion

Successful mobile game monetization requires understanding player psychology, leveraging data analytics, and continuously optimizing based on performance metrics. The most profitable games balance player satisfaction with revenue generation.

## FAQs

### What is the most effective monetization model for mobile games?
Hybrid monetization combining in-app purchases with rewarded video ads tends to be most effective, as it caters to both paying and non-paying players.

### How much should items cost in a mobile game?
Pricing should be tiered from $0.99 to $99.99, with the majority of purchases in the $2.99-$9.99 range to maximize conversion rates.

### How do I balance monetization with player retention?
Focus on providing value first, then monetize. Avoid pay-to-win mechanics and ensure free players can progress meaningfully.

## Sources

[1] Mobile Gaming Trends 2025 - https://example.com/source1
[2] IAP Best Practices - https://example.com/source2
[3] Industry Expert Interview - https://example.com/source3
[4] Game Balance Study - https://example.com/source4
[5] Ad Format Research - https://example.com/source5
[6] Player Preferences Survey - https://example.com/source6
[7] Analytics Guide - https://example.com/source7
[8] Data-Driven Design - https://example.com/source8
[9] Virtual Economy Principles - https://example.com/source9
[10] Pricing Psychology - https://example.com/source10
[11] Live Ops Best Practices - https://example.com/source11
""",
        "research": {},
        "seo": {},
        "media": {
            "featured_image": "mobile_game_monetization_2025.png"
        }
    }

    # Create formatter
    formatter = WordPressFormatter()

    # Format article
    print(f"\nFormatting article: {article_data['title']}")
    print(f"Content length: {len(article_data['final_content'])} chars")

    result = formatter.format(article_data)

    # Display results
    print("\n" + "-" * 70)
    print("METADATA GENERATED")
    print("-" * 70)

    metadata = result["metadata"]
    print(f"\nSEO Title: {metadata['seo_title']}")
    print(f"  Length: {len(metadata['seo_title'])} chars")

    print(f"\nMeta Description: {metadata['meta_description']}")
    print(f"  Length: {len(metadata['meta_description'])} chars")

    print(f"\nKeywords: {', '.join(metadata['keywords'])}")
    print(f"  Count: {len(metadata['keywords'])}")

    print(f"\nCategories: {', '.join(metadata['categories'])}")
    print(f"  Count: {len(metadata['categories'])}")

    print(f"\nTags: {', '.join(metadata['tags'])}")
    print(f"  Count: {len(metadata['tags'])}")

    print(f"\nFeatured Image Alt: {metadata['featured_image_alt']}")

    print(f"\nAuthor: {metadata['author']}")
    print(f"Date: {metadata['date']}")

    # Validation
    print("\n" + "-" * 70)
    print("VALIDATION")
    print("-" * 70)

    print(f"\nExport Ready: {'✅ YES' if result['export_ready'] else '❌ NO'}")

    if result["validation_issues"]:
        print(f"\nValidation Issues ({len(result['validation_issues'])}):")
        for issue in result["validation_issues"]:
            print(f"  ⚠️  {issue}")
    else:
        print("\n✅ No validation issues!")

    # Show frontmatter preview
    print("\n" + "-" * 70)
    print("FRONTMATTER PREVIEW")
    print("-" * 70)

    content_lines = result["wordpress_content"].split("\n")
    frontmatter_end = content_lines.index("---", 1) if "---" in content_lines[1:] else 20
    frontmatter = "\n".join(content_lines[:frontmatter_end + 1])
    print(f"\n{frontmatter}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    success = (
        len(metadata['seo_title']) <= 60 and
        len(metadata['meta_description']) <= 160 and
        len(metadata['keywords']) >= 5 and
        len(metadata['categories']) >= 1 and
        len(metadata['tags']) >= 5 and
        result['export_ready']
    )

    if success:
        print("\n✅ ALL TESTS PASSED!")
        print(f"  - SEO title: {len(metadata['seo_title'])} chars ✓")
        print(f"  - Meta description: {len(metadata['meta_description'])} chars ✓")
        print(f"  - Keywords: {len(metadata['keywords'])} ✓")
        print(f"  - Categories: {len(metadata['categories'])} ✓")
        print(f"  - Tags: {len(metadata['tags'])} ✓")
        print(f"  - Export ready: ✓")
    else:
        print("\n❌ TESTS FAILED")
        print(f"  - SEO title: {len(metadata['seo_title'])} chars")
        print(f"  - Meta description: {len(metadata['meta_description'])} chars")
        print(f"  - Keywords: {len(metadata['keywords'])}")
        print(f"  - Categories: {len(metadata['categories'])}")
        print(f"  - Tags: {len(metadata['tags'])}")
        print(f"  - Export ready: {result['export_ready']}")

    # Save output
    output_file = Path(__file__).parent / "test_wordpress_output.md"
    with open(output_file, 'w') as f:
        f.write(result["wordpress_content"])
    print(f"\n📝 WordPress content saved to: {output_file}")

    return success


if __name__ == "__main__":
    result = test_wordpress_formatter()
    sys.exit(0 if result else 1)
