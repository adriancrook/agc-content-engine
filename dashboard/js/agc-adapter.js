// ========================================
// AGC CONTENT ENGINE ADAPTER
// Transforms AGC API data to Moltcraft format
// ========================================

class AGCAdapter {
    constructor(apiUrl) {
        this.apiUrl = apiUrl || 'https://agc-content-engine-production.up.railway.app';
        this.agents = [
            { id: 'topic-discovery', name: 'TopicBot', emoji: '💡', color: '#FFD700' },
            { id: 'research', name: 'ResearchBot', emoji: '🔍', color: '#4A90D9' },
            { id: 'writer', name: 'WriterBot', emoji: '✍️', color: '#9B59B6' },
            { id: 'fact-checker', name: 'FactBot', emoji: '✅', color: '#27AE60' },
            { id: 'seo', name: 'SEOBot', emoji: '📊', color: '#E67E22' },
            { id: 'humanizer', name: 'HumanBot', emoji: '🎭', color: '#E74C3C' }
        ];
        this.currentTasks = [];
        this.topics = [];
        this.stats = {
            localCalls: 0,
            cloudCalls: 0,
            totalTokens: 0,
            costSaved: 0
        };
    }

    async fetchAll() {
        try {
            const [tasks, topics] = await Promise.all([
                this.fetchTasks(),
                this.fetchTopics()
            ]);
            return { tasks, topics, agents: this.buildAgentSessions() };
        } catch (error) {
            console.error('AGC fetch error:', error);
            return { tasks: [], topics: [], agents: [] };
        }
    }

    async fetchTasks() {
        try {
            const res = await fetch(`${this.apiUrl}/api/tasks/active`);
            const activeTasks = await res.json();
            this.currentTasks = activeTasks;
            return this.currentTasks;
        } catch (e) {
            console.error('Failed to fetch tasks:', e);
            return [];
        }
    }

    async fetchTopics() {
        try {
            const res = await fetch(`${this.apiUrl}/api/topics`);
            this.topics = await res.json();
            return this.topics;
        } catch (e) {
            console.error('Failed to fetch topics:', e);
            return [];
        }
    }

    // Transform AGC data to Moltcraft session format
    buildAgentSessions() {
        const sessions = [];
        
        // Map task types to agent IDs
        const taskTypeMap = {
            'generate_topics': 'topic-discovery',
            'research': 'research',
            'write': 'writer',
            'fact_check': 'fact-checker',
            'seo': 'seo',
            'humanize': 'humanizer'
        };
        
        // Create a session for each agent type
        this.agents.forEach((agent) => {
            // Find active task for this agent type
            const matchingTaskTypes = Object.entries(taskTypeMap)
                .filter(([_, id]) => id === agent.id)
                .map(([type]) => type);
            
            const activeTask = this.currentTasks.find(t => 
                matchingTaskTypes.includes(t.type) && t.status === 'processing'
            );
            
            // Find pending tasks for this agent
            const pendingTasks = this.currentTasks.filter(t => 
                matchingTaskTypes.includes(t.type) && t.status === 'pending'
            );

            let state = 'idle';
            let lastMessage = 'Waiting for tasks...';
            
            if (activeTask) {
                state = 'working';
                const topic = activeTask.payload?.topic || activeTask.type;
                lastMessage = `Processing: ${topic.substring(0, 50)}...`;
            } else if (pendingTasks.length > 0) {
                state = 'waiting';
                lastMessage = `${pendingTasks.length} task(s) in queue`;
            }

            sessions.push({
                sessionId: agent.id,
                key: agent.id,
                label: agent.name,
                emoji: agent.emoji,
                color: agent.color,
                state: state,
                isLocal: ['topic-discovery', 'research', 'writer', 'fact-checker', 'seo'].includes(agent.id),
                model: ['topic-discovery', 'research', 'writer', 'fact-checker', 'seo'].includes(agent.id) 
                    ? 'qwen2.5:14b (LOCAL)' 
                    : 'claude-sonnet (CLOUD)',
                stats: {
                    totalTokens: 0,
                    tasksCompleted: 0,
                    tasksInQueue: pendingTasks.length
                },
                lastActivity: activeTask?.updated_at || new Date().toISOString(),
                messages: [{
                    role: 'assistant',
                    content: lastMessage,
                    timestamp: new Date().toISOString()
                }],
                activeTask: activeTask,
                pendingCount: pendingTasks.length
            });
        });

        return sessions;
    }

    // Get summary stats for the dashboard
    getStats() {
        const processing = this.topics.filter(t => t.status === 'processing').length;
        const pending = this.topics.filter(t => t.status === 'pending').length;
        const completed = this.topics.filter(t => t.status === 'completed').length;
        
        return {
            topicsTotal: this.topics.length,
            topicsProcessing: processing,
            topicsPending: pending,
            topicsCompleted: completed,
            tasksInFlight: this.currentTasks.filter(t => t.status === 'processing').length,
            localProcessing: 5,
            cloudProcessing: 1,
            estimatedCostSaved: completed * 2.50
        };
    }
}

// Export for use in app.js
window.AGCAdapter = AGCAdapter;
