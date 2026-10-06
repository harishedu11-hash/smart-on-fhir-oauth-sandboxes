import json
import urllib.request

FHIR_BASE = "https://launch.smarthealthit.org/v/r4/sim/WzIsImQ0ZmIzYmJhLTczYTktNGI4Mi1hMGJjLTY3OGQ0N2YzODZiNCIsIiIsIkFVVE8iLDAsMCwwLCIiLCIiLCIiLCIiLCIiLCIiLCIiLDAsMSwiIl0/fhir"

with open("token_response.json") as f:
    token_data = json.load(f)

access_token = token_data.get("access_token")
patient_id = token_data.get("patient")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/fhir+json"
}

def fetch_fhir(endpoint):
    req = urllib.request.Request(f"{FHIR_BASE}/{endpoint}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

# Patient
pt = fetch_fhir(f"Patient/{patient_id}")
name = pt.get("name", [{}])[0]
print(f"Patient: {' '.join(name.get('given', []))} {name.get('family', '')} ({pt.get('gender')}, DOB: {pt.get('birthDate')})")

# Conditions
cond_bundle = fetch_fhir(f"Condition?patient={patient_id}")
print(f"\nConditions ({len(cond_bundle.get('entry', []))}):")
for entry in cond_bundle.get("entry", [])[:5]:
    c = entry.get("resource", {})
    text = c.get("code", {}).get("text") or c.get("code", {}).get("coding", [{}])[0].get("display")
    print(f" - {text}")
