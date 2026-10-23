#!/usr/bin/env python3
"""Read-only Google Calendar client using only the standard library.

Commands:
  auth    one-time browser login; stores a refresh token
  events  print upcoming events (next 24h) as JSON on stdout

`events` always prints JSON. Exit codes: 0 ok, 2 reauthorization needed, 1 other error.
"""
import base64
import hashlib
import http.server
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone

CONF = os.path.expanduser("~/.config/calendarz")
CREDS = f"{CONF}/credentials.json"
TOKEN = f"{CONF}/token.json"
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
API = "https://www.googleapis.com/calendar/v3"
HORIZON = timedelta(hours=24)


class Reauth(Exception):
    pass


def client():
    with open(CREDS) as f:
        return json.load(f)["installed"]


def post(url, data):
    req = urllib.request.Request(url, urllib.parse.urlencode(data).encode())
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def save_token(tok, refresh_token=None):
    tok["refresh_token"] = tok.get("refresh_token") or refresh_token
    tok["expiry"] = time.time() + tok.get("expires_in", 3600)
    fd = os.open(TOKEN, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(tok, f)


def access_token():
    try:
        with open(TOKEN) as f:
            tok = json.load(f)
    except FileNotFoundError:
        raise Reauth
    if tok["expiry"] > time.time() + 60:
        return tok["access_token"]
    c = client()
    try:
        new = post(c["token_uri"], {
            "client_id": c["client_id"],
            "client_secret": c["client_secret"],
            "refresh_token": tok["refresh_token"],
            "grant_type": "refresh_token",
        })
    except urllib.error.HTTPError as e:
        if e.code in (400, 401):  # invalid_grant: refresh token expired or revoked
            raise Reauth
        raise
    save_token(new, tok["refresh_token"])
    return new["access_token"]


def auth():
    c = client()
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"calendarz: authorized, you can close this tab.")

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = c["auth_uri"] + "?" + urllib.parse.urlencode({
        "client_id": c["client_id"],
        "redirect_uri": redirect,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    print("Opening browser. If nothing opens, visit:\n" + url, file=sys.stderr)
    webbrowser.open(url)
    server.handle_request()
    if "code" not in got:
        sys.exit(f"authorization failed: {got.get('error', ['unknown'])[0]}")
    tok = post(c["token_uri"], {
        "client_id": c["client_id"],
        "client_secret": c["client_secret"],
        "code": got["code"][0],
        "code_verifier": verifier,
        "redirect_uri": redirect,
        "grant_type": "authorization_code",
    })
    save_token(tok)
    print("ok: token saved", file=sys.stderr)


def get(path, token, **params):
    req = urllib.request.Request(f"{API}{path}?{urllib.parse.urlencode(params)}",
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def declined(ev):
    return any(a.get("self") and a.get("responseStatus") == "declined" for a in ev.get("attendees", []))


def events():
    token = access_token()
    now = datetime.now(timezone.utc)
    out = []
    for cal in get("/users/me/calendarList", token).get("items", []):
        if not cal.get("selected"):
            continue
        items = get(f"/calendars/{urllib.parse.quote(cal['id'])}/events", token,
                    timeMin=now.isoformat(), timeMax=(now + HORIZON).isoformat(),
                    singleEvents="true", orderBy="startTime", maxResults=50).get("items", [])
        for ev in items:
            start = ev.get("start", {}).get("dateTime")  # skips all-day events
            if not start or ev.get("status") == "cancelled" or declined(ev):
                continue
            out.append({
                "id": ev["id"],
                "title": ev.get("summary", "(no title)"),
                "start": start,
                "calendar": cal.get("summary", ""),
                "link": ev.get("hangoutLink") or ev.get("htmlLink", ""),
            })
    out.sort(key=lambda e: datetime.fromisoformat(e["start"]))
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "auth":
        auth()
    elif cmd == "events":
        try:
            print(json.dumps({"events": events()}))
        except Reauth:
            print(json.dumps({"error": "reauth"}))
            sys.exit(2)
        except Exception as e:
            print(json.dumps({"error": "error", "detail": str(e)}))
            sys.exit(1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
