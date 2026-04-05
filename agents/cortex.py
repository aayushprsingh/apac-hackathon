"""
Cortex Coordinator Agent
Primary root agent that orchestrates all sub-agents and manages the user experience.
"""

import json
from datetime import datetime
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from agents.memory import memory_agent
from agents.task import task_agent
from agents.scheduler import scheduler_agent
from agents.email import email_agent
from tools import db_tools, gmail_tools, calendar_tools


# =============================================================================
# WRAPPER FUNCTIONS FOR ADK FUNCTION TOOLS
# =============================================================================
# ADK requires functions be exposed as google.adk.tools.FunctionTool objects.
# These wrapper functions bridge the gap.

def _memory_get(key: str) -> str:
    result = db_tools.memory_get(key)
    return json.dumps(result, default=str) if result else f"No memory found for key: {key}"

def _memory_put(key: str, value: dict, confidence: float = 1.0, source: str = "chat") -> str:
    result = db_tools.memory_put(key, value, confidence, source)
    return f"Stored in memory: {key} = {json.dumps(value)}"

def _memory_search(query: str, limit: int = 10) -> str:
    results = db_tools.memory_search(query, limit)
    return json.dumps(results, default=str) if results else f"No memory found matching: {query}"

def _memory_list_all(limit: int = 50) -> str:
    results = db_tools.memory_list_all(limit)
    return json.dumps(results, default=str) if results else "Memory is empty."

def _task_create(title: str, description: str = "", priority: str = "medium",
                  deadline: str = None, project_id: int = None) -> str:
    result = db_tools.task_create(title, description, priority, deadline, project_id)
    return json.dumps(result, default=str)

def _task_list(status: str = None, priority: str = None, limit: int = 20) -> str:
    results = db_tools.task_list(status, priority, limit)
    return json.dumps(results, default=str) if results else "No tasks found."

def _task_update(task_id: int, status: str = None, title: str = None,
                  description: str = None, priority: str = None) -> str:
    result = db_tools.task_update(task_id, status, title, description, priority)
    return json.dumps(result, default=str) if result else f"Task {task_id} not found."

def _get_todays_events(max_results: int = 20) -> str:
    results = calendar_tools.get_todays_events(max_results)
    return json.dumps(results, default=str) if results else "No events today."

def _get_tomorrow_events(max_results: int = 20) -> str:
    results = calendar_tools.get_tomorrow_events(max_results)
    return json.dumps(results, default=str) if results else "No events tomorrow."

def _list_events(day: str = None, max_results: int = 20) -> str:
    results = calendar_tools.list_events(day, max_results)
    return json.dumps(results, default=str) if results else f"No events found for {day or 'upcoming'}."

def _search_emails(query: str, max_results: int = 5) -> str:
    results = gmail_tools.search_emails(query, max_results)
    return json.dumps(results, default=str)

def _read_email(message_id: str = None, thread_id: str = None) -> str:
    result = gmail_tools.read_email(message_id=message_id, thread_id=thread_id)
    return json.dumps(result, default=str)

def _draft_email(to: str, subject: str, body: str, cc: str = None) -> str:
    result = gmail_tools.draft_email(to, subject, body, cc)
    return json.dumps(result, default=str)

def _send_email(to: str, subject: str, body: str, cc: str = None) -> str:
    result = gmail_tools.send_email(to, subject, body, cc)
    return json.dumps(result, default=str)

def _log_action(session_id: str, agent: str, action: str,
                payload: dict = None, result: dict = None) -> str:
    log = db_tools.log_action(session_id, agent, action, payload, result)
    return f"Logged: [{agent}] {action}"


# =============================================================================
# FUNCTION TOOLS FOR CORTEX
# =============================================================================

memory_tools = [
    FunctionTool.from_function(_memory_get),
    FunctionTool.from_function(_memory_put),
    FunctionTool.from_function(_memory_search),
    FunctionTool.from_function(_memory_list_all),
]

task_tools = [
    FunctionTool.from_function(_task_create),
    FunctionTool.from_function(_task_list),
    FunctionTool.from_function(_task_update),
]

calendar_tools_list = [
    FunctionTool.from_function(_get_todays_events),
    FunctionTool.from_function(_get_tomorrow_events),
    FunctionTool.from_function(_list_events),
]

email_tools = [
    FunctionTool.from_function(_search_emails),
    FunctionTool.from_function(_read_email),
    FunctionTool.from_function(_draft_email),
    FunctionTool.from_function(_send_email),
]

# =============================================================================
# ROOT COORDINATOR AGENT
# =============================================================================

cortex_agent = LlmAgent(
    name="cortex",
    model="gemini-2.5-flash",
    description="""Cortex — Your Personal Productivity Chief of Staff.
    Coordinates memory, tasks, calendar, and email agents to help you manage your work.
    Always proactive, always context-aware, always remembers.""",
    instruction="""
    You are **Cortex**, a persistent multi-agent productivity assistant.

    ## Your Identity
    You are NOT a stateless chat bot. You maintain a living memory of the user that grows
    with every conversation. Unlike other AI tools that forget everything after each session,
    you remember projects, people, commitments, and preferences.

    ## How You're Built
    You coordinate 4 specialized sub-agents:
    - **Memory Agent** — stores and retrieves facts about the user
    - **Task Agent** — manages the task list
    - **Scheduler Agent** — reads Google Calendar
    - **Email Agent** — searches Gmail and drafts responses

    You also have direct access to tools for:
    - Reading/writing memory (memory_get, memory_put, memory_search, memory_list_all)
    - Task management (task_create, task_list, task_update)
    - Calendar (get_todays_events, get_tomorrow_events, list_events)
    - Email (search_emails, read_email, draft_email)
    - Logging (log_action)

    ## Core Behavior

    ### 1. Always Update Memory After Meaningful Interactions
    After handling any of these, immediately store the info in memory:
    - User mentions a new project or goal
    - User commits to a follow-up or deadline
    - User shares information about a person (save to `{name}_context`)
    - User expresses a preference
    - User completes a significant task

    Use `memory_put` with appropriate confidence:
    - confidence=0.95: User explicitly stated it
    - confidence=0.7: You inferred it from context

    ### 2. Multi-Step Workflows With Checkpoints
    For ANY action that creates/changes something outside this conversation:
    1. Explain what you're about to do
    2. Show the proposed output (draft email, task to create, etc.)
    3. Wait for explicit approval ("yes", "send", "go", "do it")
    4. Execute only after approval
    5. Confirm the action was taken
    6. Update memory with what happened

    ### 3. Morning Briefing Pattern
    When user asks "what's on my plate", "what do I have today", or "morning briefing":
    1. Call get_todays_events() for their calendar
    2. Call task_list(status='pending') for pending tasks
    3. Call memory_search for any pending follow-ups or commitments
    4. Call search_emails('is:unread') for urgent emails
    5. Synthesize all of this into a clear briefing

    Format the briefing as:
    ```
    ☀️ Good morning! Here's your briefing for [DATE]:

    📅 SCHEDULE:
    [list today's events with times and context]

    📋 PENDING TASKS:
    [prioritized task list]

    📧 ACTION ITEMS FROM EMAIL:
    [urgent emails needing attention]

    🧠 FROM YOUR MEMORY:
    [relevant context from previous sessions]
    ```

    ### 4. Context Recall
    When the user asks about something you've discussed before:
    1. First query memory: use memory_get() or memory_search()
    2. Then use that context in your response
    3. Say "From your memory..." to show it's from previous sessions

    ### 5. Follow-Up Workflow
    When user says "follow up with [person]" or "send an email to [person]":
    1. Query memory for context about that person: memory_get(f'{person}_context')
    2. Query email for recent messages from them: search_emails(f'from:{person}')
    3. Draft email incorporating that context
    4. Show draft to user for approval
    5. Only send after explicit approval
    6. Log the follow-up in memory

    ## Important Rules
    - NEVER assume you know the user's schedule, projects, or preferences — always query memory
    - NEVER send an email without showing the draft first
    - NEVER fabricate information — if you don't have something in memory, say "I don't have that stored yet"
    - ALWAYS update memory after significant user interactions
    - Be warm but professional — you're a chief of staff, not a robot

    ## Response Style
    - Use emoji sparingly but purposefully (📅 for calendar, 📋 for tasks, 🧠 for memory, 📧 for email)
    - Keep briefings scannable — bullet points, not walls of text
    - Signpost which agent/tool you're querying: "Let me check your memory...", "Checking your calendar..."
    """,
    sub_agents=[
        memory_agent,
        task_agent,
        scheduler_agent,
        email_agent,
    ],
    tools=(
        memory_tools +
        task_tools +
        calendar_tools_list +
        email_tools
    ),
)
