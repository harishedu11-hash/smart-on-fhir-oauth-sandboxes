import base64
import hashlib
import http.server
import json
import secrets
import urllib.parse
import urllib.request
import webbrowser

FHIR_BASE = "https://launch.smarthealthit.org/v/r4/sim/WzIsImQ0ZmIzYmJhLTczYTktNGI4Mi1hMGJjLTY3OGQ0N2YzODZiNCIsIiIsIkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwiIl0/fhir"
REDIRECT_URI = "http://127.0.0.1:8080/callback"
CLIENT_ID = "my-cli-app"
SCOPES = "openid fhirUser launch/patient patient/*.read"

def main():
    print("[1] Fetching SMART configuration...")
    config_url = f"{FHIR_BASE}/.well-known/smart-configuration"
    req = urllib.request.Request(config_url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        smart_config = json.loads(resp.read().decode())
    
    auth_endpoint = smart_config["authorization_endpoint"]
    token_endpoint = smart_config["token_endpoint"]

    # Generate PKCE
    verifier_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).decode().rstrip("=")
    challenge_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_hash).decode().rstrip("=")

    state = secrets.token_hex(8)
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "aud": FHIR_BASE,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    auth_url = f"{auth_endpoint}?{urllib.parse.urlencode(params)}"

    print("\n[2] Open this URL in your browser to authorize:")
    print(auth_url)

    # Temporary HTTP server to receive the callback
    auth_code = None
    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            parsed = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed.query)
            auth_code = query_params.get("code", [None])[0]
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization complete! Return to terminal.</h2>")

    server = http.server.HTTPServer(("127.0.0.1", 8080), CallbackHandler)
    print("\n[*] Waiting for redirect on http://127.0.0.1:8080/callback ...")
    server.handle_request()

    if not auth_code:
        print("[-] Failed to capture authorization code.")
        return

    print(f"\n[3] Exchanging authorization code for access token...")
    token_payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier
    }).encode("utf-8")

    token_req = urllib.request.Request(
        token_endpoint,
        data=token_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    with urllib.request.urlopen(token_req) as resp:
        tokens = json.loads(resp.read().decode())

    with open("token_response.json", "w") as f:
        json.dump(tokens, f, indent=2)

    print("[+] Successfully saved token_response.json!")
    print(f"    Patient ID: {tokens.get('patient')}")

if __name__ == "__main__":
    main()
