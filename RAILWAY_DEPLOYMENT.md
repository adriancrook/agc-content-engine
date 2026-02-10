# Railway Deployment Guide

**Status:** Ready to Deploy ✅
**Date:** February 10, 2026

---

## 🚀 What's Been Pushed

All WordPress publishing workflow code has been pushed to GitHub:

- ✅ Internal Linking integration
- ✅ WordPress Formatter with SEO metadata
- ✅ Export UI with Copy/Download buttons
- ✅ Database migration (auto-runs on startup)
- ✅ PostgreSQL support for Railway

**Total Commits:** 8 new commits pushed
**Latest Commit:** `fe421f1` - PostgreSQL migration support

---

## 📋 Railway Deployment Checklist

### 1. **Check Railway Dashboard**

Go to: https://railway.app/dashboard

Your project should already be linked to the GitHub repo. Railway will automatically:
- Detect the new commits
- Trigger a new deployment
- Run the build process

### 2. **Environment Variables**

Make sure these are set in Railway:

**Required:**
- `USE_REAL_AGENTS=true` (enables real LLMs)
- `OPENROUTER_API_KEY=xxx` (for Claude)
- `BRAVE_API_KEY=xxx` (for research/search)
- `GOOGLE_API_KEY=xxx` (for Gemini image generation)

**Auto-provided by Railway:**
- `DATABASE_URL` (PostgreSQL - automatically set)
- `PORT` (automatically set)

### 3. **Check Deployment Status**

1. Click on your project in Railway
2. Go to "Deployments" tab
3. Watch the build logs
4. Look for these success messages:
   ```
   🔄 Running database migrations...
   ✅ Migration complete!
   🚀 Starting server...
   ✓ Agents ready: Research + Writer + ... + WordPress
   ✅ Server ready!
   ```

### 4. **Verify Database Migration**

The migration script will automatically run on startup via `start.sh`:

```bash
python3 migrate_add_wordpress_columns.py
```

This adds 4 new columns to `articles_v2` table:
- `wordpress_content`
- `wordpress_metadata`
- `wordpress_export_ready`
- `wordpress_validation_issues`

**If migration fails:** It's safe - the script is idempotent (can run multiple times).

### 5. **Test the Deployment**

Once deployed, visit your Railway URL (e.g., `your-app.up.railway.app`):

1. **Check Dashboard:**
   - Should load normally
   - Shows existing articles

2. **Create Test Article:**
   - Create a new topic
   - Approve it
   - Watch pipeline progress

3. **Wait for "Ready" State:**
   - Takes 5-10 minutes
   - Monitor via dashboard

4. **Test Export:**
   - Open article detail page
   - Should see WordPress Export section
   - Click "Copy for WordPress"
   - Should copy to clipboard

---

## 🔧 What Railway Will Do

### Build Process:

1. **Detect Changes:**
   - Railway monitors your GitHub repo
   - Detects new commits automatically

2. **Pull Code:**
   - Pulls latest code from `main` branch
   - Includes all WordPress workflow files

3. **Install Dependencies:**
   - Runs nixpacks builder
   - Installs Python dependencies from `requirements.txt`

4. **Run Migrations:**
   - Executes `start.sh`
   - Runs `migrate_add_wordpress_columns.py`
   - Adds WordPress columns to PostgreSQL

5. **Start Server:**
   - Starts uvicorn on PORT
   - Initializes all agents
   - State machine begins processing

### Expected Deployment Time: 2-3 minutes

---

## 📦 New Dependencies

The migration script requires `psycopg2` for PostgreSQL. Make sure it's in `requirements.txt`:

```txt
psycopg2-binary>=2.9.0
```

**Check if needed:**
```bash
grep psycopg2 v2/requirements.txt
```

If missing, add it and push:
```bash
echo "psycopg2-binary>=2.9.0" >> v2/requirements.txt
git add v2/requirements.txt
git commit -m "Add psycopg2 for PostgreSQL support"
git push
```

---

## 🐛 Troubleshooting

### Issue: Migration Fails

**Symptom:** Build logs show migration error

**Solution:**
1. Check DATABASE_URL is set in Railway
2. Check PostgreSQL database is provisioned
3. Migration script is idempotent - safe to redeploy

### Issue: WordPress Section Not Showing

**Possible Causes:**
1. Article not in "ready" state yet
2. Database columns not created
3. Old articles (created before this update)

**Solution:**
- Create a NEW article to test
- Old articles won't have WordPress data (need re-generation)

### Issue: Copy Button Not Working

**Check:**
1. Browser supports Clipboard API (HTTPS required)
2. Railway URL is HTTPS (should be by default)
3. Check browser console for errors

### Issue: Build Fails

**Common Causes:**
1. Missing dependencies in requirements.txt
2. Syntax errors (shouldn't happen - we tested locally)
3. Railway resource limits

**Check Build Logs:**
- Go to Railway → Deployments → Click latest
- Read error messages
- Fix and push again

---

## ✅ Success Indicators

You'll know deployment worked if:

1. **Build Completes:** ✅ Green checkmark in Railway
2. **Migration Runs:** Logs show "Migration complete!"
3. **Server Starts:** Logs show "Server ready!"
4. **UI Loads:** Dashboard accessible at Railway URL
5. **Agents Work:** Can create and complete articles
6. **Export Works:** WordPress section appears on ready articles

---

## 🎯 Post-Deployment Testing

### Quick Test (5 minutes):

1. Visit Railway URL
2. Create topic: "Mobile Game Analytics 2025"
3. Approve topic
4. Wait for "ready" state (~5-10 min)
5. Click article → See export section
6. Click "Copy for WordPress"
7. Success! ✅

### Full Test (30 minutes):

1. Generate 3 different articles
2. Test all export buttons
3. Verify metadata quality
4. Check internal links work
5. Download markdown files
6. Actually paste into WordPress (optional)

---

## 📊 Monitoring

### Railway Metrics to Watch:

1. **Build Time:** Should be 2-3 minutes
2. **Memory Usage:** Should be normal (no increase expected)
3. **API Costs:** Track OpenRouter/Google usage
4. **Response Times:** Should be <1s for UI, longer for generation

### Database:

- PostgreSQL on Railway
- Auto-backups enabled
- Check size growth (should be minimal)

---

## 🔄 Rollback Plan

If something goes wrong:

### Option 1: Revert in Railway
1. Go to Deployments
2. Click previous deployment
3. Click "Redeploy"

### Option 2: Revert in Git
```bash
git revert fe421f1  # Revert migration commit
git revert 23b41fc  # Revert WordPress workflow
git push
```

### Option 3: Manual Fix
1. Connect to Railway database
2. Drop WordPress columns manually:
   ```sql
   ALTER TABLE articles_v2 DROP COLUMN wordpress_content;
   ALTER TABLE articles_v2 DROP COLUMN wordpress_metadata;
   ALTER TABLE articles_v2 DROP COLUMN wordpress_export_ready;
   ALTER TABLE articles_v2 DROP COLUMN wordpress_validation_issues;
   ```

---

## 🎉 Deployment Complete!

Once deployed successfully:

1. ✅ All existing features still work
2. ✅ New WordPress workflow available
3. ✅ Database migrated automatically
4. ✅ Zero downtime (Railway handles this)
5. ✅ Ready to generate WordPress-ready articles!

---

## 📝 Next Steps After Deployment

1. **Generate Test Article**
   - Create topic via Railway UI
   - Wait for completion
   - Test export functionality

2. **Update Documentation**
   - Share Railway URL with team
   - Document export workflow
   - Create user guide

3. **Start Production**
   - Generate real articles
   - Export to WordPress
   - Publish and celebrate! 🎉

---

## 🔗 Quick Links

- **GitHub Repo:** https://github.com/adriancrook/agc-content-engine
- **Railway Dashboard:** https://railway.app/dashboard
- **Latest Commits:** Check Railway deployments tab

---

## 📞 Need Help?

**Check These:**
1. Railway build logs
2. Server logs in Railway dashboard
3. Browser console (F12) for UI issues
4. Database status in Railway

**Common Commands:**
```bash
# Check Railway status
railway status

# View logs
railway logs

# Open Railway dashboard
railway open
```

---

## ✨ What's New on Railway

After this deployment, your Railway app will have:

**New Pipeline States:**
- INTERNAL_LINKING (adds 2-5 internal links)
- WORDPRESS_FORMATTING (generates SEO metadata)

**New API Endpoint:**
- `GET /articles/{id}/wordpress` (export endpoint)

**New UI Features:**
- WordPress Export section
- Copy/Download buttons
- Quality checklist
- Metadata viewer

**New Database Columns:**
- wordpress_content
- wordpress_metadata
- wordpress_export_ready
- wordpress_validation_issues

**Cost Impact:**
- $0 additional per article! 🎉

---

**Deployment Status:** ✅ READY
**Estimated Deploy Time:** 2-3 minutes
**Risk Level:** Low (backward compatible, auto-migration)
**Rollback Available:** Yes

---

*Ready to deploy! Railway will handle everything automatically.* 🚀
