# VANISH-Digital-Forensic-Audit
Evidence-based forensic audit framework for verifying digital data erasure across multi-device and cloud environments.

# VANISH
### Beyond the Delete Button
**An Evidence-Based Forensic Audit Framework for Verifying Digital Data Erasure Across Multi-Device and Cloud Environments**

VANISH is a digital forensic audit prototype designed to examine digital evidence integrity, evaluate sanitization outcomes, assess cloud-related erasure conditions, and maintain traceable chain-of-custody records.

The project focuses on helping investigators and forensic practitioners assess whether digital evidence has remained intact and whether data-erasure verification procedures provide meaningful results.

---

## Overview

Digital data deletion does not necessarily guarantee permanent erasure. Data may remain recoverable, evidence files may be modified, and cloud environments may introduce additional verification challenges.

VANISH provides a centralized forensic auditing interface with multiple modules for examining evidence integrity, sanitization outcomes, cloud-related verification conditions, and evidence handling records.

The framework combines cryptographic verification, structured audit records, verification procedures, and reporting capabilities within a web-based prototype.

---

## Features

### 1. Evidence Management
- Evidence file collection and registration
- Evidence metadata management
- File identification and tracking
- Evidence organization for forensic auditing

### 2. Integrity Verification
- SHA-256 cryptographic hashing
- Expected hash versus actual hash comparison
- Detection of modified evidence
- Identification of missing evidence
- Integrity verification status reporting

### 3. Sanitization Verification
- Sanitization assessment workflows
- Verification of sanitization outcomes
- Structured sanitization reports
- Verification status and result analysis

### 4. Cloud Verification
- Cloud-related erasure verification checks
- Rule-based analysis of cloud verification conditions
- Structured cloud assessment results

*Cloud verification is currently rules-based and does not directly connect to cloud service providers.*

### 5. Chain of Custody
- Traceable evidence handling records
- Audit event logging
- Integrity verification of custody records
- Chain verification status
- Identification of integrity-related issues in custody records

### 6. Forensic Analysis
- Automated analysis of verification outcomes
- Risk and severity assessment
- Findings generation
- Recommendations based on analysis results

### 7. Reports
- Integrity verification reports
- Sanitization reports
- Forensic findings
- Structured audit results

### 8. Dashboard
- Centralized forensic audit overview
- Evidence and verification status
- Module navigation
- System status information

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React |
| Frontend build tool | Vite |
| Styling | CSS |
| Backend | Python |
| Backend API | FastAPI |
| Integrity hashing | SHA-256 |
| Testing | Pytest |
| Data handling | Python-based backend and database layer |

---

## Architecture

VANISH follows a frontend-backend architecture.

```text
                 VANISH
                   |
        +----------+----------+
        |                     |
     Frontend              Backend
     React + Vite          FastAPI
        |                     |
        | HTTP API             |
        +----------+----------+
                   |
       +-----------+------------+
       |           |            |
   Evidence    Integrity    Sanitization
   Management  Verification Verification
       |           |            |
       +-----------+------------+
                   |
       +-----------+------------+
       |           |            |
     Cloud     Chain of       Reports
  Verification  Custody      & Analysis
```

### Backend Modules

The backend is organized into modules responsible for:

- Evidence collection
- Hash verification
- Integrity verification
- Chain-of-custody management
- Cloud analysis
- Sanitization verification
- Forensic analysis
- Report generation

### Frontend Modules

The frontend provides a graphical interface for:

- Dashboard
- Evidence
- Integrity Verification
- Sanitization
- Cloud Verification
- Chain of Custody
- Reports

---

## Installation and Setup

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Anshika-123-tech/VANISH-Digital-Forensic-Audit.git
```

Navigate into the project:

```bash
cd VANISH-Digital-Forensic-Audit
```

### 2. Backend Setup

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Install the backend dependencies required by the project.

Start the FastAPI backend from the project root:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Backend API:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

### 3. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## Testing

VANISH includes automated backend tests covering core functionality and API behavior.

Test categories include:

- Evidence collection
- Evidence scanning
- Evidence upload
- Integrity verification
- Chain-of-custody records
- Chain integrity
- Cloud analysis
- Cloud API
- Sanitization verification
- Report generation
- Security-related verification scenarios

Run the backend test suite from the project root:

```bash
pytest backend/tests -v
```

---

## Verification Scenarios

The prototype supports verification scenarios involving:

| Scenario | Expected Outcome |
|---|---|
| Original evidence remains unchanged | Integrity verified |
| Evidence file is modified | Integrity failure |
| Evidence file is missing | Missing evidence detected |
| Custody records remain valid | Chain verified |
| Custody record integrity is compromised | Integrity issue detected |

---

## Security and Limitations

VANISH is an academic research prototype and should not be considered a replacement for validated forensic tools or certified sanitization procedures.

- SHA-256 integrity verification identifies changes relative to a recorded hash but does not independently establish authenticity or authorship.
- Sanitization verification results depend on the verification methods and available evidence.
- The prototype cannot independently guarantee physical destruction or complete erasure from every storage medium.
- Cloud verification currently uses rules-based assessment rather than direct integration with cloud provider infrastructure.
- Results should be interpreted alongside established forensic procedures and expert judgment.

---

## Project Purpose

The purpose of VANISH is to explore an evidence-based approach to digital forensic auditing by bringing integrity verification, sanitization assessment, cloud-related checks, and chain-of-custody tracking into a unified framework.

The project demonstrates how structured verification workflows can support transparency, traceability, and more informed forensic assessment of digital data erasure.

---

## Project Status

**Version:** Prototype v1.0  
**Status:** Academic prototype / active development

---

## Author

Developed as an academic digital forensic research project.

---

*VANISH — Beyond the Delete Button.*
