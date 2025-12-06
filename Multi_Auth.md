# Multi-User Authorization Testing - Complete Guide

## Table of Contents
1. [The Problem We're Solving](#the-problem-were-solving)
2. [The Solution Approach](#the-solution-approach)
3. [System Architecture](#system-architecture)
4. [Complete Setup Guide](#complete-setup-guide)
5. [Code Explanation](#code-explanation)
6. [How to Run](#how-to-run)
7. [Understanding Results](#understanding-results)
8. [Troubleshooting](#troubleshooting)

---

## The Problem We're Solving

### Original Issue

When testing authorization with a single user account, we encountered a critical flaw:

**Single-User Testing Flow:**
```
You (Owner) → Get Token → Test Actions → All Return ALLOW
```

**Why Everything Shows ALLOW:**
- You create the test files → You're the owner
- You test with YOUR token → Owner token
- Owner has full permissions to their own files
- Result: Every test passes, no bugs found

**Example:**
```python
# Test: Can external user read private file?
# Expected: DENY
# Actual: ALLOW (because we're testing with owner token!)
# Test shows PASS but it's wrong!
```

This doesn't test real authorization because we're always the owner.

---

## The Solution Approach

### Multi-User Testing Strategy

We need to test with DIFFERENT user accounts to simulate real-world scenarios:

**Multi-User Testing Flow:**
```
Owner (You) → Creates Files
Collaborator (Teammate) → Tries to Access Files
Compare: What SHOULD happen vs What ACTUALLY happens
```

**User Roles We Need:**

1. **Owner (You - Mehak)**
   - Creates all test files
   - Has full permissions
   - Tests "owner" scenarios

2. **Collaborator (Srinivas)**
   - Different account
   - Limited permissions
   - Tests "collaborator", "org_member", and "external" scenarios

### Why This Works

```
Test: Can external user read private file?

OLD WAY (Wrong):
- Test with: Owner token (your token)
- Result: ALLOW (owner can read their own files)
- Test Status: PASS (but meaningless!)

NEW WAY (Correct):
- Test with: Collaborator token (Srinivas's token)
- Result: DENY (non-owner can't read private files)
- Test Status: FAIL (found a real authorization boundary!)
```

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure AD Application                      │
│  (Authorization Testing Framework - Your Registered App)    │
│                                                              │
│  Credentials:                                                │
│  - CLIENT_ID                                                 │
│  - CLIENT_SECRET                                             │
│  - TENANT_ID                                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ (Both users authenticate here)
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌─────────────────┐                   ┌─────────────────┐
│  Owner Account  │                   │ Collaborator    │
│  (Mehak)        │                   │ (Srinivas)      │
│                 │                   │                 │
│  Gets token_    │                   │  Gets token_    │
│  owner.txt      │                   │  collaborator   │
└────────┬────────┘                   └────────┬────────┘
         │                                     │
         │                                     │
         ▼                                     ▼
┌─────────────────┐                   ┌─────────────────┐
│ Owner's         │                   │ Collaborator's  │
│ OneDrive        │                   │ OneDrive        │
│                 │                   │                 │
│ Contains:       │                   │ Contains:       │
│ - Test files    │◄──────shares──────┤ - Can access    │
│ - Created by    │                   │   some files    │
│   owner         │                   │ - Limited perms │
└─────────────────┘                   └─────────────────┘
```

### Testing Flow

```
1. SETUP PHASE
   ┌──────────────────────────────────────────────┐
   │ multi_user_auth.py                           │
   │                                              │
   │ Step 1: Owner signs in → token_owner.txt    │
   │ Step 2: Collab signs in → token_collab.txt  │
   └──────────────────────────────────────────────┘

2. FILE CREATION PHASE
   ┌──────────────────────────────────────────────┐
   │ test_framework_multiuser.py                  │
   │                                              │
   │ Uses: token_owner.txt                        │
   │ Creates in Owner's OneDrive:                 │
   │   - multiuser_test_private_file.txt          │
   │   - multiuser_test_shared_file.txt           │
   │   - multiuser_test_org_public_file.txt       │
   │   - multiuser_test_public_file.txt           │
   │                                              │
   │ Shares: 'shared' file with collaborator      │
   └──────────────────────────────────────────────┘

3. TESTING PHASE
   ┌──────────────────────────────────────────────┐
   │ For each scenario:                           │
   │                                              │
   │ IF audience == 'owner':                      │
   │    Use token_owner.txt                       │
   │    Test action on file                       │
   │                                              │
   │ ELSE (collaborator/org_member/external):     │
   │    Use token_collaborator.txt                │
   │    Test action on file                       │
   │                                              │
   │ Compare: Expected vs Actual                  │
   │ Record: PASS or FAIL                         │
   └──────────────────────────────────────────────┘

4. RESULTS PHASE
   ┌──────────────────────────────────────────────┐
   │ Analyze results:                             │
   │                                              │
   │ Owner tests: Should all PASS                 │
   │   (owner has full access)                    │
   │                                              │
   │ Collaborator tests: Some PASS, some FAIL     │
   │   (shows real authorization boundaries!)     │
   │                                              │
   │ Export to: multiuser_test_results.json       │
   └──────────────────────────────────────────────┘
```

---

## Complete Setup Guide

### Prerequisites

1. **Two Microsoft Accounts:**
   - Your account: mehak.seth2023@gmail.com (Owner)
   - Teammate's account: srinivasmekala1227@gmail.com (Collaborator)

2. **Azure App Already Set Up:**
   - CLIENT_ID, CLIENT_SECRET, TENANT_ID in config.py
   - Both accounts can authenticate with the app

3. **Python Packages:**
   ```bash
   pip install msal requests matplotlib pandas
   ```

### File Structure

Your project should have:

```
onedrive-authorization-testing/
├── config.py                          # Azure app credentials
├── policy_model.py                    # Authorization rules
├── onedrive_client.py                 # OneDrive API wrapper
├── multi_user_auth.py                 # NEW: Get tokens for both users
├── test_framework_multiuser.py        # NEW: Multi-user testing
├── visualizations.py                  # Generate charts
├── token_owner.txt                    # Generated: Owner's token
├── token_collaborator.txt             # Generated: Collaborator's token
├── user_owner.json                    # Generated: Owner info
├── user_collaborator.json             # Generated: Collaborator info
└── results/
    └── multiuser_test_results.json    # Generated: Test results
```

---

## Code Explanation

### 1. multi_user_auth.py

**Purpose:** Get access tokens for both owner and collaborator accounts.

**How It Works:**

```python
# Step 1: Create MSAL app with your Azure credentials
app = PublicClientApplication(
    config.CLIENT_ID,
    authority=config.AUTHORITY_URL  # "https://login.microsoftonline.com/common"
)

# Step 2: Request token interactively (opens browser)
scopes = ["Files.ReadWrite.All", "Sites.ReadWrite.All", "User.Read"]
result = app.acquire_token_interactive(scopes=scopes)

# Step 3: Save token to file
if "access_token" in result:
    filename = f'token_{user_type}.txt'  # e.g., token_owner.txt
    with open(filename, 'w') as f:
        f.write(result['access_token'])
```

**Key Concepts:**

- **Interactive authentication**: Opens browser for user to sign in
- **User type parameter**: Distinguishes owner from collaborator
- **Token files**: Separate files for each user's token
  - `token_owner.txt` - Contains owner's access token
  - `token_collaborator.txt` - Contains collaborator's access token

**Usage:**
```bash
python multi_user_auth.py
# Browser opens → Sign in as Mehak (owner)
# Browser opens again → Sign in as Srinivas (collaborator)
# Result: Two token files created
```

---

### 2. test_framework_multiuser.py

**Purpose:** Test authorization using both user tokens.

**Key Components:**

#### A. Initialization

```python
class MultiUserTestFramework:
    def __init__(self, owner_token, collaborator_token):
        # Create policy model (defines expected behavior)
        self.policy = AuthorizationPolicy()
        
        # Create OneDrive clients for each user
        self.owner_client = OneDriveClient(owner_token)
        self.collab_client = OneDriveClient(collaborator_token)
        
        # Storage for results
        self.test_results = []
        self.test_files = {}
```

**Why two clients?**
- `owner_client`: Makes API calls as owner (Mehak)
- `collab_client`: Makes API calls as collaborator (Srinivas)

#### B. Setup Test Environment

```python
def setup_test_environment(self):
    # Get user info to confirm who's who
    owner_info = self.owner_client.get_user_info()
    collab_info = self.collab_client.get_user_info()
    
    print(f"Owner: {owner_info['email']}")
    print(f"Collaborator: {collab_info['email']}")
    
    # Create test files as OWNER (using owner_client)
    for visibility in ['private', 'shared', 'org_public', 'public']:
        filename = f"multiuser_test_{visibility}_file.txt"
        content = f"Test file for {visibility} testing"
        
        # IMPORTANT: Uses owner_client to create files
        result = self.owner_client.create_file(filename, content)
        
        if result['status_code'] in [200, 201]:
            file_id = result['data']['id']
            self.test_files[visibility] = {
                'id': file_id,
                'name': filename
            }
            
            # Share 'shared' files with collaborator
            if visibility == 'shared':
                self.owner_client.share_file(file_id)
```

**What happens:**
1. Owner creates 4 test files in THEIR OneDrive
2. Files are tagged by visibility level
3. 'Shared' files get sharing links created
4. File IDs are stored for testing

#### C. Test Individual Scenarios

```python
def test_scenario(self, scenario):
    # Extract scenario details
    visibility = scenario['visibility']  # e.g., 'private'
    action = scenario['action']          # e.g., 'read'
    audience = scenario['audience']      # e.g., 'collaborator'
    expected = scenario['expected']      # e.g., 'DENY'
    
    # Get the file to test
    file_id = self.test_files[visibility]['id']
    
    # KEY DECISION: Which token to use?
    if audience == 'owner':
        client = self.owner_client      # Use owner's token
        test_user = 'owner'
    else:
        client = self.collab_client     # Use collaborator's token
        test_user = 'collaborator'
    
    # Execute the action with chosen token
    if action == 'read':
        response = client.read_file(file_id)
    elif action == 'write':
        response = client.update_file(file_id, "Updated content")
    elif action == 'delete':
        response = client.read_file(file_id)  # Test access
    elif action == 'share':
        response = client.share_file(file_id)
    
    # Determine actual result from HTTP status
    if response['status_code'] in [200, 201]:
        actual = 'ALLOW'
    elif response['status_code'] in [403, 404, 401]:
        actual = 'DENY'
    else:
        actual = 'UNKNOWN'
    
    # Compare expected vs actual
    passed = (expected == actual)
    
    return {
        'scenario_id': scenario['scenario_id'],
        'expected': expected,
        'actual': actual,
        'passed': passed,
        'tested_by': test_user
    }
```

**Critical Logic:**

```
IF testing owner scenario:
    Use owner token → Should ALLOW
ELSE testing non-owner scenario:
    Use collaborator token → May DENY
```

**Example Test Flow:**

```
Scenario 1: Owner reads private file
- audience = 'owner'
- action = 'read'
- visibility = 'private'
- Uses: owner_client (owner's token)
- Expected: ALLOW
- Actual: ALLOW (200 OK)
- Result: PASS ✓

Scenario 2: Collaborator reads private file
- audience = 'collaborator'
- action = 'read'
- visibility = 'private'
- Uses: collab_client (collaborator's token)
- Expected: DENY
- Actual: DENY (403 Forbidden)
- Result: PASS ✓ (found real authorization!)

Scenario 3: Collaborator reads shared file
- audience = 'collaborator'
- action = 'read'
- visibility = 'shared'
- Uses: collab_client (collaborator's token)
- Expected: ALLOW
- Actual: ALLOW (200 OK)
- Result: PASS ✓
```

#### D. Run All Tests

```python
def run_all_tests(self):
    # Generate all 64 scenarios from policy model
    scenarios = self.policy.generate_all_scenarios()
    
    # Test each scenario
    for scenario in scenarios:
        result = self.test_scenario(scenario)
        self.test_results.append(result)
```

**What gets tested:**

```
64 Total Scenarios = 4 audiences × 4 visibility × 4 actions

Audiences: owner, collaborator, org_member, external
Visibility: private, shared, org_public, public
Actions: read, write, delete, share

Examples:
- owner read private
- owner write private
- collaborator read private  ← Tests with collab token!
- collaborator write private ← Tests with collab token!
- external read private      ← Tests with collab token!
... (64 total)
```

#### E. Analyze Results

```python
def analyze_results(self):
    total = len(self.test_results)
    passed = sum(1 for r in self.test_results if r['passed'])
    failed = total - passed
    
    print(f"Total: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    # Group failures by user type
    failures = [r for r in self.test_results if not r['passed']]
    
    by_audience = {}
    for f in failures:
        audience = f['scenario']['audience']
        by_audience[audience] = by_audience.get(audience, 0) + 1
    
    print("\nFailures by User Type:")
    for audience, count in by_audience.items():
        print(f"  {audience}: {count} bugs")
```

---

### 3. How User Mapping Works

Since we only have 2 accounts but need to test 4 user types:

```python
# User Type Mapping
scenarios = [
    {'audience': 'owner'},         # → Uses owner_client (Mehak's token)
    {'audience': 'collaborator'},  # → Uses collab_client (Srinivas's token)
    {'audience': 'org_member'},    # → Uses collab_client (Srinivas's token)
    {'audience': 'external'},      # → Uses collab_client (Srinivas's token)
]

# In test_scenario():
if audience == 'owner':
    client = self.owner_client
else:
    # All non-owner types use collaborator client
    client = self.collab_client
```

**Why this works:**

- **Owner** = Special case, needs owner token
- **Collaborator/Org Member/External** = All are "non-owners" with limited access
- Testing with one "non-owner" account reveals authorization boundaries

**Real-World Analogy:**

```
Owner = House owner (has all keys)
Collaborator/Org/External = Visitors (limited access)

To test security:
- Test owner with their key (should open everything)
- Test visitors with visitor pass (should be restricted)

Don't need 3 different visitor types to test basic access control.
```

---

## How to Run

### Step 1: Get Tokens

```bash
python multi_user_auth.py
```

**What happens:**
1. Script starts
2. Prompts: "Sign in as OWNER"
3. Browser opens → You (Mehak) sign in
4. Token saved to `token_owner.txt`
5. Prompts: "Sign in as COLLABORATOR"
6. Browser opens → Srinivas signs in
7. Token saved to `token_collaborator.txt`

**Verify:**
```bash
ls -la token_*.txt
# Should see:
# token_owner.txt
# token_collaborator.txt
```

---

### Step 2: Run Multi-User Tests

```bash
python test_framework_multiuser.py
```

**What happens:**

```
1. Load Tokens
   ✓ Loaded owner token
   ✓ Loaded collaborator token

2. Setup Test Environment
   Owner: mehak.seth2023@gmail.com
   Collaborator: srinivasmekala1227@gmail.com
   Creating test files (as owner)...
     ✓ Created private file
     ✓ Created shared file
     ✓ Created org_public file
     ✓ Created public file

3. Run Tests (64 scenarios)
   Progress: 10/64...
   Progress: 20/64...
   ...
   Progress: 64/64
   Completed!

4. Results
   Total: 64
   Passed: 45 (70.3%)
   Failed: 19 (29.7%)
   
   BUGS FOUND: 19
   
   Failures by User Type:
     collaborator: 8 bugs
     external: 7 bugs
     org_member: 4 bugs
   
   Example bugs:
     1. collaborator write private (Expected: DENY, Actual: ALLOW)
     2. external read private (Expected: DENY, Actual: ALLOW)
     ...

5. Export Results
   ✓ Results saved to: results/multiuser_test_results.json
```

---

### Step 3: Generate Visualizations

```bash
python visualizations.py
```

Creates charts showing:
- Overall pass/fail summary
- Failures by user type
- Failures by action
- Heatmap of authorization issues

---

## Understanding Results

### Good Results (Multi-User Testing Working)

```json
{
  "summary": {
    "total": 64,
    "passed": 45,
    "failed": 19
  },
  "results": [
    {
      "scenario_id": 1,
      "scenario": {
        "audience": "owner",
        "visibility": "private",
        "action": "read"
      },
      "expected": "ALLOW",
      "actual": "ALLOW",
      "passed": true,
      "tested_by": "owner"
    },
    {
      "scenario_id": 17,
      "scenario": {
        "audience": "collaborator",
        "visibility": "private",
        "action": "read"
      },
      "expected": "DENY",
      "actual": "DENY",
      "passed": true,
      "tested_by": "collaborator"
    }
  ]
}
```

**What this means:**
- Owner tests (16 scenarios): All PASS (owner has full access)
- Collaborator tests (48 scenarios): Mixed results (shows real authorization!)
- Failed tests = Found real authorization boundaries
- This is GOOD - showing actual OneDrive behavior

---

### Bad Results (Still Using Single User)

```json
{
  "summary": {
    "total": 64,
    "passed": 64,
    "failed": 0
  }
}
```

**What this means:**
- 100% pass rate = Problem!
- Probably testing with owner token for everything
- Not getting real authorization differences

**Fix:**
1. Check `user_owner.json` and `user_collaborator.json`
2. Verify they show DIFFERENT emails
3. Re-run `multi_user_auth.py` with different accounts

---

## Troubleshooting

### Issue: "Token files not found"

**Error:**
```
ERROR: token_owner.txt not found!
Please run: python multi_user_auth.py first
```

**Solution:**
```bash
python multi_user_auth.py
# Sign in as owner, then as collaborator
```

---

### Issue: "All tests show PASS (100%)"

**Problem:** Testing with same user for both owner and collaborator

**Debug:**
```bash
# Check who the tokens belong to
cat user_owner.json
cat user_collaborator.json
```

**If both show same email:**
```json
// user_owner.json
{"username": "mehak.seth2023@gmail.com"}

// user_collaborator.json  
{"username": "mehak.seth2023@gmail.com"}  ← PROBLEM!
```

**Solution:**
```bash
# Delete token files
rm token_*.txt user_*.json

# Re-run authentication
python multi_user_auth.py
# IMPORTANT: Use DIFFERENT accounts!
# First browser: mehak.seth2023@gmail.com
# Second browser: srinivasmekala1227@gmail.com
```

---

### Issue: "Cannot access files"

**Error:**
```
Error testing scenario: 403 Forbidden
```

**Possible causes:**

1. **Tokens expired** (tokens expire after ~1 hour)
   ```bash
   # Get fresh tokens
   python multi_user_auth.py
   ```

2. **Files not shared properly**
   - Check owner's OneDrive
   - Verify files exist
   - Check sharing settings

3. **Wrong file ID**
   - Re-run setup to create fresh test files

---

### Issue: "Too many API requests"

**Error:**
```
Error: 429 Too Many Requests
```

**Solution:**
- Add delays between tests
- Reduce number of test scenarios temporarily
- Wait a few minutes and retry

---

## Key Takeaways

### What Makes This Work

1. **Two Separate Tokens**
   - Owner token = Full access
   - Collaborator token = Limited access

2. **Strategic Token Selection**
   - Owner scenarios → Owner token
   - All other scenarios → Collaborator token

3. **Real Authorization Testing**
   - Owner can do everything (expected)
   - Collaborator gets denied (shows real boundaries)

### What You'll Present

"We implemented multi-user authorization testing using two accounts:
- Owner account creates and owns all test files
- Collaborator account tests access with limited permissions
- Framework automatically uses appropriate tokens for each scenario
- Found X authorization differences between owner and non-owner access
- Results validate OneDrive's authorization enforcement"

### Success Metrics

✅ Two different tokens generated
✅ Files created in owner's OneDrive
✅ Tests run with both tokens
✅ Mixed results (some PASS, some FAIL)
✅ Clear authorization boundaries identified

---

## Next Steps

1. ✅ Run `multi_user_auth.py` to get both tokens
2. ✅ Run `test_framework_multiuser.py` to execute tests
3. ✅ Run `visualizations.py` to create charts
4. ✅ Analyze results in `multiuser_test_results.json`
5. ✅ Document findings for presentation
6. ✅ Prepare demo showing multi-user testing in action

---

## Questions?

Common questions answered:

**Q: Why only 2 accounts instead of 4?**
A: Owner needs special token. All non-owners (collaborator/org/external) can be tested with one "limited access" account.

**Q: What if we don't have 2 accounts?**
A: Create a second free Microsoft account (outlook.com or gmail). Takes 2 minutes.

**Q: Can we use UAlbany accounts?**
A: Yes! If both you and Srinivas have UAlbany accounts with OneDrive for Business.

**Q: Do we need to share credentials?**
A: No! Each person authenticates with THEIR OWN account. You just share the Azure app credentials (CLIENT_ID, etc).

**Q: What if collaborator can access private files?**
A: That's a BUG! That's exactly what we're testing for. Document it as a finding.

---

## Summary

This multi-user testing approach:
- ✅ Solves the "everything shows ALLOW" problem
- ✅ Uses realistic user scenarios (owner vs non-owner)
- ✅ Reveals actual authorization boundaries
- ✅ Generates meaningful test results
- ✅ Demonstrates professional testing methodology

**You're now testing authorization properly!** 🎉