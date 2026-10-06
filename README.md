# SMART on FHIR Integration Lab: Reference Sandbox & Epic on FHIR

Hands-on implementation of the **SMART App Launch Framework** and **OAuth 2.0 Authorization Code Flow with PKCE** (RFC 7636) across two healthcare environments:
1. **SMART Health IT Reference Sandbox** (`launch.smarthealthit.org`)
2. **Epic Systems Sandbox** (`open.epic.com` / `fhir.epic.com`)

Built entirely using Linux command-line tools (`curl`) and standard Python 3.

---

## Conceptual Overview: Two Perspectives

### For the Clinician: Understanding Chart Access & Security
* **What is happening here?**  
  When an external application needs to pull a patient's chart from an Electronic Health Record (EHR) system like Epic, it cannot just "see" the database. It must ask for permission first.
* **Why does this matter in practice?**  
  Instead of sharing hospital system credentials or passwords, this workflow uses a delegated digital handshake (OAuth 2.0). When a patient logs into their portal (MyChart) or a physician signs into a workstation, they explicitly review a consent screen that asks: *"Allow Healthcare CLI Integration to view your problem list and vital signs?"*
* **The Clinical Safeguard:**  
  The application is locked inside a digital fence (compartment scoping). In this project, the tool can only read the demographics, active diagnoses (`Condition`), and vitals/labs (`Observation`) of the single selected patient (`fhircamila`). It cannot modify entries, sign notes, access records of any other patient in the facility, or view protected records outside its approved scope.

---

### For the Health Informatician: Technical Architecture & Standards
* **Protocol & Specifications:**  
  * **Transport:** HL7 FHIR Release 4 (R4) over HTTPS (RESTful architecture).
  * **Security Profile:** SMART App Launch Framework (v1/v2), OAuth 2.0 (RFC 6749) with Proof Key for Code Exchange (PKCE, RFC 7636).
* **Identity & Authentication:**  
  Discovery endpoints (`/.well-known/smart-configuration`) are dynamically queried to retrieve the authorization gateway (`/authorize`) and token issuing authority (`/token`).
* **Scoping Matrix:**  
  * `openid fhirUser`: Resolves and verifies the authenticated identity compartment.
  * `patient/Patient.read`: Access to core demographics under the `Patient` resource.
  * `patient/Condition.read`: Read access to clinical problem lists and encounter diagnoses.
  * `patient/Observation.read`: Filtered access to vitals and laboratory results.
* **PKCE Mechanics:**  
  Because CLI clients are public clients unable to safeguard client secrets, authorization code interception is mitigated using SHA-256 code verifier/challenge pairs (`code_challenge_method=S256`).

---

## Repository Structure

```text
smart-on-fhir-oauth-sandboxes/
├── .gitignore
├── README.md
├── sandbox-1-smart-healthit/
│   ├── auth_flow.py               # PKCE generation, local callback listener, token exchange
│   └── query_clinical_data.py     # FHIR R4 queries (Patient, Condition, Observation)
└── sandbox-2-epic/
    ├── auth_flow.py               # Epic OAuth 2.0 PKCE client & redirect receiver
    └── query_clinical_data.py     # Epic non-production R4 clinical compartment queries
Sandbox 1: SMART Health IT Reference Sandbox
The SMART Health IT launcher serves as the neutral reference implementation for testing SMART on FHIR compliance without proprietary vendor restrictions.

Workflow Sequence
Dynamic Discovery: Reads /.well-known/smart-configuration to extract the authorization_endpoint and token_endpoint.

PKCE Key Generation: Creates an unhashed code_verifier (high-entropy 32-byte string) and an S256 code_challenge.

Interactive Launch: Launches an authorization request with scopes openid fhirUser launch/patient patient/*.read.

Local Callback Listener: Python spins up a temporary single-request HTTP listener on 127.0.0.1:8080/callback to capture the code parameter.

Token Exchange: Performs a direct POST to the token endpoint with the code_verifier to retrieve the Bearer access token and selected patient ID.

Clinical Queries: Queries /Patient/{id}, /Condition?patient={id}, and /Observation?patient={id}.

Running Sandbox 1
Bash
cd sandbox-1-smart-healthit

# 1. Run the interactive auth flow & follow prompt instructions
python3 auth_flow.py

# 2. Query clinical resources using the received token
python3 query_clinical_data.py
Sandbox 2: Epic on FHIR (open.epic.com)
Connects to Epic's real-world non-production sandbox environment. Unlike the reference launcher, Epic requires formal application registration, strict redirect URI validation, and pre-selected API contracts.

Configuration Details
Environment: Non-Production Epic Sandbox Gateway

FHIR Base Endpoint: https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4

App Audience: Patients (MyChart Standalone Flow)

Client ID: fde57aec-73a5-4190-84c0-7f1cd9ed1317

Redirect URI: http://127.0.0.1:8080/callback

Test Patient Persona: fhircamila / epicepic1

Running Sandbox 2
Bash
cd sandbox-2-epic

# 1. Run the Epic auth script
python3 auth_flow.py
# -> Open the printed URL in your browser
# -> Login as 'fhircamila' with password 'epicepic1'
# -> Authorize the app; the callback listener saves epic_token_response.json

# 2. Query Epic's non-production FHIR R4 server
python3 query_clinical_data.py
Sample Output from Epic R4 Server
Plaintext
[+] Querying Epic for Patient ID: erXuFYUfucBZaryVksYEcMg3

Patient: Camila Lopez (female, DOB: 1986-04-16)

Conditions (3):
 - Essential hypertension
 - Type 2 diabetes mellitus
 - Chronic low back pain

Vital Signs (5):
 - Blood Pressure: 124/82 mmHg
 - Heart Rate: 72 beats/min
 - Body Temperature: 36.8 Cel
 - Respiratory Rate: 16 breaths/min
 - Body Weight: 68.2 kg
Security & Operational Safeguards
Zero Secrets in Repository: Public clients using PKCE eliminate the risk of committing hardcoded client secrets.

Token Isolation: Tokens are stored locally in uncommitted JSON files (.gitignore excludes *token_response.json).

Audience Validation: Every auth request explicitly sends the aud parameter matching the target FHIR server, protecting against malicious redirect and token relay attacks.
