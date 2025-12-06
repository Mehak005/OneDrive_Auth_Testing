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
        self.test_api_responses = []
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
            }, None
        
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
    
    def run_all_tests(self):
        """Run tests for all scenarios"""
        print("\n" + "=" * 70)
        print("RUNNING AUTHORIZATION TESTS")
        print("=" * 70 + "\n")
        
        scenarios = self.policy.generate_all_scenarios()
        
        total = len(scenarios)
        print(f"Testing {total} scenarios...\n")
        
        for i, scenario in enumerate(scenarios, 1):
            result, response = self.test_scenario(scenario)
            time.sleep(0.75) 
            self.test_results.append(result)
            self.test_api_responses.append(response)
            
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
        
        with open('results/test_api_responses.json', 'w') as f:
            json.dump([r for r in self.test_api_responses], f, indent=2)
        
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
    test_all = True
    if test_all:
        framework.run_all_tests()
        framework.analyze_results()
        framework.export_results()
    else:
        policy = AuthorizationPolicy()
        scenarios = policy.generate_all_scenarios()
        scenario = scenarios[0]  # Test first scenario only
        result = framework.test_scenario(scenario)
        print("\nSingle Scenario Test Result:")
        print(json.dumps(result, indent=2))
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)