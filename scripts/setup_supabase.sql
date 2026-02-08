-- AGC Content Engine Database Schema
-- Run this in Supabase SQL editor

-- Topics queue
CREATE TABLE IF NOT EXISTS topics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    keyword TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'declined', 'processing', 'completed')),
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    article_id UUID REFERENCES articles(id)
);

-- Articles
CREATE TABLE IF NOT EXISTS articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    topic_id UUID REFERENCES topics(id),
    title TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'researching', 'writing', 'fact_checking', 'seo', 'humanizing', 'review', 'approved', 'published', 'failed')),
    stage TEXT DEFAULT 'research',
    research_data JSONB,
    draft_content TEXT,
    final_content TEXT,
    seo_meta JSONB,
    media JSONB,
    ai_score FLOAT,
    word_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- Task queue for worker
CREATE TABLE IF NOT EXISTS tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    result JSONB,
    article_id UUID REFERENCES articles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT
);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default settings
INSERT INTO settings (key, value) VALUES 
('topic_generation', '{"max_pending": 20, "auto_generate": true, "focus_areas": ["mobile game monetization", "freemium game design", "game economy modeling"]}'),
('pipeline', '{"auto_process_approved": true, "require_human_review": true}')
ON CONFLICT (key) DO NOTHING;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);

-- RLS policies (enable row level security)
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (adjust as needed)
CREATE POLICY "Allow all for anon" ON topics FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON articles FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON tasks FOR ALL USING (true);
CREATE POLICY "Allow all for anon" ON settings FOR ALL USING (true);
