"""One-time Plaid bank authorization setup.

Starts a local Flask server, opens your browser to the Plaid Link UI,
and writes PLAID_ACCESS_TOKEN to your .env file on success.

Run once before using agent.py:
    python household_financial_agent/setup_plaid.py

Sandbox test credentials:
    Username: user_good
    Password: pass_good
    MFA (if prompted): 1234
"""

import os
import pathlib
import re
import threading
import webbrowser

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

load_dotenv()

ENV_FILE = pathlib.Path(__file__).parent / ".env"

_PLAID_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

_LINK_HTML = """<!doctype html>
<html>
<head><title>Plaid Setup</title></head>
<body>
<h2>Connecting your bank account...</h2>
<p>A Plaid Link dialog will open automatically.</p>
<script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
<script>
  const handler = Plaid.create({
    token: "{{ link_token }}",
    onSuccess: function(public_token, metadata) {
      fetch("/exchange", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({public_token: public_token})
      }).then(function() {
        document.body.innerHTML = "<h2>Setup complete!</h2><p>You can close this tab and return to the terminal.</p>";
      });
    },
    onExit: function(err, metadata) {
      document.body.innerHTML = "<h2>Cancelled.</h2><p>Close this tab and re-run setup_plaid.py to try again.</p>";
    }
  });
  handler.open();
</script>
</body>
</html>"""


def _plaid_post(endpoint: str, payload: dict) -> dict:
    plaid_env = os.environ["PLAID_ENV"]
    base_url = _PLAID_HOSTS[plaid_env]
    response = requests.post(
        f"{base_url}{endpoint}",
        json={
            "client_id": os.environ["PLAID_CLIENT_ID"],
            "secret": os.environ["PLAID_SECRET"],
            **payload,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _write_access_token(token: str) -> None:
    """Write or replace PLAID_ACCESS_TOKEN in the .env file."""
    if ENV_FILE.exists():
        content = ENV_FILE.read_text()
        if "PLAID_ACCESS_TOKEN=" in content:
            content = re.sub(r"PLAID_ACCESS_TOKEN=.*", f"PLAID_ACCESS_TOKEN={token}", content)
        else:
            content = content.rstrip("\n") + f"\nPLAID_ACCESS_TOKEN={token}\n"
        ENV_FILE.write_text(content)
    else:
        ENV_FILE.write_text(f"PLAID_ACCESS_TOKEN={token}\n")


def main() -> None:
    for var in ("PLAID_CLIENT_ID", "PLAID_SECRET", "PLAID_ENV"):
        if not os.environ.get(var):
            raise SystemExit(f"Missing required env var: {var}\nCopy .env.example to .env and fill it in.")

    plaid_env = os.environ["PLAID_ENV"]
    print(f"Plaid environment: {plaid_env}")

    print("Creating Link token...")
    link_data = _plaid_post(
        "/link/token/create",
        {
            "user": {"client_user_id": "local-household-user"},
            "client_name": "Household Financial Agent",
            "products": ["transactions"],
            "country_codes": ["US"],
            "language": "en",
        },
    )
    link_token = link_data["link_token"]

    app = Flask(__name__)
    shutdown_event = threading.Event()

    @app.route("/")
    def index():
        return render_template_string(_LINK_HTML, link_token=link_token)

    @app.route("/exchange", methods=["POST"])
    def exchange():
        public_token = request.json["public_token"]
        token_data = _plaid_post(
            "/item/public_token/exchange",
            {"public_token": public_token},
        )
        access_token = token_data["access_token"]
        _write_access_token(access_token)
        print(f"\nSetup complete. PLAID_ACCESS_TOKEN written to {ENV_FILE}")
        # Signal main thread to shut down after responding
        threading.Timer(1.0, shutdown_event.set).start()
        return jsonify({"status": "ok"})

    server_thread = threading.Thread(
        target=lambda: app.run(port=8080, debug=False, use_reloader=False),
        daemon=True,
    )
    server_thread.start()

    print("Opening browser at http://localhost:8080 ...")
    webbrowser.open("http://localhost:8080")
    print("Authorize your bank in the browser. Waiting...")

    shutdown_event.wait()
    print("Done. Run agent.py to start chatting with your financial data.")


if __name__ == "__main__":
    main()
