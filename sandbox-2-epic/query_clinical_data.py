import json
import urllib.request

with open("epic_token_response.json") as f:
    token_data = json.load(f)

access_token = token_data.get("access_token")
patient_id = token_data.get("patient")
epic_fhir_base = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/fhir+json"
}

def get_fhir(path):
    url = f"{epic_fhir_base}/{path}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print(f"[+] Querying Epic for Patient ID: {patient_id}\n")

# Demographics
pt = get_fhir(f"Patient/{patient_id}")
name = pt.get("name", [{}])[0]
print(f"Patient: {' '.join(name.get('given', []))} {name.get('family', '')} ({pt.get('gender')}, DOB: {pt.get('birthDate')})\n")

# Conditions
cond_bundle = get_fhir(f"Condition?patient={patient_id}")
print(f"Conditions ({len(cond_bundle.get('entry', []))}):")
for entry in cond_bundle.get("entry", [])[:5]:
    c = entry.get("resource", {})
    text = c.get("code", {}).get("text") or c.get("code", {}).get("coding", [{}])[0].get("display")
    print(f" - {text}")

# Vital Signs
obs_bundle = get_fhir(f"Observation?patient={patient_id}&category=vital-signs")
print(f"\nVital Signs ({len(obs_bundle.get('entry', []))}):")
for entry in obs_bundle.get("entry", [])[:5]:
    o = entry.get("resource", {})
    disp = o.get("code", {}).get("text") or o.get("code", {}).get("coding", [{}])[0].get("display")
    val = o.get("valueQuantity", {}).get("value", "N/A")
    unit = o.get("valueQuantity", {}).get("unit", "")
    print(f" - {disp}: {val} {unit}")
