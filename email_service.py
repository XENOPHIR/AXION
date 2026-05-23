import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

DEPARTMENT_EMAILS = {
    "Digital Banking": os.getenv("EMAIL_DIGITAL_BANKING", "accessbank.digital@yopmail.com"),
    "Card Operations": os.getenv("EMAIL_CARD_OPERATIONS", "accessbank.cards@yopmail.com"),
    "Transfers & Payments": os.getenv("EMAIL_TRANSFERS", "accessbank.transfers@yopmail.com"),
    "Loans & Applications": os.getenv("EMAIL_LOANS", "accessbank.loans@yopmail.com"),
    "Customer Service / Branch Operations": os.getenv("EMAIL_CUSTOMER_SERVICE", "accessbank.support@yopmail.com"),
}

SEVERITY_COLORS = {
    "LOW":      {"bg": "#e8f5e9", "border": "#4caf50", "badge": "#4caf50", "emoji": "🟢"},
    "MEDIUM":   {"bg": "#fff8e1", "border": "#ff9800", "badge": "#ff9800", "emoji": "🟡"},
    "HIGH":     {"bg": "#fff3e0", "border": "#f44336", "badge": "#f44336", "emoji": "🟠"},
    "CRITICAL": {"bg": "#ffebee", "border": "#b71c1c", "badge": "#b71c1c", "emoji": "🔴"},
}

SLA_TIMES = {
    "LOW": "72 hours",
    "MEDIUM": "24 hours",
    "HIGH": "4 hours",
    "CRITICAL": "1 hour",
}


def build_html_email(case_id, department, severity, issue_description, collected_info, username, ai_summary=""):
    now = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
    colors = SEVERITY_COLORS.get(severity, SEVERITY_COLORS["MEDIUM"])
    sla = SLA_TIMES.get(severity, "24 hours")
    emoji = colors["emoji"]

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AccessBank Support Escalation</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg,#1a237e 0%,#0d47a1 100%);padding:32px 40px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <div style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:1px;">
              🏦 AXION
            </div>
            <div style="font-size:13px;color:#90caf9;margin-top:4px;">
              Intelligent Banking Support System
            </div>
          </td>
          <td align="right">
            <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 16px;display:inline-block;">
              <div style="font-size:11px;color:#90caf9;text-transform:uppercase;letter-spacing:1px;">Case ID</div>
              <div style="font-size:18px;font-weight:700;color:#ffffff;font-family:monospace;">{case_id}</div>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SEVERITY BANNER -->
  <tr>
    <td style="background:{colors['bg']};border-left:5px solid {colors['border']};padding:16px 40px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <span style="font-size:13px;color:#555;text-transform:uppercase;letter-spacing:1px;font-weight:600;">
              Severity Level
            </span>
            <br>
            <span style="font-size:24px;font-weight:700;color:{colors['border']};">
              {emoji} {severity}
            </span>
          </td>
          <td align="right">
            <div style="background:{colors['badge']};color:#fff;border-radius:20px;padding:6px 18px;font-size:13px;font-weight:600;">
              SLA: Respond within {sla}
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- MAIN CONTENT -->
  <tr>
    <td style="padding:32px 40px;">

      <!-- META INFO -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border-radius:8px;padding:20px;margin-bottom:24px;">
        <tr>
          <td width="50%" style="padding:6px 0;">
            <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:1px;">Department</div>
            <div style="font-size:15px;font-weight:600;color:#1a237e;margin-top:2px;">🏢 {department}</div>
          </td>
          <td width="50%" style="padding:6px 0;">
            <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:1px;">Customer</div>
            <div style="font-size:15px;font-weight:600;color:#333;margin-top:2px;">👤 @{username}</div>
          </td>
        </tr>
        <tr>
          <td width="50%" style="padding:6px 0;">
            <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:1px;">Timestamp</div>
            <div style="font-size:14px;color:#333;margin-top:2px;">🕐 {now}</div>
          </td>
          <td width="50%" style="padding:6px 0;">
            <div style="font-size:11px;color:#999;text-transform:uppercase;letter-spacing:1px;">Status</div>
            <div style="font-size:14px;color:#f57c00;font-weight:600;margin-top:2px;">⏳ Awaiting Action</div>
          </td>
        </tr>
      </table>

      <!-- AI SUMMARY -->
      <div style="margin-bottom:24px;">
        <div style="font-size:13px;font-weight:700;color:#1a237e;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #e3e8f0;">
          🧠 AI Summary
        </div>
        <div style="font-size:15px;color:#333;line-height:1.7;background:#e8eaf6;border-radius:8px;padding:16px;border-left:3px solid #3949ab;font-style:italic;">
          {ai_summary}
        </div>
      </div>

      <!-- ISSUE DESCRIPTION -->
      <div style="margin-bottom:24px;">
        <div style="font-size:13px;font-weight:700;color:#1a237e;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #e3e8f0;">
          📋 Issue Description
        </div>
        <div style="font-size:15px;color:#333;line-height:1.7;background:#f8fafc;border-radius:8px;padding:16px;border-left:3px solid #1a237e;">
          {issue_description}
        </div>
      </div>

      <!-- COLLECTED DETAILS -->
      <div style="margin-bottom:24px;">
        <div style="font-size:13px;font-weight:700;color:#1a237e;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;padding-bottom:8px;border-bottom:2px solid #e3e8f0;">
          📌 Collected Details
        </div>
        <div style="font-size:15px;color:#333;line-height:1.7;background:#f8fafc;border-radius:8px;padding:16px;">
          {collected_info}
        </div>
      </div>

      <!-- ACTION REQUIRED -->
      <div style="background:linear-gradient(135deg,#1a237e,#0d47a1);border-radius:10px;padding:20px 24px;margin-bottom:24px;">
        <div style="font-size:13px;font-weight:700;color:#90caf9;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
          ⚡ Action Required
        </div>
        <div style="font-size:15px;color:#ffffff;line-height:1.6;">
          Please review this case and respond within <strong style="color:#ffd54f;">{sla}</strong>.<br>
          Reply to this email to update the case status automatically.
        </div>
      </div>

      <!-- SLA TABLE -->
      <table width="100%" cellpadding="0" cellspacing="0" style="border-radius:8px;overflow:hidden;border:1px solid #e3e8f0;margin-bottom:24px;">
        <tr style="background:#f8fafc;">
          <td style="padding:10px 16px;font-size:12px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:1px;">Severity</td>
          <td style="padding:10px 16px;font-size:12px;font-weight:700;color:#999;text-transform:uppercase;letter-spacing:1px;">Response Time</td>
        </tr>
        <tr style="border-top:1px solid #e3e8f0;{'background:#ffebee;' if severity=='CRITICAL' else ''}">
          <td style="padding:10px 16px;font-size:13px;color:#b71c1c;font-weight:600;">🔴 CRITICAL</td>
          <td style="padding:10px 16px;font-size:13px;color:#333;">1 hour</td>
        </tr>
        <tr style="border-top:1px solid #e3e8f0;{'background:#fff3e0;' if severity=='HIGH' else ''}">
          <td style="padding:10px 16px;font-size:13px;color:#e64a19;font-weight:600;">🟠 HIGH</td>
          <td style="padding:10px 16px;font-size:13px;color:#333;">4 hours</td>
        </tr>
        <tr style="border-top:1px solid #e3e8f0;{'background:#fff8e1;' if severity=='MEDIUM' else ''}">
          <td style="padding:10px 16px;font-size:13px;color:#f57c00;font-weight:600;">🟡 MEDIUM</td>
          <td style="padding:10px 16px;font-size:13px;color:#333;">24 hours</td>
        </tr>
        <tr style="border-top:1px solid #e3e8f0;{'background:#e8f5e9;' if severity=='LOW' else ''}">
          <td style="padding:10px 16px;font-size:13px;color:#388e3c;font-weight:600;">🟢 LOW</td>
          <td style="padding:10px 16px;font-size:13px;color:#333;">72 hours</td>
        </tr>
      </table>

    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#f8fafc;border-top:1px solid #e3e8f0;padding:20px 40px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <div style="font-size:12px;color:#999;line-height:1.6;">
              This email was generated automatically by <strong>AXION</strong>.<br>
              Do not share sensitive customer credentials in your reply.
            </div>
          </td>
          <td align="right">
            <div style="font-size:11px;color:#bbb;">
              AccessBank AI Support System<br>
              {now}
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

</table>
</td></tr>
</table>

</body>
</html>
""".strip()


def send_escalation_email(
    case_id: str,
    department: str,
    severity: str,
    issue_description: str,
    collected_info: str,
    username: str,
    ai_summary: str = "",
    attachment_bytes: bytes = None,
    attachment_name: str = None,
) -> Tuple[str, str]:
    recipient = DEPARTMENT_EMAILS.get(department, DEPARTMENT_EMAILS["Customer Service / Branch Operations"])
    html_body = build_html_email(case_id, department, severity, issue_description, collected_info, username, ai_summary)
    severity_label = {"LOW": "🟢 LOW", "MEDIUM": "🟡 MEDIUM", "HIGH": "🟠 HIGH", "CRITICAL": "🔴 CRITICAL"}.get(severity, severity)
    subject = f"[{severity_label}] Case {case_id} — {department} | AXION"

    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"AXION <{GMAIL_ADDRESS}>"
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            if attachment_bytes and attachment_name:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment_bytes)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={attachment_name}")
                msg.attach(part)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
                server.sendmail(GMAIL_ADDRESS, recipient, msg.as_string())

            logger.info(f"[EMAIL] Sent to {recipient}")
            return recipient, f"SENT-{case_id}"

        except Exception as e:
            logger.error(f"[EMAIL] Error: {e}")

    logger.info(f"[EMAIL MOCK] To: {recipient} | Subject: {subject}")
    return recipient, f"MOCK-{case_id}"


def get_department_email(department: str) -> str:
    return DEPARTMENT_EMAILS.get(department, DEPARTMENT_EMAILS["Customer Service / Branch Operations"])
