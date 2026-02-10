# DataEnrichment Debugging Guide

**Updated:** 2026-02-09
**Status:** Enhanced logging added, ready for testing

---

## 🔧 What Was Added

### 1. Enhanced Logging (Step-by-Step Visibility)
Added detailed logging to **every step** of the enrichment process:

- ✅ **Step timing** - Each of 6 steps logs start and completion time
- ✅ **API call logging** - Before and after OpenRouter/Brave calls
- ✅ **Progress indicators** - Clear markers (STEP X/6, ✓, →)
- ✅ **Result counts** - Shows claims found, citations discovered, etc.
- ✅ **Detailed error handling** - Separate logging for timeouts vs errors

### 2. Improved Exception Handling
- ✅ Specific handling for `requests.exceptions.Timeout`
- ✅ Separate handling for `requests.exceptions.RequestException`
- ✅ More descriptive error messages with emojis (⚠️, ❌, ✓)

### 3. Test Script for Finding Breaking Point
Created [test_enrichment_sizes.py](v2/test_enrichment_sizes.py):
- Tests incrementally: 100, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 5000 words
- 90-second timeout per test
- Identifies exact breaking point
- Summary report at the end

---

## 🧪 How to Debug

### Step 1: Run Minimal Test (Known to Work)
This proves the agent logic is correct:

```bash
cd v2
python test_enrichment_minimal.py
```

**Expected:**
- ✅ Completes in ~7-8 seconds
- ✅ Returns 3-5 citations, 1-2 metrics, 0-1 testimonials
- ✅ All 6 steps complete successfully

**If it hangs:** Check API keys and network connection

---

### Step 2: Find Breaking Point
Run incremental tests to identify where it fails:

```bash
cd v2
python test_enrichment_sizes.py
```

**What to watch for:**
- Which step hangs (STEP 1/6, 2/6, etc.)?
- Does it hang at the same word count?
- Does it timeout at OpenRouter or Brave Search?

**Expected output:**
```
STEP 1/6: Analyzing draft for enrichment needs...
  → Calling Claude API to analyze 2543 chars...
  → Calling OpenRouter API (timeout: 120s)...
  ✓ OpenRouter API returned 543 chars
  ✓ Claude API returned 543 chars
✓ Draft analysis complete in 3.2s - Found 5 claims, 3 examples, 4 sections

STEP 2/6: Finding citations for 5 claims...
  → Brave Search 1/5: Gacha mechanics drive billions in mobile...
  ✓ Found 5 results
  → Brave Search 2/5: Genshin Impact generates over $3 billion...
  ✓ Found 5 results
  [etc...]
```

**Where it might hang:**
- ⚠️ **STEP 1** - OpenRouter API timeout (draft too large)
- ⚠️ **STEP 2** - Brave Search timeout (too many claims)
- ⚠️ **STEP 6** - Integration guide too large

---

### Step 3: Analyze Logs

Look for the **last log message** before hanging:

#### If hangs at "Calling OpenRouter API":
**Problem:** Draft analysis taking too long
**Solution:**
- Reduce MAX_ANALYSIS_WORDS (currently 1500)
- Or increase OpenRouter timeout (currently 120s)
- Or use faster model (claude-haiku instead of claude-sonnet)

#### If hangs at "Brave Search X/Y":
**Problem:** Multiple sequential Brave API calls
**Solution:**
- Reduce claims limit (currently 5)
- Or parallelize Brave searches (use async)
- Or increase individual timeout (currently 10s)

#### If hangs at "Creating integration guide":
**Problem:** Guide generation with large data
**Solution:**
- Limit guide size
- Or simplify guide format

---

## 🎯 Quick Fixes (If Needed)

### Fix 1: Reduce Analysis Size
**File:** [v2/agents/data_enrichment.py](v2/agents/data_enrichment.py)
**Line:** 86

```python
# Change from:
MAX_ANALYSIS_WORDS = 1500

# To:
MAX_ANALYSIS_WORDS = 1000  # More aggressive truncation
```

---

### Fix 2: Reduce Citations Limit
**File:** [v2/agents/data_enrichment.py](v2/agents/data_enrichment.py)
**Line:** 211

```python
# Change from:
for i, claim in enumerate(claims[:5]):  # Limit to 5 citations

# To:
for i, claim in enumerate(claims[:3]):  # Limit to 3 citations
```

---

### Fix 3: Use Faster Model
**File:** [v2/agents/data_enrichment.py](v2/agents/data_enrichment.py)
**Line:** 549

```python
# Change from:
"model": "anthropic/claude-sonnet-4",

# To:
"model": "anthropic/claude-haiku-4.5",  # 10x faster
```

---

## 📊 Expected Performance

Based on session notes:

| Draft Size | Expected Time | Status |
|------------|---------------|--------|
| 100 words  | 7-8s          | ✅ Works |
| 500 words  | 10-15s        | 🔍 Unknown |
| 1000 words | 15-20s        | 🔍 Unknown |
| 1500 words | 20-30s        | 🔍 Unknown |
| 2000 words | 30-40s        | 🔍 Unknown |
| 4500 words | ???           | ❌ Hangs |

---

## 🚀 Testing Workflow

```bash
# 1. Verify minimal test works
cd v2
python test_enrichment_minimal.py

# Expected: 7-8 seconds, success

# 2. Find breaking point
python test_enrichment_sizes.py

# Expected: Identify exact word count where it fails

# 3. Analyze logs - look for last message before hanging

# 4. Apply quick fix if needed

# 5. Re-run test to confirm fix

# 6. Test full pipeline
python test_full_pipeline.py
```

---

## 📝 Logging Output Examples

### ✅ Successful Run
```
2026-02-09 14:23:45 [INFO] data_enrichment: Enriching article: Gacha Mechanics (97 words)
2026-02-09 14:23:45 [INFO] data_enrichment: STEP 1/6: Analyzing draft for enrichment needs...
2026-02-09 14:23:45 [INFO] data_enrichment:   → Calling Claude API to analyze 543 chars...
2026-02-09 14:23:45 [INFO] data_enrichment:   → Calling OpenRouter API (timeout: 120s)...
2026-02-09 14:23:48 [INFO] data_enrichment:   ✓ OpenRouter API returned 234 chars
2026-02-09 14:23:48 [INFO] data_enrichment:   ✓ Claude API returned 234 chars
2026-02-09 14:23:48 [INFO] data_enrichment: ✓ Draft analysis complete in 3.2s - Found 5 claims, 2 examples, 3 sections
2026-02-09 14:23:48 [INFO] data_enrichment: STEP 2/6: Finding citations for 5 claims...
2026-02-09 14:23:48 [INFO] data_enrichment:   → Brave Search 1/5: Gacha mechanics drive...
2026-02-09 14:23:49 [INFO] data_enrichment:   ✓ Found 5 results
[...continues for all steps...]
2026-02-09 14:23:52 [INFO] data_enrichment: 🎉 ENRICHMENT COMPLETE in 7.4s: 5 citations, 2 metrics, 1 testimonials
```

### ❌ Timeout Example
```
2026-02-09 14:23:45 [INFO] data_enrichment: STEP 1/6: Analyzing draft for enrichment needs...
2026-02-09 14:23:45 [INFO] data_enrichment:   → Calling Claude API to analyze 8543 chars...
2026-02-09 14:23:45 [INFO] data_enrichment:   → Calling OpenRouter API (timeout: 120s)...
[...120 seconds pass...]
2026-02-09 14:25:45 [ERROR] data_enrichment: ⚠️ OpenRouter API TIMEOUT after 120s
```

---

## ✅ Success Criteria

You'll know it's working when:
1. ✅ Minimal test completes in 7-8 seconds
2. ✅ 1000-word test completes in under 30 seconds
3. ✅ 4500-word test completes in under 60 seconds
4. ✅ All 6 steps log completion times
5. ✅ Full pipeline test succeeds end-to-end

---

## 🐛 Common Issues

### Issue: "OpenRouter API key required"
**Fix:** Check `.env` file has `OPENROUTER_API_KEY=sk-or-...`

### Issue: "No Brave API key - citation search will be limited"
**Fix:** Add `BRAVE_API_KEY=...` to `.env` (optional but recommended)

### Issue: Hangs at Step 1 forever
**Fix:** Reduce MAX_ANALYSIS_WORDS or use claude-haiku model

### Issue: Hangs at Step 2 (citations)
**Fix:** Reduce claims limit from 5 to 3

---

## 📞 Next Steps After Debugging

Once enrichment works reliably:

1. **Optimize WriterAgent Pass 2** - Integrate enrichment data
2. **Test full pipeline** - RESEARCHING → WRITING → ENRICHING → REVISING
3. **Add caching** - Cache Brave Search results
4. **Parallelize searches** - Make Brave calls async
5. **Monitor performance** - Track timing metrics

---

**Need help?** The logs will tell you exactly where it's hanging! 🔍
