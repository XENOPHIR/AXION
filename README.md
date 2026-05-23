# 🏦 AXION — AccessBank AI Support Agent

> AI-powered banking support agent that triages, prioritizes, escalates and tracks customer incidents end-to-end — through Telegram.

---

## 📌 What is AXION?

AXION is an intelligent customer support agent built for AccessBank. Unlike a simple FAQ chatbot, AXION understands the difference between a customer asking a question and a customer reporting a real problem.

When a real issue is detected, AXION automatically:
- Identifies which of 5 departments should handle it
- Scores the severity (Low / Medium / High / Critical)
- Reads the customer's emotional tone (sentiment)
- Collects only safe, relevant details — never PIN, CVV, OTP
- Creates a numbered support case in the database
- Sends a professional HTML escalation email with AI summary
- Shows the customer a live case timeline
- Asks for a star rating after the case is created

Everything happens inside Telegram — no app to install, no forms to fill.

---

## 🚀 Quick Start

### Requirements
- Docker Desktop
- Telegram Bot token (from @BotFather)
- OpenAI API key (provided by hackathon)
- Gmail account + App Password

### 1. Clone the repository
```bash
git clone https://github.com/your-username/accessbank-ai-agent.git
cd accessbank-ai-agent
```

### 2. Create .env file

**Linux / Mac:**
```bash
cp env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item env.example .env
```

Open `.env` in any text editor and fill in:
```env
OPENAI_API_KEY=sk-proj-...
TELEGRAM_BOT_TOKEN=your-bot-token
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_DIGITAL_BANKING=axion.support@sharklasers.com
EMAIL_CARD_OPERATIONS=axion.support@sharklasers.com
EMAIL_TRANSFERS=axion.support@sharklasers.com
EMAIL_LOANS=axion.loans@sharklasers.com
EMAIL_CUSTOMER_SERVICE=axion.support@sharklasers.com
```

### 3. Run
```bash
docker-compose up --build
```

### 4. Open Telegram and send /start

---

## ✅ Live Demo Credentials

To verify the system is working end-to-end, use these real inboxes:

### 📧 Sent emails (Gmail outbox)
```
Email:    splunkalert2@gmail.com
Password: axionteam5!
```
Login at gmail.com — all sent escalation emails are visible in Sent.

### 📬 Department inboxes (receive escalations)

**Digital Banking / Card Operations / Transfers / Customer Service:**
```
Inbox: axion.support@sharklasers.com
Check: https://www.guerrillamail.com
       → enter: axion.support
```

**Loans & Applications:**
```
Inbox: axion.loans@sharklasers.com
Check: https://www.guerrillamail.com
       → enter: axion.loans
```

No registration needed — just open guerrillamail.com, type the inbox name and see the emails arrive in real time.

---

## 📧 Escalation Email Example

When a case is created, the department receives a fully formatted HTML email:

```
┌─────────────────────────────────────────────────┐
│ 🏦 AXION          │ CASE ID: AB-DDF6FE49        │
│ Intelligent       │                              │
│ Banking Support   │                              │
├─────────────────────────────────────────────────┤
│ SEVERITY LEVEL                                  │
│ 🟠 HIGH    [ SLA: Respond within 4 hours ]      │
├───────────────────┬─────────────────────────────┤
│ DEPARTMENT        │ CUSTOMER                    │
│ Transfers &       │ @muradbabay3v               │
│ Payments          │                             │
│ TIMESTAMP         │ STATUS                      │
│ May 23, 2026      │ ⏳ Awaiting Action           │
│ 11:17 UTC         │                             │
├─────────────────────────────────────────────────┤
│ 🧠 AI SUMMARY                                   │
│                                                 │
│ On May 23 at 14:30, a bank transfer via app     │
│ version 2.3.1 from the Nizami branch to another │
│ bank failed. The issue is classified as HIGH    │
│ severity. Immediate investigation required.     │
├─────────────────────────────────────────────────┤
│ 📋 ISSUE DESCRIPTION                            │
│ Transfer failed, money was deducted from        │
│ account. Amount 350 AZN to Kapital Bank.        │
├─────────────────────────────────────────────────┤
│ 📌 COLLECTED DETAILS                            │
│ Amount: 350 AZN · Date: May 23 · Time: 14:30   │
│ Transfer to: Kapital Bank · Branch: Nizami      │
├─────────────────────────────────────────────────┤
│ ⚡ ACTION REQUIRED                              │
│ Respond within 4 hours                          │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Project Workflow

```
USER (Telegram)
      │
      │ writes message
      ▼
┌─────────────────┐
│    main.py      │ ── keyboard buttons ──▶ static responses
│   Bot Handler   │                         (Services, Departments,
└────────┬────────┘                          Security, Help)
         │
         │ text message
         ▼
┌─────────────────┐     ┌──────────────────┐
│    rag.py       │     │    agent.py      │
│  TF-IDF search  │────▶│   GPT-4o Brain   │
│  Knowledge Base │     │                  │
│  (FAQ lookup)   │     │ • Is this a real │
└─────────────────┘     │   issue or FAQ?  │
                        │ • Which dept?    │
                        │ • Severity?      │
                        │ • Sentiment?     │
                        │ • Need more info?│
                        └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              FAQ question              Real issue detected
                    │                         │
                    ▼                         ▼
           Answer from KB          Collect safe details
           (working hours,         (amount, date, branch)
            loan info, etc)               │
                                          │ user confirms
                                          ▼
                              ┌───────────────────────┐
                              │      database.py       │
                              │   Create Case record   │
                              │   AB-XXXXXXXX          │
                              │   Log timeline events  │
                              └───────────┬───────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │    email_service.py    │
                              │  Generate AI Summary   │
                              │  Build HTML email      │
                              │  Attach file (if any)  │
                              │  Send via Gmail SMTP   │
                              └───────────┬───────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │   USER gets in TG:     │
                              │   ✅ Case ID           │
                              │   🧠 AI Summary        │
                              │   🕐 Timeline          │
                              │   ⭐ Rate experience   │
                              └───────────────────────┘
```

---

## 🗄️ Database Structure

All data is stored in SQLite at `data/accessbank_cases.db`

### Table: cases
```
┌──────────────────┬──────────┬──────────────────────────────┐
│ Column           │ Type     │ Description                  │
├──────────────────┼──────────┼──────────────────────────────┤
│ id               │ TEXT     │ Case number (AB-XXXXXXXX)    │
│ user_id          │ TEXT     │ Telegram user ID             │
│ username         │ TEXT     │ Telegram username            │
│ issue_description│ TEXT     │ Original customer message    │
│ department       │ TEXT     │ Assigned department          │
│ severity         │ TEXT     │ LOW/MEDIUM/HIGH/CRITICAL     │
│ status           │ TEXT     │ open/pending/resolved/closed │
│ collected_info   │ TEXT     │ Details gathered from user   │
│ email_sent_to    │ TEXT     │ Department email address     │
│ email_message_id │ TEXT     │ Gmail message reference      │
│ created_at       │ TEXT     │ ISO timestamp                │
│ updated_at       │ TEXT     │ ISO timestamp                │
└──────────────────┴──────────┴──────────────────────────────┘
```

### Table: case_timeline
```
┌──────────────────┬──────────┬──────────────────────────────┐
│ Column           │ Type     │ Description                  │
├──────────────────┼──────────┼──────────────────────────────┤
│ id               │ INTEGER  │ Auto increment               │
│ case_id          │ TEXT     │ Links to cases.id            │
│ event            │ TEXT     │ What happened at this step   │
│ timestamp        │ TEXT     │ ISO timestamp                │
└──────────────────┴──────────┴──────────────────────────────┘
```

### Table: ratings
```
┌──────────────────┬──────────┬──────────────────────────────┐
│ Column           │ Type     │ Description                  │
├──────────────────┼──────────┼──────────────────────────────┤
│ id               │ INTEGER  │ Auto increment               │
│ user_id          │ TEXT     │ Telegram user ID             │
│ username         │ TEXT     │ Telegram username            │
│ stars            │ INTEGER  │ Rating 1 to 5                │
│ case_id          │ TEXT     │ Related case (optional)      │
│ created_at       │ TEXT     │ ISO timestamp                │
└──────────────────┴──────────┴──────────────────────────────┘
```

### View the database
```bash
docker exec accessbank-ai-agent python3 view_db.py
```

---

## 📚 Knowledge Base

Located at `knowledge_base/accessbank_faq.txt`

Covers: working hours, branches, mobile app, cards, transfers, loans, deposits, currency exchange, fees, security rules.

The system uses **TF-IDF retrieval** — it does NOT send the full knowledge base to GPT every time. It finds only the 2-3 most relevant sections per query. To update — edit the file and restart.

---

## 💬 Bot Usage

### Menu Buttons
| Button | What it does |
|---|---|
| 🏦 Services | All AccessBank services |
| 🏢 Departments | 5 departments with descriptions |
| 🔒 Security | Security rules and scam warnings |
| ❓ Help | Usage guide |
| 📋 My Cases | Your open cases |
| 🚨 Report Issue | How to report a problem |

### Commands
```
/start   — Welcome screen
/help    — Usage guide
/cases   — Your cases
/status AB-XXXXXXXX — Track a case
/clear   — Reset conversation
```

### Attaching Evidence
Send a photo or file before describing your issue — it will be attached to the escalation email automatically.

---

## 🔒 Security

- Never requests PIN, CVV, OTP, password, or full card number
- Each user sees only their own cases (isolated by Telegram user ID)
- API keys in `.env` — never committed to Git
- Gmail uses App Password — no account password stored anywhere

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Interface | Telegram Bot (python-telegram-bot v20) |
| AI Brain | OpenAI GPT-4o |
| Knowledge Retrieval | TF-IDF (scikit-learn) |
| Database | SQLite |
| Email | Gmail SMTP + App Password (SSL port 465) |
| Language | Python 3.11 |
| Deployment | Docker + Docker Compose |

---

## 📁 Project Structure

```
accessbank-ai-agent/
├── main.py                    — Telegram bot, all handlers
├── agent.py                   — GPT-4o, severity, sentiment, summary
├── rag.py                     — TF-IDF retrieval over knowledge base
├── database.py                — SQLite, cases, timeline, ratings
├── email_service.py           — Gmail, HTML email, file attachment
├── view_db.py                 — Database viewer
├── knowledge_base/
│   └── accessbank_faq.txt     — AccessBank knowledge base
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── env.example
└── README.md
```

---

*Built for the AccessBank Hackathon — AXION turns reactive customer support into intelligent, automated incident management.*