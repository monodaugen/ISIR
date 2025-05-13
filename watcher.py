import requests, json, os, time
from datetime import datetime
from smtplib import SMTP
from email.mime.text import MIMEText
import threading
from dotenv import load_dotenv

load_dotenv()

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", 10))
SMTP_CONFIG = {
    "server": os.getenv("SMTP_SERVER"),
    "port": int(os.getenv("SMTP_PORT", 587)),
    "user": os.getenv("SMTP_USER"),
    "password": os.getenv("SMTP_PASS"),
    "from": os.getenv("SMTP_FROM"),
    "to": os.getenv("SMTP_TO"),
}

DATA_DIR = "data"
STATE_FILE = os.path.join(DATA_DIR, "event_state.json")
IC_FILE = os.path.join(DATA_DIR, "ic_list.json")

def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_events(ic):
    url = "https://www.isir.info/api/getevents"
    response = requests.get(url, params={"ic": ic})
    response.raise_for_status()
    return response.json().get("data", [])

def send_email(subject, body):
    config = SMTP_CONFIG
    if not config["user"]:
        print("⚠️ SMTP není nastaven.")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = config["from"]
    msg["To"] = config["to"]

    with SMTP(config["server"], config["port"]) as smtp:
        smtp.starttls()
        smtp.login(config["user"], config["password"])
        smtp.send_message(msg)

def check_all():
    ic_list = load_json(IC_FILE).get("ics", [])
    state = load_json(STATE_FILE)
    all_new = {}

    for ic in ic_list:
        try:
            events = get_events(ic)
            last_id = state.get(ic, 0)

            new_events = [e for e in events if e["event_id"] > last_id]
            if new_events:
                new_events.sort(key=lambda e: e["event_id"])
                state[ic] = new_events[-1]["event_id"]
                all_new[ic] = new_events

        except Exception as e:
            print(f"❌ Chyba při kontrole IČ {ic}: {e}")

    if all_new:
        save_json(STATE_FILE, state)
        text = ""
        for ic, events in all_new.items():
            text += f"IČ {ic} – {len(events)} nových událostí:\n"
            for e in events:
                text += f"- {e['timestamp']} | {e['text']}\n"
            text += "\n"

        send_email("ISIR: nové události", text.strip())
        print(f"📧 Odeslán e-mail s novinkami.")
    return all_new

def run_scheduler():
    print(f"🕒 Spouštím kontrolu každých {CHECK_INTERVAL} minut.")
    while True:
        check_all()
        time.sleep(CHECK_INTERVAL * 60)

def start_background_thread():
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
