"""
Format-specific prompts for different article types
Based on adriancrook.com blog analysis
"""

# Mobile gaming context that applies to ALL formats
MOBILE_GAMING_CONTEXT = """
MOBILE GAMING FOCUS:
- Target audience: Mobile game developers, publishers, product managers
- Industry: Freemium/F2P mobile games
- Examples should use real mobile games: Candy Crush, Clash of Clans, Pokémon GO, Genshin Impact,
  PUBG Mobile, Clash Royale, Brawl Stars, Marvel Snap, Block Blast, Vita Mahjong, etc.
- Focus areas: monetization, retention, game economy, player engagement, live ops

TONE GUIDELINES:
- Professional but practical (NOT academic)
- Industry professional voice (speaking to peers)
- Actionable and clear
- Use contractions sparingly
- AVOID: "honestly", "let me tell you", "here's the thing", "paradigm shift", "fundamental transformation"
- USE: "Here's what works", "Developers should", "Key considerations", "This matters because"

MOBILE GAME METRICS TO REFERENCE:
- ARPU (Average Revenue Per User)
- LTV (Lifetime Value)
- D1/D7/D30 Retention
- DAU (Daily Active Users)
- Conversion Rate
- Session Length
- ARPPU (Average Revenue Per Paying User)
"""

# Format 1: Prediction/Analysis (YouTube Deep Dive)
PREDICTION_ANALYSIS_PROMPT = """
You are writing for adriancrook.com - a mobile gaming industry blog for professionals.

{mobile_gaming_context}

ARTICLE TYPE: Prediction/Analysis (YouTube Video Deep Dive)
TOPIC: {topic}
SOURCE: {source_description}

REQUIRED STRUCTURE:

1. HOOK INTRO (200-250 words):
   - Start with context about the mobile gaming industry trend
   - Reference the source (e.g., "A recent video discussion among industry experts...")
   - Preview what insights will be covered
   - NO generic statements - be specific about mobile gaming

2. MAIN SECTIONS (3-5 predictions):
   Each section must have this exact structure:

   ## [Compelling Section Title - Make it a Question or Bold Statement]

   **Prediction:** [Bold, specific prediction statement]

   [2-3 paragraphs explaining the prediction with specific examples from mobile games]

   **Why This Matters:**
   1. **[Point Name]**: [Explanation for developers/publishers]
   2. **[Point Name]**: [Explanation for developers/publishers]
   3. **[Point Name]**: [Explanation for developers/publishers]

   **Key Drivers:**
   - [Specific driver with example]
   - [Specific driver with example]
   - [Specific driver with example]

3. KEY TAKEAWAYS (Bulleted list at end):
   - [Concise actionable takeaway]
   - [Concise actionable takeaway]
   - [Concise actionable takeaway]

4. CONCLUSION (150-200 words):
   - Synthesize the predictions
   - Forward-looking implications
   - End with actionable insight

5. SOURCE CITATION:
   Source: "[Video Title]" – [Channel/Source], [Platform], [Date] – [URL]

REQUIREMENTS:
- Use REAL mobile game examples (Candy Crush, Clash of Clans, etc.)
- Include specific metrics when possible ($3M revenue, 50% increase, etc.)
- Every prediction must have "Why This Matters" and "Key Drivers"
- Target: 2000-2500 words
- Professional but practical tone
- Actionable for mobile game developers/publishers

Write the complete article in markdown format.
"""

# Format 2: Ultimate Guide
ULTIMATE_GUIDE_PROMPT = """
You are writing for adriancrook.com - a mobile gaming industry blog for professionals.

{mobile_gaming_context}

ARTICLE TYPE: Ultimate Guide
TOPIC: {topic}
FORMAT: Comprehensive how-to guide for mobile game developers

REQUIRED STRUCTURE:

1. HOOK INTRO (150-200 words):
   - Open with why this topic matters for mobile games
   - Provide a quick breakdown (3-4 bullet points)
   - Example: "Want to create engaging X that keep players hooked? Here's what works:"

2. KEY TAKEAWAYS (Before main content):
   **Key Takeaways:**
   - [Main point with brief explanation]
   - [Main point with brief explanation]
   - [Main point with brief explanation]
   - [Main point with brief explanation]

3. MAIN CONTENT SECTIONS (4-6 H2 sections):
   Each section should have:
   - Clear H2 heading
   - 2-3 H3 subsections
   - At least 1 TABLE comparing options, best practices, or showing framework
   - Specific mobile game examples
   - Actionable guidance

   TABLE FORMAT (use at least 2 tables):
   | Aspect | Option A | Option B | Best For |
   |--------|----------|----------|----------|
   | [Row]  | [Data]   | [Data]   | [Guidance] |

4. COMMON MISTAKES SECTION:
   ## Common Mistakes to Avoid
   - [Mistake]: [Why it's bad] → [What to do instead]
   - [Mistake]: [Why it's bad] → [What to do instead]
   - [Mistake]: [Why it's bad] → [What to do instead]

5. IMPLEMENTATION GUIDE:
   ## How to Implement [Topic]
   Step-by-step guidance with examples

6. PROFESSIONAL SERVICES (Optional but recommended):
   Brief mention of AC&A consulting services (1-2 sentences max)
   Example: "Working with experts in game economy design can help refine these systems."

7. CONCLUSION (150-200 words):
   - Recap main points
   - Actionable next steps
   - Forward-looking insight

8. FAQs (EXACTLY 3 questions):
   ## FAQs

   ### [Specific question about the topic]?
   [Detailed answer with examples, 100-150 words]

   ### [Specific question about implementation]?
   [Detailed answer with examples, 100-150 words]

   ### [Specific question about common challenges]?
   [Detailed answer with examples, 100-150 words]

REQUIREMENTS:
- At least 2-3 tables
- Real mobile game examples throughout
- Practical, actionable advice
- Target: 2000-2500 words
- Professional but accessible tone

Write the complete article in markdown format.
"""

# Format 3: Conceptual Deep Dive
CONCEPTUAL_DEEPDIVE_PROMPT = """
You are writing for adriancrook.com - a mobile gaming industry blog for professionals.

{mobile_gaming_context}

ARTICLE TYPE: Conceptual Deep Dive
TOPIC: {topic}
FORMAT: Explaining game design concepts with comparison and application

REQUIRED STRUCTURE:

1. HOOK INTRO (150-200 words):
   - Start with a question or statement about player behavior
   - Explain why this concept matters
   - Preview the comparison/analysis

2. KEY TAKEAWAYS (Top of article):
   **Key Takeaways:**
   - **[Concept A]**: [Brief explanation and impact]
   - **[Concept B]**: [Brief explanation and impact]
   - **The Balance**: [How they work together]

3. QUICK COMPARISON TABLE (Early in article):
   | Aspect | [Concept A] | [Concept B] |
   |--------|-------------|-------------|
   | Source | [Description] | [Description] |
   | Engagement | [Type] | [Type] |
   | Focus | [What] | [What] |
   | Monetization | [How] | [How] |
   | Risks | [Issues] | [Issues] |

4. DEEP DIVE SECTIONS:

   ## [Concept A] in Mobile Games

   ### Understanding [Concept A]
   [Explanation with examples]

   ### Game Features That Use [Concept A]
   - [Feature]: [How it works]
   - [Feature]: [How it works]
   - [Feature]: [How it works]

   ### Why [Concept A] Matters
   [Benefits and impacts with examples]

   [REPEAT STRUCTURE FOR CONCEPT B]

5. SIDE-BY-SIDE ANALYSIS:
   ## Comparing [Concept A] vs [Concept B]

   ### Key Differences
   [Analysis of behavioral differences]

   ### Comparison Table (Detailed)
   | Type | [Concept A] | [Concept B] |
   |------|-------------|-------------|
   | [Aspect] | [Detail] | [Detail] |
   | [Aspect] | [Detail] | [Detail] |

   ### Combining Both Approaches
   [How to balance both concepts effectively]

6. APPLICATION IN FREEMIUM GAMES:
   ## Application in Freemium Game Design

   ### Design Implementation Guide
   [Practical steps for developers]

   ### Professional Design Support (Optional)
   [Brief AC&A mention with testimonial if relevant]

7. CONCLUSION:
   ## Conclusion

   ### Main Points
   [Key insights recap]

   ### Recommendations
   [Actionable guidance for developers]

8. FAQs (EXACTLY 3):
   [Same format as Ultimate Guide]

REQUIREMENTS:
- At least 2 comparison tables
- Real mobile game examples (Clash Royale, Candy Crush, etc.)
- Show how concepts apply to freemium monetization
- Target: 1800-2200 words
- Clear, educational tone

Write the complete article in markdown format.
"""

# Format 4: Best Practices
BEST_PRACTICES_PROMPT = """
You are writing for adriancrook.com - a mobile gaming industry blog for professionals.

{mobile_gaming_context}

ARTICLE TYPE: Best Practices Guide
TOPIC: {topic}
FORMAT: Problem/solution guide for mobile game developers

REQUIRED STRUCTURE:

1. HOOK INTRO (100-150 words):
   - Start with the problem/challenge
   - Provide quick breakdown of solutions (3-4 bullets)
   - "Here's what works:" style

2. KEY ELEMENTS SECTION:
   ## Key Elements of [Topic]

   ### [Element 1]
   [Explanation with mobile game examples]

   ### [Element 2]
   [Explanation with mobile game examples]

   ### [Element 3]
   [Explanation with mobile game examples]

3. COMMON PROBLEMS/MISTAKES:
   ## Common [Topic] Issues

   ### [Problem 1]
   [Explanation of the issue and why it happens]

   ### [Problem 2]
   [Explanation of the issue and why it happens]

   ### [Problem 3]
   [Explanation of the issue and why it happens]

   BEST PRACTICES TABLE:
   | Issue | Common Mistake | Best Practice | Implementation Tips |
   |-------|----------------|---------------|---------------------|
   | [Issue] | [Wrong way] | [Right way] | [How to do it] |
   | [Issue] | [Wrong way] | [Right way] | [How to do it] |

4. SOLUTIONS/HOW TO FIX:
   ## How to Solve [Topic] Problems

   ### [Solution 1]
   [Detailed guidance with steps]

   ### [Solution 2]
   [Detailed guidance with steps]

   ### [Solution 3]
   [Detailed guidance with steps]

5. MEASURING SUCCESS:
   ## Tracking [Topic] Performance

   ### Key Metrics
   - [Metric]: [What to track and why]
   - [Metric]: [What to track and why]
   - [Metric]: [What to track and why]

   ### Testing Methods
   [How to validate improvements]

6. PROFESSIONAL HELP (Optional):
   Brief mention of consulting services if relevant

7. SUMMARY:
   ## Summary

   [Table summarizing key principles]

   | Component | Best Practice | Impact |
   |-----------|---------------|--------|
   | [Element] | [Practice] | [Result] |

8. FAQs (EXACTLY 3):
   [Same format as other templates]

REQUIREMENTS:
- At least 2 reference/best practice tables
- Real mobile game examples
- Problem → Solution structure
- Target: 1800-2200 words
- Practical, actionable tone

Write the complete article in markdown format.
"""

# Helper function to get the right prompt
def get_format_prompt(format_type: str, topic: str, source_description: str = "") -> str:
    """
    Get the appropriate prompt template for the article format

    Args:
        format_type: One of 'prediction', 'guide', 'conceptual', 'best_practices'
        topic: The article topic
        source_description: Description of the source (for predictions)

    Returns:
        Formatted prompt string
    """
    prompts = {
        'prediction': PREDICTION_ANALYSIS_PROMPT,
        'guide': ULTIMATE_GUIDE_PROMPT,
        'conceptual': CONCEPTUAL_DEEPDIVE_PROMPT,
        'best_practices': BEST_PRACTICES_PROMPT,
    }

    if format_type not in prompts:
        raise ValueError(f"Unknown format type: {format_type}. Must be one of {list(prompts.keys())}")

    template = prompts[format_type]

    return template.format(
        mobile_gaming_context=MOBILE_GAMING_CONTEXT,
        topic=topic,
        source_description=source_description
    )
