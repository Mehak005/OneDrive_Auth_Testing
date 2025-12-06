# policy_model.py
"""
Authorization Policy Model for OneDrive

Defines expected authorization rules for a *personal* OneDrive test matrix:
- Audiences: owner, invited_user (abc@example.com), normal_user (no sharing)
- Visibilities: private file, public view link, public edit link, direct invite
- Actions: read, write, delete, share
- Context: whether the audience effectively has permission for that visibility
"""

class AuthorizationPolicy:
    """Defines expected authorization behavior"""
    
    # Define possible values for each factor (personal OneDrive only)
    AUDIENCES = ['owner', 'invited_user', 'normal_user']
    VISIBILITY_LEVELS = ['private', 'public_view_link', 'public_edit_link', 'collab_invite']
    ACTIONS = ['read', 'write', 'delete', 'share']
    
    def evaluate(self, audience, visibility, action, is_owner=False, 
                 has_permission=False, same_org=False):
        """
        Evaluate if an action should be allowed based on policy rules.
        
        Args:
            audience: Type of user (owner, invited_user, normal_user)
            visibility: File visibility (private, public_view_link, public_edit_link, collab_invite)
            action: What action is being attempted (read, write, delete, share)
            is_owner: Is the user the file owner?
            has_permission: Does user have permission via link/invite?
            same_org: Unused for personal drives (kept for signature compatibility)
        
        Returns:
            'ALLOW' or 'DENY'
        """
        
        # Rule 1: Owner has full access to their own files
        if is_owner:
            return 'ALLOW'
        
        # Rule 2: Private files - only owner and explicit invitees
        if visibility == 'private':
            if has_permission:
                if action in ['read', 'write']:
                    return 'ALLOW'
                else:
                    return 'DENY'  # Non-owners shouldn't delete/share
            else:
                return 'DENY'
        
        # Rule 3: View-only link (anyone with link can read)
        if visibility == 'public_view_link':
            if has_permission and action == 'read':
                return 'ALLOW'
            return 'DENY'
        
        # Rule 4: Edit link (anyone with link can read/write)
        if visibility == 'public_edit_link':
            if has_permission and action in ['read', 'write']:
                return 'ALLOW'
            return 'DENY'
        
        # Rule 5: Direct invite to collaborator
        if visibility == 'collab_invite':
            if has_permission and action in ['read', 'write']:
                return 'ALLOW'
            return 'DENY'
        
        # Rule 6: Default deny
        return 'DENY'
    
    def generate_all_scenarios(self):
        """
        Generate all possible test scenarios (personal OneDrive)
        
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
                    # Permissions are granted by the sharing model:
                    # - public_view_link: anyone with link can read
                    # - public_edit_link: anyone with link can read/write
                    # - collab_invite: only invited_user has read/write
                    has_permission = False
                    if visibility == 'public_view_link':
                        has_permission = True  # link is broadly usable
                    elif visibility == 'public_edit_link':
                        has_permission = True  # link grants edit
                    elif visibility == 'collab_invite' and audience == 'invited_user':
                        has_permission = True
                    
                    # Get expected result from policy
                    expected = self.evaluate(
                        audience=audience,
                        visibility=visibility,
                        action=action,
                        is_owner=is_owner,
                        has_permission=has_permission,
                        same_org=False
                    )
                    
                    scenario = {
                        'scenario_id': scenario_id,
                        'audience': audience,
                        'visibility': visibility,
                        'action': action,
                        'is_owner': is_owner,
                        'has_permission': has_permission,
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
    
    # Test 2: Normal user reads view link
    result = policy.evaluate('normal_user', 'public_view_link', 'read', has_permission=True)
    print(f"Normal user reads public view link: {result}")  # Should be ALLOW
    
    # Test 3: Normal user writes view link
    result = policy.evaluate('normal_user', 'public_view_link', 'write', has_permission=True)
    print(f"Normal user writes public view link: {result}")  # Should be DENY
    
    # Generate all scenarios
    scenarios = policy.generate_all_scenarios()
    print(f"\nGenerated {len(scenarios)} test scenarios")
    print(f"First scenario: {scenarios[0]}")
    
    # save scenarios to a csv file for further analysis if needed
    import csv
    with open('scenarios.csv', 'w', newline='') as csvfile:
        fieldnames = ['scenario_id', 'audience', 'visibility', 'action', 'is_owner', 'has_permission', 'expected']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for scenario in scenarios:
            writer.writerow(scenario)
            
