import base64
import hashlib
import http.server
import json
import secrets
import urllib.parse
import urllib.request

FHIR_BASE = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
AUTH_ENDPOINT = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize"
TOKEN_ENDPOINT = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"

CLIENT_ID = "fde57aec-73a5-4190-84c0-7f1cd9ed1317"
REDIRECT_URI = "http://127.0.0.1:8080/callback"
SCOPES = "openid fhirUser patient/Patient.read patient/Observation.read patient/Condition.read"

def main():
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

    auth_url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
    print("=" * 70)
    print("[*] 1. Open this URL in your browser:")
    print(auth_url)
    print("\n[*] 2. Login with Username: fhircamila | Password: epicepic1")
    print("=" * 70)

    auth_code = None

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            global auth_code
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            auth_code = params.get("code", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Epic Authorization Code Captured! Return to terminal.</h1>")

    server = http.server.HTTPServer(("127.0.0.1", 8080), CallbackHandler)
    print("\n[*] Waiting for redirect on http://127.0.0.1:8080/callback ...")
    server.handle_request()

    if not auth_code:
        print("[-] Failed to capture code.")
        return

    print(f"\n[+] Auth code captured: {auth_code[:20]}...")
    print("[*] Exchanging code for Access Token...")

    token_payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier
    }).encode("utf-8")

    token_req = urllib.request.Request(
        TOKEN_ENDPOINT,
        data=token_payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    with urllib.request.urlopen(token_req) as resp:
        tokens = json.loads(resp.read().decode())
        with open("epic_token_response.json", "w") as f:
            json.dump(tokens, f, indent=2)
        print("\n[+] SUCCESS! Saved tokens to epic_token_response.json")
        print(f"    Patient ID: {tokens.get('patient')}")

if __name__ == "__main__":
    main()
