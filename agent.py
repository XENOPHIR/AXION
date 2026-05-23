import os
import json
from openai import OpenAI
from rag import get_rag_engine

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEPARTMENTS = [
    "Digital Banking",
    "Card Operations",
    "Transfers & Payments",
    "Loans & Applications",
    "Customer Service / Branch Operations",
]

SYSTEM_PROMPT = """You are an AI customer support agent for AccessBank, one of Azerbaijan's leading banks.

IMPORTANT LANGUAGE RULE: Always respond in the same language the user writes in. If the user writes in Azerbaijani, respond in Azerbaijani. If in Russian, respond in Russian. If in English, respond in English. The response field in your JSON must follow this rule.

Your responsibilities:
1. Answer general AccessBank questions using the provided knowledge base context
2. Detect when a user is reporting a real problem that needs escalation
3. Collect necessary (but safe) information to create a support case
4. NEVER ask for: PIN, CVV, OTP, password, or full card number

Always respond to the customer in the same language they write in (Azerbaijani, Russian, or English).

You must respond in JSON format with this exact structure:
{
  "response": "Your message to the customer",
  "is_issue": true/false,
  "department": "Department name or null",
  "severity": "LOW/MEDIUM/HIGH/CRITICAL or null",
  "severity_reason": "Brief reason for severity or null",
  "needs_more_info": true/false,
  "missing_info": ["list of safe info still needed"] or [],
  "collected_info_summary": "Summary of what was collected or null",
  "sentiment": "neutral/frustrated/angry/calm",
  "ready_to_escalate": true/false
}

Severity guidelines:
- CRITICAL: Money lost, account blocked, security breach suspected
- HIGH: Failed transaction with deducted money, card blocked unexpectedly
- MEDIUM: Transfer delayed, app not working, card delivery delayed
- LOW: General complaints, questions about services, minor inconveniences

Department routing:
- Digital Banking: Mobile app, internet banking, login, OTP issues
- Card Operations: Card payments, blocked cards, lost/stolen card
- Transfers & Payments: Failed transfers, delayed payments, deducted amount
- Loans & Applications: Loan applications, loan status, repayment
- Customer Service / Branch Operations: General complaints, branch issues

Safe information to collect (ONLY these):
- Transaction amount (NOT card number)
- Date and time of issue
- Last 4 digits of card (NOT full number)
- Type of transaction (transfer, payment, etc.)
- Mobile app version (if relevant)
- Branch name (if relevant)

When ready_to_escalate is true, the system will automatically create a case and send an email."""


def classify_and_respond(
    user_message: str,
    conversation_history: list,
    user_id: str,
    username: str,
) -> dict:
    """
    Main agent function. Returns structured response with all metadata.
    """
    rag = get_rag_engine()
    context = rag.get_context(user_message)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\n\nKNOWLEDGE BASE CONTEXT:\n{context}",
        }
    ]

    # Add conversation history (last 10 messages for context)
    for msg in conversation_history[-10:]:
        messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    raw = response.choices[0].message.content

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "response": "I apologize, I encountered an issue. Please try again.",
            "is_issue": False,
            "department": None,
            "severity": None,
            "severity_reason": None,
            "needs_more_info": False,
            "missing_info": [],
            "collected_info_summary": None,
            "sentiment": "neutral",
            "ready_to_escalate": False,
        }

    return result


def generate_email_body(
    case_id: str,
    department: str,
    severity: str,
    issue_description: str,
    collected_info: str,
    conversation_history: list,
) -> str:
    """Use GPT to generate a professional escalation email body."""
    prompt = f"""Write a concise, professional escalation email for a banking support case.

Case ID: {case_id}
Department: {department}
Severity: {severity}
Issue: {issue_description}
Collected Info: {collected_info}

The email should be clear, professional, and include only what the department needs to act.
Do not include any sensitive banking credentials.
Keep it under 200 words."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content


def generate_case_summary(issue_description: str, department: str, severity: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": f"""Summarize this banking support issue in 2-3 short, clear sentences.
Be concise and professional. Focus on: what happened, what impact, what action needed.

Issue: {issue_description}
Department: {department}
Severity: {severity}

Respond with only the summary, no intro text."""
        }],
        temperature=0.2,
        max_tokens=120,
    )
    return response.choices[0].message.content.strip()
