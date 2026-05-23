import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from database import init_db, create_case, get_case, get_case_timeline, get_user_cases, save_rating, get_rating_stats
from agent import classify_and_respond, generate_case_summary
from email_service import send_escalation_email, get_department_email

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

conversations = {}
pending_escalations = {}
user_attachments = {}

LINE = "<code>─────────────────────</code>"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🏦 Services"), KeyboardButton("🏢 Departments")],
        [KeyboardButton("🔒 Security"), KeyboardButton("❓ Help")],
        [KeyboardButton("📋 My Cases"), KeyboardButton("🚨 Report Issue")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Type your question or choose below...",
)

STAR_KEYBOARD = InlineKeyboardMarkup([[
    InlineKeyboardButton("1 ⭐", callback_data="rate_1"),
    InlineKeyboardButton("2 ⭐", callback_data="rate_2"),
    InlineKeyboardButton("3 ⭐", callback_data="rate_3"),
    InlineKeyboardButton("4 ⭐", callback_data="rate_4"),
    InlineKeyboardButton("5 ⭐", callback_data="rate_5"),
]])

def get_conversation(user_id):
    return conversations.get(str(user_id), [])

def add_to_conversation(user_id, role, content):
    uid = str(user_id)
    if uid not in conversations:
        conversations[uid] = []
    conversations[uid].append({"role": role, "content": content})
    if len(conversations[uid]) > 20:
        conversations[uid] = conversations[uid][-20:]

def sev_emoji(s): return {"LOW":"🟢","MEDIUM":"🟡","HIGH":"🟠","CRITICAL":"🔴"}.get(s,"⚪")
def sev_sla(s):   return {"LOW":"72 hours","MEDIUM":"24 hours","HIGH":"4 hours","CRITICAL":"1 hour"}.get(s,"24 hours")
def sent_emoji(s):return {"calm":"😊","neutral":"😐","frustrated":"😤","angry":"😠"}.get(s,"😐")

def h(text): return f"<b>{text}</b>"
def c(text): return f"<code>{text}</code>"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = "\n".join([
        f"👋 {h(f'Welcome, {user.first_name}!')}",
        LINE,
        f"🏦 {h('AXION')} | AccessBank AI Support",
        LINE,
        "",
        f"{h('I can help you with:')}",
        "",
        "💳  Card issues &amp; payments",
        "💸  Failed transfers",
        "📱  Mobile &amp; internet banking",
        "🏦  Loans &amp; applications",
        "🏢  Branch complaints",
        "❓  General questions",
        "",
        LINE,
        "💬 Describe your issue in any language",
        LINE,
        "",
        f"🔒 {h('I will NEVER ask for your:')}",
        c("PIN · CVV · OTP · Password"),
    ])
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "\n".join([
        f"📖 {h('How to use AXION')}",
        LINE,
        "",
        "Just type your question or problem in any language.",
        "",
        f"{h('💬 Examples:')}",
        c("What are working hours?"),
        c("My transfer failed, money deducted"),
        c("I cannot login to mobile app"),
        c("My card was blocked"),
        "",
        "📎 You can send a photo or file as evidence",
        "before describing your issue.",
        "",
        LINE,
        f"{h('📋 Commands')}",
        LINE,
        "/cases   — View your open cases",
        "/status  — Track a specific case",
        "/clear   — Reset conversation",
        "/help    — This menu",
        "",
        LINE,
        f"🔒 {h('Your data is private &amp; secure')}",
        "Each user sees only their own cases.",
    ])
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    conversations.pop(user_id, None)
    pending_escalations.pop(user_id, None)
    user_attachments.pop(user_id, None)
    msg = "\n".join([
        f"🔄 {h('Conversation Reset')}",
        LINE,
        "",
        "Fresh start! How can I help you today?",
    ])
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        msg = "\n".join([
            f"ℹ️ {h('Usage')}",
            LINE,
            "",
            c("/status AB-XXXXXXXX"),
            "",
            "Example:",
            c("/status AB-3F8A21B0"),
        ])
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    case_id = context.args[0].upper()
    case = get_case(case_id)

    if not case:
        msg = "\n".join([
            f"❌ {h('Case Not Found')}",
            LINE,
            "",
            f"Case ID: {c(case_id)}",
            "",
            "Please check the ID and try again.",
            "Use /cases to see your open cases.",
        ])
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    timeline = get_case_timeline(case_id)
    timeline_lines = [c(f"{t['timestamp'][11:16]}") + f"  {t['event']}" for t in timeline]
    status_icons = {"open":"🟡 OPEN","pending":"🟠 PENDING","resolved":"🟢 RESOLVED","closed":"⚫ CLOSED"}
    status_label = status_icons.get(case["status"], case["status"].upper())
    sev = case["severity"]

    msg = "\n".join([
        f"📋 {h('Case Details')}",
        LINE,
        "",
        f"🆔 {c(case_id)}",
        f"📊 {h(status_label)}",
        f"🏢 {case['department']}",
        f"{sev_emoji(sev)} {h(sev)} — SLA: {sev_sla(sev)}",
        f"📅 {case['created_at'][:16].replace('T',' ')} UTC",
        "",
        LINE,
        f"{h('📝 Issue')}",
        LINE,
        "",
        case["issue_description"],
        "",
        LINE,
        f"{h('🕐 Timeline')}",
        LINE,
        "",
    ] + timeline_lines)
    await update.message.reply_text(msg, parse_mode="HTML")


async def cases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    cases = get_user_cases(user_id)

    if not cases:
        msg = "\n".join([
            f"📂 {h('No Cases Found')}",
            LINE,
            "",
            "You have no open support cases.",
            "",
            "Describe your issue and I will",
            "create a case automatically.",
        ])
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    status_icons = {"open":"🟡","pending":"🟠","resolved":"🟢","closed":"⚫"}
    lines = [f"📂 {h('Your Cases')}", LINE]
    for cas in cases[:5]:
        sev = cas["severity"]
        s_icon = status_icons.get(cas["status"], "⚪")
        lines += [
            "",
            f"🆔 {c(cas['id'])}",
            f"{sev_emoji(sev)} {h(sev)}  {s_icon} {cas['status'].upper()}",
            f"🏢 {cas['department']}",
            f"📅 {cas['created_at'][:10]}",
        ]
    lines += ["", LINE, "Use /status [ID] for details"]
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def handle_attachment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if update.message.photo:
        tg_file = update.message.photo[-1]
        file_id = tg_file.file_id
        file_type = "photo"
        file_name = "evidence.jpg"
    elif update.message.document:
        tg_file = update.message.document
        file_id = tg_file.file_id
        file_type = "document"
        file_name = tg_file.file_name or "attachment"
    else:
        return

    # Download file bytes from Telegram
    try:
        file_obj = await context.bot.get_file(file_id)
        file_bytes = await file_obj.download_as_bytearray()
    except Exception as e:
        logger.error(f"File download error: {e}")
        file_bytes = None

    user_attachments[user_id] = {
        "file_id": file_id,
        "type": file_type,
        "file_name": file_name,
        "file_bytes": bytes(file_bytes) if file_bytes else None,
    }
    msg = "\n".join([
        f"📎 {h('Attachment Received')}",
        LINE,
        "",
        f"{'🖼️ Photo' if file_type == 'photo' else '📄 Document'} saved successfully.",
        "",
        "It will be attached to your case.",
        "",
        LINE,
        "Now describe your issue in text.",
    ])
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)


async def handle_keyboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📋 My Cases":
        await cases_command(update, context)
        return
    if text == "❓ Help":
        await help_command(update, context)
        return

    if text == "🏦 Services":
        msg = "\n".join([
            f"🏦 {h('AccessBank Services')}",
            LINE,
            "",
            "💳  Cards — Debit &amp; Credit (Visa, Mastercard)",
            "💸  Transfers — Local &amp; International (SWIFT)",
            "📱  Digital Banking — Mobile App &amp; Internet",
            "🏠  Loans — Personal, Business, Mortgage",
            "💰  Deposits — AZN, USD, EUR",
            "💱  Currency Exchange — All branches",
            "",
            LINE,
            "Ask me anything about these services!",
        ])
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)
        return

    if text == "🏢 Departments":
        msg = "\n".join([
            f"🏢 {h('Our Departments')}",
            LINE,
            "",
            "📱 " + h("Digital Banking"),
            "     Mobile app, login, OTP issues",
            "",
            "💳 " + h("Card Operations"),
            "     Blocked cards, failed payments",
            "",
            "💸 " + h("Transfers &amp; Payments"),
            "     Failed transfers, deducted amount",
            "",
            "🏦 " + h("Loans &amp; Applications"),
            "     Loan status, documents, repayment",
            "",
            "🏢 " + h("Customer Service"),
            "     Branch complaints, general issues",
            "",
            LINE,
            "Describe your issue and I will route",
            "you to the right department automatically.",
        ])
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)
        return

    if text == "🔒 Security":
        msg = "\n".join([
            f"🛡️ {h('Security Center')}",
            LINE,
            "",
            f"🔴 {h('AXION &amp; AccessBank will')}",
            f"{h('NEVER ask you for:')}",
            "",
            c("  ✗  PIN code"),
            c("  ✗  CVV / CVC number"),
            c("  ✗  OTP / SMS code"),
            c("  ✗  Internet banking password"),
            c("  ✗  Full card number"),
            "",
            LINE,
            f"✅ {h('What we WILL ask for:')}",
            "",
            "   ✓  Last 4 digits of card",
            "   ✓  Transaction amount",
            "   ✓  Date and time of issue",
            "   ✓  Type of operation",
            "",
            LINE,
            f"⚠️ {h('SCAM WARNING')}",
            LINE,
            "",
            "If ANYONE claims to be AccessBank",
            "and asks for sensitive data —",
            f"{h('HANG UP immediately.')}",
            "",
            "📞  Fraud hotline: " + c("*8801"),
            "🌐  Official site: " + c("accessbank.az"),
            "",
            LINE,
            f"🔒 {h('Your safety is our priority.')}",
        ])
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)
        return

    if text == "🚨 Report Issue":
        msg = "\n".join([
            f"🚨 {h('Report an Issue')}",
            LINE,
            "",
            "Describe your problem in plain language:",
            "",
            c("My transfer failed, money deducted"),
            c("I cannot login to mobile banking"),
            c("My card was blocked unexpectedly"),
            "",
            LINE,
            "📎 You can also send a photo or file",
            "as evidence first, then describe.",
            "",
            LINE,
            "I will analyze, assign severity",
            "and escalate automatically.",
        ])
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=MAIN_KEYBOARD)
        return

    await handle_message(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or user.first_name
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    history = get_conversation(user_id)
    result = classify_and_respond(
        user_message=user_message,
        conversation_history=history,
        user_id=user_id,
        username=username,
    )

    add_to_conversation(user_id, "user", user_message)
    add_to_conversation(user_id, "assistant", result.get("response", ""))

    response_text = result.get("response", "I am sorry, something went wrong.")
    is_issue = result.get("is_issue", False)
    ready_to_escalate = result.get("ready_to_escalate", False)
    sentiment = result.get("sentiment", "neutral")

    parts = [response_text]

    if is_issue and result.get("severity"):
        sev = result["severity"]
        dept = result.get("department", "Unknown")
        sev_reason = result.get("severity_reason", "")
        has_attachment = user_id in user_attachments
        parts += [
            "",
            LINE,
            f"🤖 {h('AI Analysis')}",
            LINE,
            "",
            f"🏢 {h(dept)}",
            f"{sev_emoji(sev)} {h(sev)}",
            f"💡 {sev_reason}",
            f"{sent_emoji(sentiment)} {sentiment.capitalize()} customer",
            f"⏱️ SLA: {sev_sla(sev)}",
            f"📎 {'Attachment ready ✅' if has_attachment else 'No attachment'}",
        ]

    if ready_to_escalate:
        pending_escalations[user_id] = {
            "result": result,
            "issue_description": user_message,
            "username": username,
        }
        parts += ["", LINE, f"📋 {h('Create a support case?')}"]
        keyboard = [[
            InlineKeyboardButton("✅ Yes, create case", callback_data="escalate_yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="escalate_no"),
        ]]
        await update.message.reply_text("\n".join(parts), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("\n".join(parts), parse_mode="HTML")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username or user.first_name

    if query.data.startswith("rate_"):
        stars = int(query.data.split("_")[1])
        star_str = "⭐" * stars
        responses = {
            1: "We are sorry to hear that. We will work to improve.",
            2: "Thank you. We will do better next time.",
            3: "Thank you for your feedback!",
            4: "Great! We are glad we could help.",
            5: "Amazing! Thank you for the perfect score!",
        }
        msg = "\n".join([
            f"🌟 {h('Thank you for rating us!')}",
            LINE,
            "",
            f"Your rating: {star_str}",
            "",
            responses.get(stars, "Thank you!"),
            "",
            LINE,
            "🏦 AXION — AccessBank AI Support",
        ])
        await query.edit_message_text(msg, parse_mode="HTML")
        return

    if query.data == "escalate_yes":
        pending = pending_escalations.get(user_id)
        if not pending:
            await query.edit_message_text("Session expired. Please describe your issue again.")
            return

        result = pending["result"]
        department = result.get("department", "Customer Service / Branch Operations")
        severity = result.get("severity", "MEDIUM")
        collected_info = result.get("collected_info_summary", "No additional details collected.")
        issue_description = pending["issue_description"]

        await query.edit_message_text("\n".join([
            f"⏳ {h('Processing your case...')}",
            LINE,
            "",
            "🧠 Generating AI summary...",
            "📋 Creating case...",
            "📧 Sending escalation email...",
        ]), parse_mode="HTML")

        summary = generate_case_summary(issue_description, department, severity)
        attachment = user_attachments.get(user_id)
        attachment_note = f"\nAttachment: {attachment['type']} provided by customer" if attachment else ""

        try:
            email_recipient, email_message_id = send_escalation_email(
                case_id="PENDING",
                department=department,
                severity=severity,
                issue_description=issue_description,
                collected_info=collected_info + attachment_note,
                username=username,
                ai_summary=summary,
                attachment_bytes=attachment.get("file_bytes") if attachment else None,
                attachment_name=attachment.get("file_name") if attachment else None,
            )
        except Exception as e:
            logger.error(f"Email error: {e}")
            email_recipient = get_department_email(department)
            email_message_id = None

        case_id = create_case(
            user_id=user_id,
            username=username,
            issue_description=issue_description,
            department=department,
            severity=severity,
            collected_info=collected_info,
            email_sent_to=email_recipient,
            email_message_id=email_message_id,
        )

        if attachment and attachment.get("type") == "photo":
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=attachment["file_id"],
                    caption=f"📎 Evidence attached to Case {case_id}",
                )
            except Exception as e:
                logger.error(f"Photo error: {e}")

        user_attachments.pop(user_id, None)
        now = datetime.utcnow().strftime("%H:%M")

        confirmation = "\n".join([
            f"✅ {h('Case Created Successfully')}",
            LINE,
            "",
            f"🆔 {c(case_id)}",
            f"🏢 {h(department)}",
            f"{sev_emoji(severity)} {h(severity)} — SLA: {sev_sla(severity)}",
            f"📧 Email dispatched",
            f"📬 {c(email_recipient)}",
            "",
            LINE,
            f"🧠 {h('AI Summary')}",
            LINE,
            "",
            f"<i>{summary}</i>",
            "",
            LINE,
            f"🕐 {h('Timeline')}",
            LINE,
            "",
            f"{c(now)}  ✅ Case registered",
            f"{c(now)}  📂 Routed to {department}",
            f"{c(now)}  📧 Email dispatched",
            f"{c(now)}  ⏳ Awaiting response",
            "",
            LINE,
            f"Track: {c('/status ' + case_id)}",
        ])

        await context.bot.send_message(chat_id=query.message.chat_id, text=confirmation, parse_mode="HTML")
        pending_escalations.pop(user_id, None)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="\n".join([
                f"⭐ {h('Rate Your Experience')}",
                LINE,
                "",
                "How would you rate AXION support today?",
            ]),
            parse_mode="HTML",
            reply_markup=STAR_KEYBOARD,
        )

    elif query.data == "escalate_no":
        pending_escalations.pop(user_id, None)
        await query.edit_message_text("\n".join([
            f"❌ {h('Cancelled')}",
            LINE,
            "",
            "No case was created.",
            "Feel free to ask anything else.",
        ]), parse_mode="HTML")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception: {context.error}")


def main():
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cases", cases_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_attachment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_keyboard_button))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    logger.info("AXION — AccessBank AI Agent is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()