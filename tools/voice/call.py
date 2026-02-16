#!/usr/bin/env python3
"""
Atlas Voice — Outbound call trigger.

Usage:
    python tools/voice/call.py norm "Hey Norm, this is Atlas testing voice."
    python tools/voice/call.py austin
    python tools/voice/call.py --to "+19105551234" --greeting "Hello!"

Lifecycle:
  1. Starts FastAPI WebSocket server (server.py) on port 8001
  2. Starts ngrok tunnel to expose the server publicly
  3. Creates outbound call via Twilio REST API
  4. Waits for call to end (Ctrl+C to hang up early)
  5. Cleans up server + ngrok
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

# Load environment
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_PATH)

# Also load from chief_of_staff .env for any shared keys
COS_ENV = Path("/Users/nl/projects/chief_of_staff/.env")
if COS_ENV.exists():
    load_dotenv(COS_ENV, override=False)

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "args" / "voice_config.yaml"
CONTACTS_PATH = Path(__file__).resolve().parent.parent.parent / "args" / "contacts.yaml"
PYTHON = Path("/Users/nl/projects/chief_of_staff/.venv/bin/python")
SERVER_SCRIPT = Path(__file__).resolve().parent / "server.py"

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

with open(CONTACTS_PATH) as f:
    contacts_data = yaml.safe_load(f)


def resolve_contact(name_or_number: str) -> tuple[str, str, str]:
    """Resolve a contact name to (phone, name, context). Or use raw number."""
    if name_or_number.startswith("+"):
        return name_or_number, "Unknown", ""

    contacts = contacts_data.get("contacts", {})
    key = name_or_number.lower()
    if key not in contacts:
        available = ", ".join(contacts.keys())
        print(f"[call] Contact '{name_or_number}' not found. Available: {available}")
        sys.exit(1)

    entry = contacts[key]
    phone = entry.get("phone", "")
    if "REPLACEME" in phone:
        print(f"[call] Contact '{key}' phone not configured. Edit args/contacts.yaml")
        sys.exit(1)

    context = entry.get("context", "")
    return phone, key, context


def start_server(port: int, env_vars: dict) -> subprocess.Popen:
    """Start the FastAPI voice server as a subprocess."""
    env = os.environ.copy()
    env.update(env_vars)

    proc = subprocess.Popen(
        [str(PYTHON), str(SERVER_SCRIPT)],
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(f"[call] Server starting on port {port} (PID: {proc.pid})")

    # Wait for server to be ready
    for i in range(20):
        try:
            r = requests.get(f"http://localhost:{port}/docs", timeout=1)
            if r.status_code == 200:
                print(f"[call] Server ready.")
                return proc
        except requests.ConnectionError:
            pass
        time.sleep(0.5)

    print("[call] Server failed to start within 10s")
    proc.terminate()
    sys.exit(1)


def start_ngrok(port: int) -> tuple[subprocess.Popen, str]:
    """Start ngrok tunnel and return (process, public_domain)."""
    proc = subprocess.Popen(
        ["ngrok", "http", str(port), "--log=stdout", "--log-format=json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"[call] ngrok starting (PID: {proc.pid})...")

    # Wait for tunnel to be ready, then query the API
    time.sleep(3)

    for i in range(10):
        try:
            r = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            tunnels = r.json().get("tunnels", [])
            for t in tunnels:
                public_url = t.get("public_url", "")
                if public_url.startswith("https://"):
                    domain = public_url.replace("https://", "")
                    print(f"[call] ngrok tunnel: {public_url}")
                    return proc, domain
        except Exception:
            pass
        time.sleep(1)

    print("[call] Failed to get ngrok tunnel URL")
    proc.terminate()
    sys.exit(1)


def make_call(to_number: str, twiml_url: str) -> str:
    """Create outbound call via Twilio REST API. Returns Call SID."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        print("[call] Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env")
        sys.exit(1)

    from twilio.rest import Client
    client = Client(account_sid, auth_token)

    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url=twiml_url,
    )

    print(f"[call] Call initiated: SID={call.sid}, To={to_number}, Status={call.status}")
    return call.sid


def wait_for_call_end(call_sid: str):
    """Poll Twilio for call status until it ends."""
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    from twilio.rest import Client
    client = Client(account_sid, auth_token)

    print("[call] Call in progress. Press Ctrl+C to hang up.")

    while True:
        try:
            call = client.calls(call_sid).fetch()
            status = call.status
            if status in ("completed", "failed", "busy", "no-answer", "canceled"):
                duration = call.duration or 0
                print(f"[call] Call ended: status={status}, duration={duration}s")
                return
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n[call] Hanging up...")
            try:
                client.calls(call_sid).update(status="completed")
            except Exception:
                pass
            return


def main():
    parser = argparse.ArgumentParser(description="Atlas Voice — make an outbound call")
    parser.add_argument("contact", nargs="?", help="Contact name from contacts.yaml or phone number (+1...)")
    parser.add_argument("greeting", nargs="?", default=None, help="Custom greeting (optional)")
    parser.add_argument("--to", help="Phone number to call (alternative to contact name)")
    parser.add_argument("--greeting", dest="greeting_flag", help="Custom greeting")
    args = parser.parse_args()

    # Resolve who to call
    target = args.to or args.contact
    if not target:
        print("Usage: python tools/voice/call.py <contact_name> [greeting]")
        print("       python tools/voice/call.py --to '+1XXXXXXXXXX' --greeting 'Hello!'")
        sys.exit(1)

    phone, name, context = resolve_contact(target)
    greeting = args.greeting or args.greeting_flag or f"Hey, this is Atlas calling for Norm."

    port = config.get("call", {}).get("server_port", 8001)

    print(f"[call] Calling {name} at {phone}")
    print(f"[call] Greeting: {greeting}")

    # Track subprocesses for cleanup
    server_proc = None
    ngrok_proc = None

    def cleanup(sig=None, frame=None):
        print("\n[call] Cleaning up...")
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        if ngrok_proc:
            ngrok_proc.terminate()
            ngrok_proc.wait(timeout=5)
        print("[call] Done.")
        if sig:
            sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # 1. Start ngrok first (need the URL for the server)
        ngrok_proc, ngrok_domain = start_ngrok(port)

        # 2. Start the voice server
        env_vars = {
            "NGROK_DOMAIN": ngrok_domain,
            "CALL_CONTEXT": context,
            "CALL_GREETING": greeting,
        }
        server_proc = start_server(port, env_vars)

        # 3. Make the call
        twiml_url = f"https://{ngrok_domain}/twiml"
        print(f"[call] TwiML URL: {twiml_url}")

        call_sid = make_call(phone, twiml_url)

        # 4. Wait for call to end
        wait_for_call_end(call_sid)

    except Exception as e:
        print(f"[call] Error: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
