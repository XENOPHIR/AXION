import sqlite3
import os
from datetime import datetime

DB_PATH = "data/accessbank_cases.db"

def color(text, code): return f"\033[{code}m{text}\033[0m"
def bold(text): return color(text, "1")
def green(text): return color(text, "92")
def yellow(text): return color(text, "93")
def red(text): return color(text, "91")
def blue(text): return color(text, "94")
def cyan(text): return color(text, "96")

SEV_COLOR = {"LOW": green, "MEDIUM": yellow, "HIGH": red, "CRITICAL": red}

def sev_fmt(s):
    fn = SEV_COLOR.get(s, str)
    icons = {"LOW":"🟢","MEDIUM":"🟡","HIGH":"🟠","CRITICAL":"🔴"}
    return fn(f"{icons.get(s,'')} {s}")

def print_header():
    print()
    print(bold(cyan("━"*60)))
    print(bold(cyan("  🏦  AXION — AccessBank AI Support")))
    print(bold(cyan("       Database Viewer")))
    print(bold(cyan("━"*60)))
    print()

def print_cases(cursor):
    cursor.execute("SELECT id, department, severity, status, created_at, issue_description FROM cases ORDER BY created_at DESC")
    rows = cursor.fetchall()

    print(bold(blue(f"📋  CASES  ({len(rows)} total)")))
    print("─"*60)

    if not rows:
        print("  No cases found.")
        return

    for row in rows:
        case_id, dept, sev, status, created_at, issue = row
        date = created_at[:16].replace("T", " ")
        status_icon = {"open":"🟡","pending":"🟠","resolved":"🟢","closed":"⚫"}.get(status,"⚪")
        short_issue = (issue[:50] + "...") if issue and len(issue) > 50 else issue

        print(f"  {bold(case_id)}  {status_icon} {status.upper()}")
        print(f"  🏢 {dept}")
        print(f"  {sev_fmt(sev)}  |  📅 {date}")
        print(f"  💬 {short_issue}")
        print("  " + "·"*56)

def print_ratings(cursor):
    try:
        cursor.execute("SELECT username, stars, created_at FROM ratings ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.execute("SELECT AVG(stars), COUNT(*) FROM ratings")
        avg, total = cursor.fetchone()
    except:
        rows = []
        avg, total = 0, 0

    print()
    print(bold(blue(f"⭐  RATINGS  ({total} total)")))
    print("─"*60)

    if not rows:
        print("  No ratings yet.")
    else:
        for username, stars, created_at in rows:
            date = created_at[:16].replace("T", " ")
            star_str = "⭐" * stars
            print(f"  @{username or 'unknown'}  {star_str}  |  📅 {date}")

    if total and avg:
        print()
        print(f"  {bold('Average rating:')} {'⭐' * round(avg)}  {round(avg,1)}/5  ({total} reviews)")

def print_stats(cursor):
    cursor.execute("SELECT COUNT(*) FROM cases")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT department, COUNT(*) as cnt FROM cases GROUP BY department ORDER BY cnt DESC")
    dept_rows = cursor.fetchall()
    cursor.execute("SELECT severity, COUNT(*) as cnt FROM cases GROUP BY severity ORDER BY cnt DESC")
    sev_rows = cursor.fetchall()

    print()
    print(bold(blue("📊  STATS")))
    print("─"*60)
    print(f"  Total cases: {bold(str(total))}")
    print()
    print("  By department:")
    for dept, cnt in dept_rows:
        bar = "█" * cnt
        print(f"    {dept[:35]:<35} {cyan(bar)} {cnt}")
    print()
    print("  By severity:")
    for sev, cnt in sev_rows:
        print(f"    {sev_fmt(sev):<20}  {cnt} cases")

def main():
    if not os.path.exists(DB_PATH):
        print(red("Database not found. Run the bot first."))
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print_header()
    print_cases(cursor)
    print_ratings(cursor)
    print_stats(cursor)

    print()
    print(bold(cyan("━"*60)))
    print(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(bold(cyan("━"*60)))
    print()

    conn.close()

if __name__ == "__main__":
    main()
