# test_framework.py
"""
OneDrive Authorization Testing Framework

Main framework for testing authorization enforcement in OneDrive
"""

import json
import time
from datetime import datetime
import base64
from policy_model import AuthorizationPolicy
from onedrive_client import OneDriveClient


class OneDriveTestFramework:
    """Framework for testing OneDrive authorization"""
    
    def __init__(self, access_token, audience):
        """
        Initialize test framework
        
        Args:
            access_token: Microsoft Graph API access token
        """
        self.audience = audience
        self.policy = AuthorizationPolicy()
        self.client = OneDriveClient(access_token)
        self.test_results = []
        self.test_api_responses = []
        self.test_files = {}  # Store created test files
    
    def setup_test_environment(self):
        """
        Create test files with different sharing states:
        - private_file.txt: no sharing
        - public_view.txt: anonymous view link
        - public_edit.txt: anonymous edit link
        - collab_file.txt: direct invite to collaborator
        """
        def compute_share_id(web_url):
            encoded = base64.urlsafe_b64encode(web_url.encode()).decode().rstrip("=")
            return f"u!{encoded}"
        print("\n" + "=" * 70)
        print("SETTING UP TEST ENVIRONMENT")
        print("=" * 70)
        
        # Get current user info
        user_info = self.client.get_user_info()
        if user_info['status_code'] == 200:
            user_data = user_info['data']
            print(f"User: {user_data.get('userPrincipalName', user_data.get('mail', 'Unknown'))}")
        
        print("\nCreating test files...")
        specs = [
            ("private", "private_file.txt", "This is a private test file"),
            ("public_view_link", "public_view.txt", "This file is shared with a view-only link"),
            ("public_edit_link", "public_edit.txt", "This file is shared with an edit link"),
            ("collab_invite", "collab_file.txt", "This file is shared directly with a collaborator")
        ]
        
        for visibility, filename, content in specs:
            result = self.client.create_file(filename, content)
            
            if result['status_code'] in [200, 201]:
                file_id = result['data']['id']
                self.test_files[visibility] = {
                    'id': file_id,
                    'name': filename
                }
                print(f"  Created {filename} file: {file_id[:8]}...")
                
                # Apply sharing as needed
                if visibility == "public_view_link":
                    share_resp = self.client.share_file(file_id, link_type="view", scope="anonymous")
                    self.test_files[visibility]["share"] = share_resp
                    share_id = share_resp["data"].get("shareId")
                    if not share_id and "link" in share_resp["data"]:
                        share_id = compute_share_id(share_resp["data"]["link"]["webUrl"])
                    self.test_files[visibility]["share_id"] = share_id
                    print(f"    Added view link (status {share_resp['status_code']})")
                elif visibility == "public_edit_link":
                    share_resp = self.client.share_file(file_id, link_type="edit", scope="anonymous")
                    self.test_files[visibility]["share"] = share_resp
                    share_id = share_resp["data"].get("shareId")
                    if not share_id and "link" in share_resp["data"]:
                        share_id = compute_share_id(share_resp["data"]["link"]["webUrl"])
                    self.test_files[visibility]["share_id"] = share_id
                    print(f"    Added edit link (status {share_resp['status_code']})")
                elif visibility == "collab_invite":
                    invite_resp = self.client.invite_user(file_id, emails=["srinivasmekala1227@gmail.com"], role="write")
                    self.test_files[visibility]["invite"] = invite_resp
                    share_id = None
                    try:
                        link_url = invite_resp["data"]["value"][0]["link"]["webUrl"]
                        share_id = compute_share_id(link_url)
                    except Exception:
                        pass
                    self.test_files[visibility]["share_id"] = share_id
                    print(f"    Invited collaborator (status {invite_resp['status_code']})")
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
            }, None
        
        file_id = self.test_files[visibility]['id']
        share_id = self.test_files[visibility].get('share_id')
        use_share = (self.audience != 'owner' and share_id)
        
        # Execute the action on OneDrive
        try:
            if action == 'read':
                if use_share:
                    response = self.client.read_file_via_share(share_id)
                else:
                    response = self.client.read_file(file_id)
            elif action == 'write':
                if use_share:
                    response = self.client.update_file_via_share(share_id, "Updated content")
                else:
                    response = self.client.update_file(file_id, "Updated content")
            elif action == 'delete':
                # Don't actually delete - just check if we can read (proxy for access)
                if use_share:
                    response = self.client.read_file_via_share(share_id)
                else:
                    response = self.client.read_file(file_id)
            elif action == 'share':
                if use_share:
                    response = self.client.share_file_via_share(share_id)
                else:
                    response = self.client.share_file(file_id)
            else:
                response = {'status_code': 400}
            
            # Determine actual result based on status code
            # 200, 201 = success (ALLOW)
            # 400, 403, 404 = forbidden/not found/invalid for drive (DENY)
            if response['status_code'] in [200, 201]:
                actual = 'ALLOW'
            elif response['status_code'] in [400, 403, 404]:
                print(f"DENY FOR scenario {scenario['scenario_id']}: RESPONSE={response}")
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
        
        return result, response
    
    def run_tests(self, audience):
        """Run tests for all scenarios"""
        print("\n" + "=" * 70)
        print(f"RUNNING AUTHORIZATION TESTS for audience: {audience}")
        print("=" * 70 + "\n")
        
        scenarios = self.policy.generate_all_scenarios()
        scenarios = [s for s in scenarios if s['audience'] == audience]
        total = len(scenarios)
        print(f"Testing {total} scenarios...\n")
        
        for i, scenario in enumerate(scenarios, 1):
            result, response = self.test_scenario(scenario)
            time.sleep(0.75) 
            self.test_results.append(result)
            self.test_api_responses.append(response)
            
            # Print progress
            status = "PASS" if result['passed'] else "FAIL"
            # if i % 10 == 0:
        print(f"For {audience}: {total} scenarios tested...")
        
        # print(f"\nCompleted: {total}/{total} scenarios tested")
        
    
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
    
    def export_results(self):
        filename=f'results/test_results_{self.audience}.json'
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
        
        with open(f'results/test_api_responses_{self.audience}.json', 'w') as f:
            json.dump([r for r in self.test_api_responses], f, indent=2)
        
        print(f"\nResults exported to: {filename}")


# Main execution
if __name__ == "__main__":
    print("OneDrive Authorization Testing Framework")
    print("=" * 70)
    
    # Load access token
    try:
        with open('owner_token.txt', 'r') as f:
            owner_token = f.read().strip()
        with open("collab_token.txt", "r") as f:
            collab_token = f.read().strip()
        with open("external_token.txt", "r") as f:
            external_token = f.read().strip()
    except FileNotFoundError:
        print("\nERROR: token.txt not found!")
        print("Please run: python test_token.py first")
        exit(1)
    
    # Initialize framework
    owner_framework = OneDriveTestFramework(owner_token, audience='owner')
    invited_framework = OneDriveTestFramework(collab_token, audience='invited_user')
    normal_framework = OneDriveTestFramework(external_token, audience='normal_user')
    
    # Run tests
    owner_framework.setup_test_environment()
    time.sleep(2)  # Give OneDrive time to process files
    test_all = True
    if test_all:
        owner_framework.run_tests(audience='owner')
        invited_framework.test_files = owner_framework.test_files
        normal_framework.test_files = owner_framework.test_files
        invited_framework.run_tests(audience='invited_user')
        normal_framework.run_tests(audience='normal_user')
        print("\n" + "=" * 70)
        print("TESTS COMPLETED")
        print("=" * 70 + "\n")
        owner_framework.analyze_results()
        owner_framework.export_results()
        invited_framework.analyze_results()
        invited_framework.export_results()
        normal_framework.analyze_results()
        normal_framework.export_results()
    else:
        policy = AuthorizationPolicy()
        scenarios = policy.generate_all_scenarios()
        scenario = scenarios[0]  # Test first scenario only
        result = owner_framework.test_scenario(scenario)
        print("\nSingle Scenario Test Result:")
        print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
