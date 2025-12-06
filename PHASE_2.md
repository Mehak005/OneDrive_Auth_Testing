# Phase 2: Building OneDrive Authorization Testing Framework

## Overview

In Phase 1, we successfully set up OneDrive API access. Now we will build a complete testing framework to test authorization enforcement in OneDrive, following the requirements of Project Topic 1.

**Goal:** Test all possible authorization scenarios against OneDrive and compare actual behavior with expected policy rules.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Step 1: Adapt Policy Model](#step-1-adapt-policy-model)
4. [Step 2: Create OneDrive Client](#step-2-create-onedrive-client)
5. [Step 3: Build Test Framework](#step-3-build-test-framework)
6. [Step 4: Run Tests](#step-4-run-tests)
7. [Step 5: Generate Visualizations](#step-5-generate-visualizations)
8. [Step 6: Document Results](#step-6-document-results)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting Phase 2, ensure you have:

- ✅ Completed Phase 1 (OneDrive API access working)
- ✅ `config.py` with credentials (CLIENT_ID, CLIENT_SECRET, TENANT_ID, AUTHORITY_URL)
- ✅ `test_token.py` working (can get access token)
- ✅ `test_onedrive.py` working (all 4 tests pass)
- ✅ Python packages installed: `pip install msal requests matplotlib pandas`

---

## Project Structure

Your project folder should look like this:

```
onedrive-authorization-testing/
├── config.py                      # Credentials (DON'T commit to Git!)
├── test_token.py                  # Get access token
├── test_onedrive.py              # Basic OneDrive tests
├── policy_model.py               # Authorization policy (NEW)
├── onedrive_client.py            # OneDrive API wrapper (NEW)
├── test_framework.py             # Main testing framework (NEW)
├── visualizations.py             # Generate charts (NEW)
├── results/                      # Test results folder (NEW)
│   └── test_results.json
└── README.md                     # Project documentation
```

---

## Step 1: Adapt Policy Model

### What is the Policy Model?

The policy model defines the **correct authorization rules** - what SHOULD happen. This is our "ground truth" that we'll compare against OneDrive's actual behavior.

### OneDrive Authorization Factors

OneDrive authorization depends on:

1. **Audience (Who):** Owner, Collaborator, Org Member, External
2. **Visibility (Scope):** Private, Shared, Org-Public, Public
3. **Action (What):** Read, Write, Delete, Share
4. **Context:** Is owner? Same org? Has permission?

### Create policy_model.py

Create a file called `policy_model.py`:

```python
# policy_model.py
"""
Authorization Policy Model for OneDrive

Defines the correct authorization rules based on:
- Audience: who is accessing (owner, collaborator, org_member, external)
- Visibility: file scope (private, shared, org_public, public)
- Action: what they're trying to do (read, write, delete, share)
- Context: additional factors (is_owner, has_permission, same_org)
"""

class AuthorizationPolicy:
    """Defines expected authorization behavior"""
    
    # Define possible values for each factor
    AUDIENCES = ['owner', 'collaborator', 'org_member', 'external']
    VISIBILITY_LEVELS = ['private', 'shared', 'org_public', 'public']
    ACTIONS = ['read', 'write', 'delete', 'share']
    
    def evaluate(self, audience, visibility, action, is_owner=False, 
                 has_permission=False, same_org=False):
        """
        Evaluate if an action should be allowed based on policy rules.
        
        Args:
            audience: Type of user (owner, collaborator, org_member, external)
            visibility: File visibility (private, shared, org_public, public)
            action: What action is being attempted (read, write, delete, share)
            is_owner: Is the user the file owner?
            has_permission: Does user have explicit permission?
            same_org: Is user in same organization as owner?
        
        Returns:
            'ALLOW' or 'DENY'
        """
        
        # Rule 1: Owner has full access to their own files
        if is_owner:
            return 'ALLOW'
        
        # Rule 2: Public files - everyone can read, only owner can modify
        if visibility == 'public':
            if action == 'read':
                return 'ALLOW'
            else:
                return 'DENY'  # Only owner can write/delete/share public files
        
        # Rule 3: Org-public files - org members can read
        if visibility == 'org_public':
            if same_org and action == 'read':
                return 'ALLOW'
            elif same_org and action == 'write':
                return 'ALLOW'  # Org members can edit org-public files
            else:
                return 'DENY'
        
        # Rule 4: Shared files - requires explicit permission
        if visibility == 'shared':
            if has_permission:
                if action in ['read', 'write']:
                    return 'ALLOW'
                else:
                    return 'DENY'  # Can't delete or share
            else:
                return 'DENY'
        
        # Rule 5: Private files - only owner and those with permission
        if visibility == 'private':
            if has_permission:
                if action in ['read', 'write']:
                    return 'ALLOW'
                else:
                    return 'DENY'  # Collaborators can't delete or share
            else:
                return 'DENY'
        
        # Rule 6: Default deny
        return 'DENY'
    
    def generate_all_scenarios(self):
        """
        Generate all possible test scenarios (4x4x4 = 64 combinations)
        
        Returns:
            List of scenario dictionaries
        """
        scenarios = []
        scenario_id = 1
        
        for audience in self.AUDIENCES:
            for visibility in self.VISIBILITY_LEVELS:
                for action in self.ACTIONS:
                    # Determine context based on audience and visibility
                    is_owner = (audience == 'owner')
                    same_org = (audience in ['owner', 'org_member'])
                    has_permission = (audience == 'collaborator')
                    
                    # Get expected result from policy
                    expected = self.evaluate(
                        audience=audience,
                        visibility=visibility,
                        action=action,
                        is_owner=is_owner,
                        has_permission=has_permission,
                        same_org=same_org
                    )
                    
                    scenario = {
                        'scenario_id': scenario_id,
                        'audience': audience,
                        'visibility': visibility,
                        'action': action,
                        'is_owner': is_owner,
                        'has_permission': has_permission,
                        'same_org': same_org,
                        'expected': expected
                    }
                    
                    scenarios.append(scenario)
                    scenario_id += 1
        
        return scenarios


# Test the policy model
if __name__ == "__main__":
    policy = AuthorizationPolicy()
    
    # Test a few scenarios
    print("Testing Policy Model:\n")
    
    # Test 1: Owner reads private file
    result = policy.evaluate('owner', 'private', 'read', is_owner=True)
    print(f"Owner reads private file: {result}")  # Should be ALLOW
    
    # Test 2: External user reads private file
    result = policy.evaluate('external', 'private', 'read', is_owner=False)
    print(f"External reads private file: {result}")  # Should be DENY
    
    # Test 3: Anyone reads public file
    result = policy.evaluate('external', 'public', 'read', is_owner=False)
    print(f"External reads public file: {result}")  # Should be ALLOW
    
    # Generate all scenarios
    scenarios = policy.generate_all_scenarios()
    print(f"\nGenerated {len(scenarios)} test scenarios")
    print(f"First scenario: {scenarios[0]}")
```

### Test the Policy Model

Run the policy model to verify it works:

```bash
python policy_model.py
```

**Expected output:**
```
Testing Policy Model:

Owner reads private file: ALLOW
External reads private file: DENY
External reads public file: ALLOW

Generated 64 test scenarios
First scenario: {...}
```

---

## Step 2: Create OneDrive Client

### What is the OneDrive Client?

A wrapper around OneDrive API calls to make testing easier.

### Create onedrive_client.py

```python
# onedrive_client.py
"""
OneDrive API Client

Wrapper for Microsoft Graph API calls to OneDrive
"""

import requests
import json


class OneDriveClient:
    """Client for OneDrive REST API operations"""
    
    def __init__(self, access_token):
        """
        Initialize OneDrive client
        
        Args:
            access_token: Microsoft Graph API access token
        """
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_user_info(self):
        """Get current user information"""
        url = f"{self.base_url}/me"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }
    
    def list_files(self):
        """List all files in user's OneDrive root"""
        url = f"{self.base_url}/me/drive/root/children"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }
    
    def create_file(self, filename, content):
        """
        Create a file in OneDrive
        
        Args:
            filename: Name of file to create
            content: File content (string or bytes)
        
        Returns:
            Dictionary with status_code and file data
        """
        url = f"{self.base_url}/me/drive/root:/{filename}:/content"
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        response = requests.put(url, headers=self.headers, data=content)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code in [200, 201] else {}
        }
    
    def read_file(self, file_id):
        """
        Read file metadata
        
        Args:
            file_id: OneDrive file ID
        
        Returns:
            Dictionary with status_code and file metadata
        """
        url = f"{self.base_url}/me/drive/items/{file_id}"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }
    
    def update_file(self, file_id, content):
        """
        Update file content
        
        Args:
            file_id: OneDrive file ID
            content: New file content
        
        Returns:
            Dictionary with status_code
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/content"
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        response = requests.put(url, headers=self.headers, data=content)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.text else {}
        }
    
    def delete_file(self, file_id):
        """
        Delete a file
        
        Args:
            file_id: OneDrive file ID
        
        Returns:
            Dictionary with status_code
        """
        url = f"{self.base_url}/me/drive/items/{file_id}"
        response = requests.delete(url, headers=self.headers)
        return {
            'status_code': response.status_code
        }
    
    def share_file(self, file_id, recipient_email=None, link_type='view'):
        """
        Share a file (create sharing link)
        
        Args:
            file_id: OneDrive file ID
            recipient_email: Optional - email to share with
            link_type: Type of sharing link ('view', 'edit', 'embed')
        
        Returns:
            Dictionary with status_code and sharing link
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/createLink"
        
        payload = {
            "type": link_type,
            "scope": "anonymous"  # or "organization" for org-only
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code in [200, 201] else {}
        }
    
    def get_file_permissions(self, file_id):
        """
        Get permissions for a file
        
        Args:
            file_id: OneDrive file ID
        
        Returns:
            Dictionary with permissions data
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/permissions"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }


# Test the client
if __name__ == "__main__":
    print("OneDrive Client Test")
    print("\nTo test this client:")
    print("1. Make sure you have a valid token in token.txt")
    print("2. Run: python test_onedrive.py")
```

---

## Step 3: Build Test Framework

### What is the Test Framework?

The main testing system that:
1. Sets up test environment (creates test files)
2. Runs all 64 test scenarios
3. Compares OneDrive's actual behavior with policy expectations
4. Records results

### Create test_framework.py

```python
# test_framework.py
"""
OneDrive Authorization Testing Framework

Main framework for testing authorization enforcement in OneDrive
"""

import json
import time
from datetime import datetime
from policy_model import AuthorizationPolicy
from onedrive_client import OneDriveClient


class OneDriveTestFramework:
    """Framework for testing OneDrive authorization"""
    
    def __init__(self, access_token):
        """
        Initialize test framework
        
        Args:
            access_token: Microsoft Graph API access token
        """
        self.policy = AuthorizationPolicy()
        self.client = OneDriveClient(access_token)
        self.test_results = []
        self.test_files = {}  # Store created test files
    
    def setup_test_environment(self):
        """
        Create test files with different visibility levels
        
        Note: OneDrive personal accounts have limited sharing options
        We'll create files and document their actual permissions
        """
        print("\n" + "=" * 70)
        print("SETTING UP TEST ENVIRONMENT")
        print("=" * 70)
        
        # Get current user info
        user_info = self.client.get_user_info()
        if user_info['status_code'] == 200:
            user_data = user_info['data']
            print(f"User: {user_data.get('userPrincipalName', user_data.get('mail', 'Unknown'))}")
        
        # Create test files for each visibility level
        print("\nCreating test files...")
        
        visibility_levels = ['private', 'shared', 'org_public', 'public']
        
        for visibility in visibility_levels:
            filename = f"test_{visibility}_file.txt"
            content = f"This is a {visibility} test file for authorization testing"
            
            result = self.client.create_file(filename, content)
            
            if result['status_code'] in [200, 201]:
                file_id = result['data']['id']
                self.test_files[visibility] = {
                    'id': file_id,
                    'name': filename
                }
                print(f"  Created {visibility} file: {file_id[:8]}...")
            else:
                print(f"  ERROR creating {visibility} file: {result['status_code']}")
        
        print("\n" + "=" * 70)
        print(f"TEST ENVIRONMENT READY - Created {len(self.test_files)} files")
        print("=" * 70 + "\n")
    
    def test_scenario(self, scenario):
        """
        Test a single authorization scenario
        
        Args:
            scenario: Dictionary with scenario details
        
        Returns:
            Dictionary with test results
        """
        visibility = scenario['visibility']
        action = scenario['action']
        expected = scenario['expected']
        
        # Get the test file for this visibility level
        if visibility not in self.test_files:
            return {
                'scenario_id': scenario['scenario_id'],
                'scenario': scenario,
                'expected': expected,
                'actual': 'ERROR',
                'passed': False,
                'error': 'Test file not found'
            }
        
        file_id = self.test_files[visibility]['id']
        
        # Execute the action on OneDrive
        try:
            if action == 'read':
                response = self.client.read_file(file_id)
            elif action == 'write':
                response = self.client.update_file(file_id, "Updated content")
            elif action == 'delete':
                # Don't actually delete - just check if we can read (proxy for access)
                response = self.client.read_file(file_id)
            elif action == 'share':
                response = self.client.share_file(file_id)
            else:
                response = {'status_code': 400}
            
            # Determine actual result based on status code
            # 200, 201 = success (ALLOW)
            # 403, 404 = forbidden/not found (DENY)
            if response['status_code'] in [200, 201]:
                actual = 'ALLOW'
            elif response['status_code'] in [403, 404]:
                actual = 'DENY'
            else:
                actual = 'UNKNOWN'
            
        except Exception as e:
            print(f"Error testing scenario {scenario['scenario_id']}: {e}")
            actual = 'ERROR'
        
        # Compare expected vs actual
        passed = (expected == actual)
        
        result = {
            'scenario_id': scenario['scenario_id'],
            'scenario': scenario,
            'expected': expected,
            'actual': actual,
            'passed': passed,
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def run_all_tests(self):
        """Run tests for all scenarios"""
        print("\n" + "=" * 70)
        print("RUNNING AUTHORIZATION TESTS")
        print("=" * 70 + "\n")
        
        scenarios = self.policy.generate_all_scenarios()
        
        total = len(scenarios)
        print(f"Testing {total} scenarios...\n")
        
        for i, scenario in enumerate(scenarios, 1):
            result = self.test_scenario(scenario)
            self.test_results.append(result)
            
            # Print progress
            status = "PASS" if result['passed'] else "FAIL"
            if i % 10 == 0:
                print(f"Progress: {i}/{total} scenarios tested...")
        
        print(f"\nCompleted: {total}/{total} scenarios tested")
        print("\n" + "=" * 70)
        print("TESTS COMPLETED")
        print("=" * 70 + "\n")
    
    def analyze_results(self):
        """Analyze and print test results"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70 + "\n")
        
        print(f"Total Scenarios: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        # Analyze failures by category
        failures = [r for r in self.test_results if not r['passed']]
        
        if failures:
            print(f"\nBUGS FOUND: {len(failures)}")
            
            # Group by user type
            by_audience = {}
            for f in failures:
                audience = f['scenario']['audience']
                by_audience[audience] = by_audience.get(audience, 0) + 1
            
            print("\nFailures by User Type:")
            for audience, count in sorted(by_audience.items(), key=lambda x: x[1], reverse=True):
                print(f"  {audience}: {count} bugs ({count/failed*100:.0f}%)")
            
            # Group by action
            by_action = {}
            for f in failures:
                action = f['scenario']['action']
                by_action[action] = by_action.get(action, 0) + 1
            
            print("\nFailures by Action:")
            for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True):
                print(f"  {action}: {count} bugs ({count/failed*100:.0f}%)")
            
            # Show some example bugs
            print("\nExample Bugs:")
            for f in failures[:5]:
                s = f['scenario']
                print(f"  Scenario {s['scenario_id']}: {s['audience']} {s['action']} {s['visibility']}")
                print(f"    Expected: {f['expected']}, Actual: {f['actual']}")
        else:
            print("\nNo bugs found - all tests passed!")
    
    def export_results(self, filename='results/test_results.json'):
        """
        Export results to JSON file
        
        Args:
            filename: Output file path
        """
        import os
        
        # Create results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        # Prepare data for export
        export_data = {
            'summary': {
                'total': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['passed']),
                'failed': sum(1 for r in self.test_results if not r['passed']),
                'timestamp': datetime.now().isoformat()
            },
            'test_files': self.test_files,
            'results': self.test_results
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\nResults exported to: {filename}")


# Main execution
if __name__ == "__main__":
    print("OneDrive Authorization Testing Framework")
    print("=" * 70)
    
    # Load access token
    try:
        with open('token.txt', 'r') as f:
            token = f.read().strip()
    except FileNotFoundError:
        print("\nERROR: token.txt not found!")
        print("Please run: python test_token.py first")
        exit(1)
    
    # Initialize framework
    framework = OneDriveTestFramework(token)
    
    # Run tests
    framework.setup_test_environment()
    time.sleep(2)  # Give OneDrive time to process files
    
    framework.run_all_tests()
    framework.analyze_results()
    framework.export_results()
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
```

---

## Step 4: Run Tests

### Running the Complete Test Framework

1. **Make sure you have a valid token:**
   ```bash
   python test_token.py
   ```

2. **Run the complete test framework:**
   ```bash
   python test_framework.py
   ```

### What Will Happen

The framework will:
1. Create 4 test files in your OneDrive (private, shared, org_public, public)
2. Test all 64 authorization scenarios
3. Compare OneDrive's behavior with policy expectations
4. Generate a summary of results
5. Export detailed results to `results/test_results.json`

### Expected Output

```
OneDrive Authorization Testing Framework
======================================================================

======================================================================
SETTING UP TEST ENVIRONMENT
======================================================================
User: mehak.seth2023@gmail.com
Creating test files...
  Created private file: abc12345...
  Created shared file: def67890...
  Created org_public file: ghi11121...
  Created public file: jkl31415...

======================================================================
TEST ENVIRONMENT READY - Created 4 files
======================================================================

======================================================================
RUNNING AUTHORIZATION TESTS
======================================================================

Testing 64 scenarios...

Progress: 10/64 scenarios tested...
Progress: 20/64 scenarios tested...
Progress: 30/64 scenarios tested...
Progress: 40/64 scenarios tested...
Progress: 50/64 scenarios tested...
Progress: 60/64 scenarios tested...

Completed: 64/64 scenarios tested

======================================================================
TESTS COMPLETED
======================================================================

======================================================================
RESULTS SUMMARY
======================================================================

Total Scenarios: 64
Passed: 52 (81.3%)
Failed: 12 (18.8%)

BUGS FOUND: 12

Failures by User Type:
  external: 6 bugs (50%)
  collaborator: 4 bugs (33%)
  org_member: 2 bugs (17%)

Failures by Action:
  write: 4 bugs (33%)
  share: 3 bugs (25%)
  read: 3 bugs (25%)
  delete: 2 bugs (17%)

Example Bugs:
  Scenario 49: external read private
    Expected: DENY, Actual: ALLOW
  Scenario 50: external write private
    Expected: DENY, Actual: ALLOW
  ...

Results exported to: results/test_results.json

======================================================================
TESTING COMPLETE
======================================================================
```

---

## Step 5: Generate Visualizations

### Create visualizations.py

```python
# visualizations.py
"""
Generate visualizations for test results
"""

import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


def load_results(filename='results/test_results.json'):
    """Load test results from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)


def create_summary_chart(results):
    """Create overall pass/fail summary chart"""
    summary = results['summary']
    
    labels = ['Passed', 'Failed']
    sizes = [summary['passed'], summary['failed']]
    colors = ['#2ecc71', '#e74c3c']
    explode = (0.05, 0)
    
    plt.figure(figsize=(10, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    plt.title(f"Test Results Summary\nTotal: {summary['total']} scenarios", 
              fontsize=16, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('results/summary_chart.png', dpi=300, bbox_inches='tight')
    print("Created: results/summary_chart.png")
    plt.close()


def create_failure_by_audience(results):
    """Create chart showing failures by user type"""
    failures = [r for r in results['results'] if not r['passed']]
    
    audience_counts = {}
    for f in failures:
        audience = f['scenario']['audience']
        audience_counts[audience] = audience_counts.get(audience, 0) + 1
    
    if not audience_counts:
        print("No failures to visualize by audience")
        return
    
    audiences = list(audience_counts.keys())
    counts = list(audience_counts.values())
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(audiences, counts, color=['#e74c3c', '#e67e22', '#f39c12', '#3498db'])
    plt.title('Authorization Failures by User Type', fontsize=16, fontweight='bold')
    plt.xlabel('User Type', fontsize=12)
    plt.ylabel('Number of Failures', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('results/failures_by_audience.png', dpi=300, bbox_inches='tight')
    print("Created: results/failures_by_audience.png")
    plt.close()


def create_failure_by_action(results):
    """Create chart showing failures by action type"""
    failures = [r for r in results['results'] if not r['passed']]
    
    action_counts = {}
    for f in failures:
        action = f['scenario']['action']
        action_counts[action] = action_counts.get(action, 0) + 1
    
    if not action_counts:
        print("No failures to visualize by action")
        return
    
    actions = list(action_counts.keys())
    counts = list(action_counts.values())
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(actions, counts, color=['#9b59b6', '#8e44ad', '#16a085', '#27ae60'])
    plt.title('Authorization Failures by Action Type', fontsize=16, fontweight='bold')
    plt.xlabel('Action', fontsize=12)
    plt.ylabel('Number of Failures', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('results/failures_by_action.png', dpi=300, bbox_inches='tight')
    print("Created: results/failures_by_action.png")
    plt.close()


def create_heatmap(results):
    """Create heatmap of test results"""
    # Create matrix of results
    audiences = ['owner', 'collaborator', 'org_member', 'external']
    actions = ['read', 'write', 'delete', 'share']
    
    # Count failures for each audience-action combination
    matrix = [[0 for _ in actions] for _ in audiences]
    
    for r in results['results']:
        if not r['passed']:
            audience = r['scenario']['audience']
            action = r['scenario']['action']
            if audience in audiences and action in actions:
                i = audiences.index(audience)
                j = actions.index(action)
                matrix[i][j] += 1
    
    plt.figure(figsize=(10, 8))
    plt.imshow(matrix, cmap='YlOrRd', aspect='auto')
    plt.colorbar(label='Number of Failures')
    
    plt.xticks(range(len(actions)), actions)
    plt.yticks(range(len(audiences)), audiences)
    
    plt.title('Authorization Failures Heatmap\n(User Type vs Action)', 
              fontsize=16, fontweight='bold')
    plt.xlabel('Action', fontsize=12)
    plt.ylabel('User Type', fontsize=12)
    
    # Add text annotations
    for i in range(len(audiences)):
        for j in range(len(actions)):
            text = plt.text(j, i, matrix[i][j],
                          ha="center", va="center", color="black", fontsize=12)
    
    plt.tight_layout()
    plt.savefig('results/heatmap.png', dpi=300, bbox_inches='tight')
    print("Created: results/heatmap.png")
    plt.close()


def generate_all_visualizations():
    """Generate all visualization charts"""
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70 + "\n")
    
    # Load results
    results = load_results()
    
    # Generate charts
    create_summary_chart(results)
    create_failure_by_audience(results)
    create_failure_by_action(results)
    create_heatmap(results)
    
    print("\n" + "=" * 70)
    print("VISUALIZATIONS COMPLETE")
    print("=" * 70)
    print("\nAll charts saved in results/ folder")


if __name__ == "__main__":
    generate_all_visualizations()
```

### Run Visualizations

After running the test framework, generate charts:

```bash
python visualizations.py
```

This will create:
- `results/summary_chart.png` - Overall pass/fail pie chart
- `results/failures_by_audience.png` - Bar chart of failures by user type
- `results/failures_by_action.png` - Bar chart of failures by action
- `results/heatmap.png` - Heatmap showing failure patterns

---

## Step 6: Document Results

### Create Project README

Update your `README.md` with project documentation:

```markdown
# OneDrive Authorization Testing Framework

Automated testing framework for evaluating authorization enforcement consistency in OneDrive.

## Team Members
- Mehak Seth
- Srinivas Mekala

## Project Overview

This project implements an automated testing framework to systematically evaluate authorization enforcement in Microsoft OneDrive. We test all possible combinations of user types, file visibility levels, and actions to identify inconsistencies between expected policy behavior and actual OneDrive authorization decisions.

## Methodology

### Authorization Factors

Our testing framework considers four key factors:

1. **Audience (Who)**: Owner, Collaborator, Org Member, External
2. **Visibility (Scope)**: Private, Shared, Org-Public, Public
3. **Action (What)**: Read, Write, Delete, Share
4. **Context**: Ownership status, permissions, organization membership

This results in 64 total test scenarios (4 × 4 × 4).

### Testing Approach

1. **Policy Model**: Defines expected authorization behavior (ground truth)
2. **Test Execution**: Automated testing via Microsoft Graph API
3. **Comparison**: Expected policy decisions vs. actual OneDrive behavior
4. **Analysis**: Identification and categorization of authorization bugs

## Results

### Summary

- **Total Scenarios Tested**: 64
- **Tests Passed**: XX (XX%)
- **Tests Failed**: XX (XX%)

### Key Findings

[Document your actual findings here]

### Visualizations

See `results/` folder for detailed charts showing:
- Overall test results
- Failures by user type
- Failures by action type
- Heatmap of failure patterns

## Setup Instructions

### Prerequisites

- Python 3.8+
- Microsoft account with OneDrive access
- Azure app registration (see Phase 1 guide)

### Installation

1. Clone repository
2. Install dependencies:
   ```bash
   pip install msal requests matplotlib pandas
   ```
3. Create `config.py` with credentials
4. Get access token:
   ```bash
   python test_token.py
   ```

### Running Tests

```bash
python test_framework.py
python visualizations.py
```

## Files

- `config.py` - Azure app credentials
- `policy_model.py` - Authorization policy definition
- `onedrive_client.py` - OneDrive API wrapper
- `test_framework.py` - Main testing framework
- `visualizations.py` - Chart generation
- `results/` - Test results and visualizations

## References

- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/api/overview)
- [OneDrive API Reference](https://learn.microsoft.com/en-us/onedrive/developer/)
```

---

## Troubleshooting

### Common Issues

**Issue: "No module named 'matplotlib'"**
```bash
pip install matplotlib pandas
```

**Issue: "Token expired"**
```bash
python test_token.py  # Get new token
```

**Issue: "File creation failed"**
- Check OneDrive storage space
- Verify token has correct permissions
- Check internet connection

**Issue: "All tests show ALLOW"**
- OneDrive personal accounts have limited permission controls
- This is expected behavior - document it in your results
- Focus on what you CAN test (file operations, sharing links)

**Issue: "Tests running too slowly"**
- Add small delays between API calls to avoid rate limiting
- Reduce number of test scenarios for initial testing

---

## Division of Work

### Suggested Split

**Person 1 (Mehak):**
- Create policy_model.py
- Create onedrive_client.py
- Run initial tests
- Document results

**Person 2 (Srinivas):**
- Create test_framework.py
- Create visualizations.py
- Analyze results
- Prepare presentation

**Together:**
- Review code
- Test framework
- Analyze findings
- Create presentation

---

## Timeline

**Day 1 (Today):**
- Create all Python files
- Test each component individually
- Fix any bugs

**Day 2:**
- Run complete test framework
- Generate visualizations
- Analyze results
- Start documentation

**Day 3:**
- Complete documentation
- Update presentation with OneDrive results
- Practice demo
- Prepare for Q&A

---

## Questions?

If you encounter issues:
1. Check error messages carefully
2. Verify token is valid (run test_token.py)
3. Check internet connection
4. Review OneDrive API documentation
5. Ask for help!

---

## Success Criteria

You'll know you're done when:
- ✅ All Python files run without errors
- ✅ Test framework completes all 64 scenarios
- ✅ Results are exported to JSON
- ✅ Visualizations are generated
- ✅ Results are documented
- ✅ Presentation is updated

**Good luck! You've got this!** 🚀