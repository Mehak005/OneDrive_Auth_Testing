# test_framework_multiuser.py
"""
Multi-User OneDrive Authorization Testing Framework

Tests authorization by using different user accounts (owner vs collaborator)
to get realistic authorization test results.
"""

import json
import time
from datetime import datetime
from policy_model import AuthorizationPolicy
from onedrive_client import OneDriveClient


class MultiUserTestFramework:
    """Framework for testing with multiple user accounts"""

    def __init__(self, owner_token, collaborator_token):
        """
        Initialize with tokens for different users

        Args:
            owner_token: Access token for file owner
            collaborator_token: Access token for collaborator/test user
        """
        self.policy = AuthorizationPolicy()
        self.owner_client = OneDriveClient(owner_token)
        self.collab_client = OneDriveClient(collaborator_token)
        self.test_results = []
        self.test_files = {}
        self.owner_email = None
        self.collab_email = None

    def setup_test_environment(self):
        """
        Create test files as OWNER and share some with collaborator
        """
        print("\n" + "=" * 70)
        print("SETTING UP TEST ENVIRONMENT")
        print("=" * 70)

        # Get owner info
        owner_info = self.owner_client.get_user_info()
        if owner_info['status_code'] == 200:
            self.owner_email = owner_info['data'].get('userPrincipalName',
                                                      owner_info['data'].get('mail', 'Unknown'))
            print(f"Owner: {self.owner_email}")
        else:
            print("ERROR: Could not get owner info")
            return False

        # Get collaborator info
        collab_info = self.collab_client.get_user_info()
        if collab_info['status_code'] == 200:
            self.collab_email = collab_info['data'].get('userPrincipalName',
                                                        collab_info['data'].get('mail', 'Unknown'))
            print(f"Collaborator: {self.collab_email}")
        else:
            print("ERROR: Could not get collaborator info")
            return False

        # Create test files as OWNER
        print("\nCreating test files (as owner)...")

        visibility_levels = ['private', 'shared', 'org_public', 'public']

        for visibility in visibility_levels:
            filename = f"multiuser_test_{visibility}_file.txt"
            content = f"This is a {visibility} test file for multi-user testing.\nCreated by: {self.owner_email}"

            result = self.owner_client.create_file(filename, content)

            if result['status_code'] in [200, 201]:
                file_id = result['data']['id']
                file_name = result['data']['name']
                self.test_files[visibility] = {
                    'id': file_id,
                    'name': file_name
                }
                print(f"  Created {visibility} file: {file_name}")

                # Share 'shared' files with collaborator
                if visibility == 'shared':
                    print(f"    Attempting to share with collaborator...")
                    # Note: Personal OneDrive has limited sharing API
                    # We'll create a sharing link instead
                    share_result = self.owner_client.share_file(file_id, link_type='edit')
                    if share_result['status_code'] in [200, 201]:
                        share_link = share_result['data'].get('link', {}).get('webUrl', 'N/A')
                        print(f"    Share link created: {share_link[:50]}...")
                        self.test_files[visibility]['share_link'] = share_link
            else:
                print(f"  ERROR creating {visibility} file: {result['status_code']}")

        print("\n" + "=" * 70)
        print(f"TEST ENVIRONMENT READY - Created {len(self.test_files)} files")
        print("=" * 70)

        return True

    def test_scenario(self, scenario):
        """
        Test a single authorization scenario with appropriate user

        Args:
            scenario: Dictionary with scenario details

        Returns:
            Dictionary with test results
        """
        visibility = scenario['visibility']
        action = scenario['action']
        audience = scenario['audience']
        expected = scenario['expected']

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

        # Choose which client to use based on audience
        if audience == 'owner':
            client = self.owner_client
            test_user = 'owner'
        else:
            # Use collaborator client for all non-owner tests
            # (collaborator, org_member, external all tested with collab account)
            client = self.collab_client
            test_user = 'collaborator'

        # Execute action
        try:
            if action == 'read':
                response = client.read_file(file_id)
            elif action == 'write':
                response = client.update_file(file_id, f"Updated by {test_user}")
            elif action == 'delete':
                # Don't actually delete - just test if we can access
                response = client.read_file(file_id)
            elif action == 'share':
                response = client.share_file(file_id)
            else:
                response = {'status_code': 400}

            # Determine actual result based on status code
            if response['status_code'] in [200, 201]:
                actual = 'ALLOW'
            elif response['status_code'] in [403, 404, 401]:
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
            'tested_by': test_user,
            'timestamp': datetime.now().isoformat()
        }

        return result

    def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "=" * 70)
        print("RUNNING MULTI-USER AUTHORIZATION TESTS")
        print("=" * 70)

        scenarios = self.policy.generate_all_scenarios()

        # For now, test owner and collaborator scenarios
        # (We only have 2 users, so we'll map org_member and external to collaborator)
        test_scenarios = scenarios

        total = len(test_scenarios)
        print(f"\nTesting {total} scenarios with 2 users...")
        print("  - Owner scenarios: tested with owner token")
        print("  - Other scenarios: tested with collaborator token")
        print()

        for i, scenario in enumerate(test_scenarios, 1):
            result = self.test_scenario(scenario)
            self.test_results.append(result)

            # Print progress
            if i % 10 == 0:
                print(f"Progress: {i}/{total} scenarios tested...")

        print(f"\nCompleted: {total}/{total} scenarios tested")
        print("\n" + "=" * 70)
        print("TESTS COMPLETED")
        print("=" * 70)

    def analyze_results(self):
        """Analyze and print test results"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed

        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)

        print(f"\nTotal Scenarios: {total}")
        print(f"Passed: {passed} ({passed / total * 100:.1f}%)")
        print(f"Failed: {failed} ({failed / total * 100:.1f}%)")

        # Analyze failures
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
                print(f"  {audience}: {count} bugs ({count / failed * 100:.0f}%)")

            # Group by action
            by_action = {}
            for f in failures:
                action = f['scenario']['action']
                by_action[action] = by_action.get(action, 0) + 1

            print("\nFailures by Action:")
            for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True):
                print(f"  {action}: {count} bugs ({count / failed * 100:.0f}%)")

            # Group by visibility
            by_visibility = {}
            for f in failures:
                visibility = f['scenario']['visibility']
                by_visibility[visibility] = by_visibility.get(visibility, 0) + 1

            print("\nFailures by Visibility:")
            for visibility, count in sorted(by_visibility.items(), key=lambda x: x[1], reverse=True):
                print(f"  {visibility}: {count} bugs ({count / failed * 100:.0f}%)")

            # Show example bugs
            print("\nExample Authorization Bugs Found:")
            for i, f in enumerate(failures[:10], 1):
                s = f['scenario']
                print(f"\n  {i}. Scenario {s['scenario_id']}: {s['audience']} {s['action']} {s['visibility']}")
                print(f"     Expected: {f['expected']}, Actual: {f['actual']}")
                print(f"     Tested by: {f['tested_by']}")
        else:
            print("\nNo bugs found - all tests passed!")
            print("This means OneDrive's authorization matches our policy perfectly.")

    def export_results(self, filename='results/multiuser_test_results.json'):
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
            'test_info': {
                'owner': self.owner_email,
                'collaborator': self.collab_email,
                'timestamp': datetime.now().isoformat()
            },
            'summary': {
                'total': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['passed']),
                'failed': sum(1 for r in self.test_results if not r['passed'])
            },
            'test_files': self.test_files,
            'results': self.test_results
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\nResults exported to: {filename}")


# Main execution
if __name__ == "__main__":
    print("=" * 70)
    print("MULTI-USER ONEDRIVE AUTHORIZATION TESTING FRAMEWORK")
    print("=" * 70)

    # Load access tokens
    try:
        with open('token_owner.txt', 'r') as f:
            owner_token = f.read().strip()
        print("Loaded owner token")
    except FileNotFoundError:
        print("\nERROR: token_owner.txt not found!")
        print("Please run: python multi_user_auth.py first")
        exit(1)

    try:
        with open('token_collaborator.txt', 'r') as f:
            collab_token = f.read().strip()
        print("Loaded collaborator token")
    except FileNotFoundError:
        print("\nERROR: token_collaborator.txt not found!")
        print("Please run: python multi_user_auth.py first")
        exit(1)

    # Initialize framework
    framework = MultiUserTestFramework(owner_token, collab_token)

    # Setup test environment
    success = framework.setup_test_environment()
    if not success:
        print("\nERROR: Failed to setup test environment")
        exit(1)

    # Give OneDrive time to process
    print("\nWaiting for OneDrive to process files...")
    time.sleep(3)

    # Run tests
    framework.run_all_tests()
    framework.analyze_results()
    framework.export_results()

    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check results/multiuser_test_results.json for detailed results")
    print("  2. Run: python visualizations.py to generate charts")
    print("=" * 70)