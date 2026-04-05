-- Cortex Seed Data
-- Sample data for demo purposes — hackathon presentation

-- ============================================================================
-- MEMORY: User Context (makes the demo impressive)
-- ============================================================================

INSERT INTO user_model (key, value, confidence, source) VALUES
(
    'rahul_context',
    '{"name": "Rahul Sharma", "relationship": "investor", "topic": "15% equity for ₹50L", "last_contact": "2026-04-03", "status": "waiting_on_rahul", "notes": "Rahul said he would revert within 3 days — deadline was April 1, now overdue"}',
    0.95,
    'chat'
),
(
    'current_project',
    '{"name": "Bhooyam Ankuran Jal", "type": "AI-powered hydroponic system", "stage": "pre-launch", "priority": "high", "deadline": "2026-04-15"}',
    0.95,
    'chat'
),
(
    'pending_followups',
    '{"items": [{"who": "Rahul", "topic": "investment terms", "due": "2026-04-05"}, {"who": "design team", "topic": "logo sign-off", "due": "2026-04-07"}]}',
    0.9,
    'chat'
),
(
    'user_preferences',
    '{"briefing_style": "concise with detail", "working_hours": "9am-8pm IST", "communication": "direct and brief", "priority_focus": "Bhooyam"}',
    0.9,
    'explicit'
),
(
    'q1_goals',
    '{"goals": ["Launch Ankuran Jal MVP", "Close Rahul investment", "Complete GCP hackathon", "Build 3 freelance clients"], "status": "in_progress"}',
    0.9,
    'chat'
),
(
    'weekly_goals',
    '{"week_of": "2026-04-05", "focus": ["GCP hackathon submission", "Rahul follow-up", "Bhooyam prototype testing"], "energy_level": "medium"}',
    0.85,
    'chat'
)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- PROJECTS
-- ============================================================================

INSERT INTO projects (name, description, status, deadline) VALUES
('Bhooyam Ankuran Jal', 'AI-powered autonomous hydroponic system for home food production', 'active', '2026-04-15'),
('GCP Gen AI Hackathon', 'Cohort 1 hackathon — multi-agent productivity assistant', 'active', '2026-04-08'),
('India Stock Autopilot', 'Telegram bot for Indian stock market monitoring', 'active', '2026-04-10')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- TASKS
-- ============================================================================

INSERT INTO tasks (title, description, status, priority, deadline) VALUES
('Follow up with Rahul on investment terms', '15% equity for ₹50L — 3 day deadline passed, need to follow up', 'pending', 'urgent', '2026-04-05 18:00:00+05:30'),
('Submit GCP Hackathon project', 'Deploy Cortex to Cloud Run, create demo video and slides', 'pending', 'high', '2026-04-08 23:59:00+05:30'),
('Review Bhooyam logo design', 'Design team sent mockups, need sign-off', 'pending', 'high', '2026-04-07 17:00:00+05:30'),
('Test hydroponic prototype', 'Run nutrient flow test on Jal prototype', 'pending', 'medium', '2026-04-10 10:00:00+05:30'),
('Write freelance proposal for client X', 'Website automation project — $500 estimate', 'pending', 'medium', '2026-04-06 12:00:00+05:30'),
('Complete hackathon codelabs Track 2', 'MCP tools codelab — Travel Assistant', 'in_progress', 'medium', '2026-04-06 20:00:00+05:30'),
('Update MEMORY.md with hackathon progress', 'Document Track 1 submission, remaining tasks', 'done', 'low', '2026-04-02 22:00:00+05:30');
