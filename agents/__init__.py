# Cortex Agents Package — lazy loading to avoid circular imports
# Each agent is imported on first access rather than at package load time.
import sys
from pathlib import Path
# Ensure /app/tools can be imported (when running in container)
_tools_path = str(Path(__file__).parent.parent / "tools")
if _tools_path not in sys.path:
    sys.path.insert(0, _tools_path)

__all__ = [
    "cortex_agent",
    "memory_agent",
    "task_agent",
    "scheduler_agent",
    "email_agent",
]


def __getattr__(name):
    if name == "cortex_agent":
        from agents.cortex import cortex_agent
        globals()["cortex_agent"] = cortex_agent
        return cortex_agent
    if name == "memory_agent":
        from agents.memory import memory_agent
        globals()["memory_agent"] = memory_agent
        return memory_agent
    if name == "task_agent":
        from agents.task import task_agent
        globals()["task_agent"] = task_agent
        return task_agent
    if name == "scheduler_agent":
        from agents.scheduler import scheduler_agent
        globals()["scheduler_agent"] = scheduler_agent
        return scheduler_agent
    if name == "email_agent":
        from agents.email import email_agent
        globals()["email_agent"] = email_agent
        return email_agent
    raise AttributeError(f"module 'agents' has no attribute '{name}'")
