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
    
    # save scenarios to a csv file for further analysis if needed
    import csv
    with open('scenarios.csv', 'w', newline='') as csvfile:
        fieldnames = ['scenario_id', 'audience', 'visibility', 'action', 'is_owner', 'has_permission', 'same_org', 'expected']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for scenario in scenarios:
            writer.writerow(scenario)
            
