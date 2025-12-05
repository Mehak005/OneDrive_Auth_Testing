# Project 14: Comprehensive Exploration of OneDrive Authorization Enforcement

**Team:** Srinivas Mekala, Mehak Seth  
**Topic:** 1. Comprehensive Exploration of Authorization Enforcement  
**Course:** CSI-524/424

---

## 📅 Project Roadmap & Action Plan

This document outlines the step-by-step plan to automate the testing of OneDrive's access control, ensuring we meet the requirement to "account for all possible variation of factors".

### Phase 1: Infrastructure & Authentication (Current Status: ✅ 90% Complete)
**Goal:** Establish stable, automated connectivity to the OneDrive Graph API.

- [x] **App Registration:** Register App in Azure Portal (Multi-tenant/Personal).
- [x] **Config Setup:** Create `config.py` to separate secrets from code.
- [x] **Authentication Logic:** Implement MSAL flow to handle tokens (Personal/Common endpoint).
- [ ] **Token Refresh:** Ensure the script can run for long periods (handle token expiration).
- [ ] **Rate Limiting:** Add a 1-second `time.sleep()` between requests to respect API limits.

### Phase 2: The "Experiment Matrix" Design (Target: Next 2 Days)
**Goal:** Define exactly *what* we are testing. We need to create a matrix of scenarios to prove "comprehensiveness."

We will automate the creation of the following scenarios:

| ID | Resource Type | Shared With | Role | Expected Result |
|----|--------------|-------------|------|-----------------|
| S1 | File | Teammate (Email) | Read | Can Read / Cannot Write |
| S2 | File | Teammate (Email) | Write| Can Read / Can Write |
| S3 | Folder | Teammate (Email) | Read | Can List Children |
| S4 | File | Public (Link) | Read | Anyone can read |
| S5 | File | "Block" (Unshare) | None | Access Denied (403) |

*Action Item:* Create a Python dictionary/JSON file (`scenarios.json`) that represents this table so our script can load it dynamically.

### Phase 3: Automation Development (Core Coding)
**Goal:** Write the Python scripts that execute the experiment loop.

#### Script A: `setup_environment.py` (The "Owner")
1.  Reads `scenarios.json`.
2.  **Uploads** unique test files for each scenario (e.g., `test_file_S1.txt`, `test_file_S2.txt`).
3.  **Applies Permissions** using the `/invite` API endpoint.
4.  **Logs** the `file_id` and `permission_id` to a `state.json` file.

#### Script B: `audit_permissions.py` (The "Oracle")
1.  Reads `state.json`.
2.  Queries the `/permissions` endpoint for each file.
3.  **Compares** the actual API result against the `Expected Result` from the matrix.
4.  Flags any "Inconsistencies" (e.g., We requested 'Read', but API says 'Write').

#### Script C: `verify_access.py` (The "Audience" - *Optional/Bonus*)
1.  Authenticates as the *other* user (Srinivas).
2.  Attempts to actually download/edit the files.
3.  Confirms if enforcement matches the policy.

### Phase 4: Data Collection & Analysis
**Goal:** Run the scripts and generate the report data.

- [ ] Run the full test suite (50+ scenarios).
- [ ] Output results to `results.csv`.
- [ ] Analyze: Did we find any cases where the API metadata didn't match the request?

### Phase 5: Reporting & Video
**Goal:** Final deliverables.

- [ ] **Data Visualization:** Create a simple chart/table summarizing Pass/Fail rates.
- [ ] **Report Writing:** Fill out the "Methodology" and "Experimental Setup" sections in the final report.
- [ ] **Screencast:** Record a 5-minute video showing the script running (creating files, sharing them, verifying them).

---

## 🛠️ Technical Architecture

### Directory Structure
```text
/
├── config.py           # API Secrets (Ignored by Git)
├── msal_auth.py        # Authentication Handler
├── main_experiment.py  # The loop that runs Scenarios S1-S5
├── scenarios.json      # Configuration of tests
├── results/            # Folder for logs and CSV outputs
├── README.md           # This file
└── requirements.txt    # dependencies (msal, requests)