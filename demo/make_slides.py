"""
Cortex 3-Slide PDF Presentation Generator
Using reportlab via uv
"""
import os

slides = [
    {
        "title": "Cortex - Personal Productivity Assistant",
        "subtitle": "Google Cloud Gen AI Academy APAC 2026 | Cohort 1 Hackathon",
        "lines": [
            "THE PROBLEM: Every AI tool is stateless - close the chat, it forgets everything",
            "THE SOLUTION: A persistent multi-agent chief of staff that remembers you",
            "",
            "Key Differentiator:",
            "  * Persistent memory layer - stores facts, preferences, relationships",
            "  * Multi-agent coordination - 1 user message -> 5 agents working together",
            "  * Checkpoint workflows - drafts shown for approval before any action",
            "  * Proactive context assembly - does not wait to be asked",
            "",
            "Tech Stack: Google ADK | Gemini 2.5 Flash | PostgreSQL (Cloud SQL)",
            "            Gmail API | Google Calendar API | Flask | Cloud Run",
        ],
        "footer": "Aayush Pratap Singh | Bhooyam Agritech Pvt. Ltd."
    },
    {
        "title": "Architecture - 5-Agent Multi-Agent System",
        "subtitle": "",
        "lines": [
            "                         CORTEX COORDINATOR (Root LlmAgent)",
            "                    Orchestrates | Coordinates | Synthesizes",
            "                    ------------------------------------------",
            "          +------------------+-------------------+",
            "          |                  |                   |",
            "    Memory Agent      Task Agent        Scheduler Agent",
            "    (PostgreSQL)      (PostgreSQL)       (Calendar API)",
            "          |                  |                   |",
            "          +---------- Email Agent ---------------+",
            "                   (Gmail API)",
            "                    |",
            "          PostgreSQL (Cloud SQL) <- Persistent Memory Model",
            "",
            "Primary Agent: Cortex Coordinator (LlmAgent)",
            "Sub-Agents: Memory | Task | Scheduler | Email",
            "Data Layer: PostgreSQL - user_model, tasks, projects, sessions, action_log",
        ],
        "footer": "Multi-Agent AI System | Google ADK + Gemini 2.5 Flash"
    },
    {
        "title": "Submission Summary",
        "subtitle": "Cohort 1 Hackathon | April 5, 2026",
        "lines": [
            "PROJECT: Cortex - Persistent Multi-Agent Productivity Assistant",
            "BUILT WITH: Google ADK | Gemini 2.5 Flash | PostgreSQL | Gmail API | Calendar API",
            "",
            "REQUIREMENTS MET:",
            "  [X] Primary root agent (Cortex) + 4 sub-agents",
            "  [X] Persistent structured data storage (PostgreSQL user_model)",
            "  [X] Multiple tool integrations (Gmail + Calendar REST APIs)",
            "  [X] Multi-step workflow with human-in-the-loop checkpoint",
            "  [X] REST API deployed on Google Cloud Run",
            "",
            "SUBMISSION URL: https://cortex-agent-[REGION].run.app",
            "GITHUB: https://github.com/aayushprsingh/apac-hackathon",
            "",
            "DEMO HIGHLIGHT: The system remembers context from previous sessions",
            "  - e.g. 'waiting on Rahul for 4 days' - verified via live PostgreSQL",
        ],
        "footer": "Aayush Pratap Singh | Bhooyam Agritech Pvt. Ltd. | github.com/aayushprsingh"
    }
]

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

pdf_path = os.path.join(os.path.dirname(__file__), "Cortex_Presentation.pdf")
c = canvas.Canvas(pdf_path, pagesize=landscape(A4))
width, height = landscape(A4)

for slide in slides:
    # Background
    c.setFillColor(HexColor('#0f1117'))
    c.rect(0, 0, width, height, fill=True)

    # Title
    c.setFillColor(HexColor('#667eea'))
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width/2, height - 70, slide['title'])

    # Subtitle
    if slide['subtitle']:
        c.setFillColor(HexColor('#9ca3af'))
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 95, slide['subtitle'])

    # Content
    c.setFillColor(HexColor('#e5e7eb'))
    y = height - 140
    for line in slide['lines']:
        if line.startswith("  ") or line.startswith("   ") or line.startswith("|"):
            c.setFont("Courier", 10)
        elif line.startswith("  -") or line.startswith("  ["):
            c.setFont("Helvetica", 11)
        elif line.isupper() and len(line) < 40:
            c.setFillColor(HexColor('#f97316'))
            c.setFont("Helvetica-Bold", 13)
        else:
            c.setFillColor(HexColor('#e5e7eb'))
            c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, y, line)
        y -= 22
        if y < 70:
            break

    # Footer
    c.setFillColor(HexColor('#6b7280'))
    c.setFont("Helvetica", 9)
    c.drawCentredString(width/2, 25, slide['footer'])

    c.showPage()

c.save()
print(f"PDF created: {pdf_path}")
