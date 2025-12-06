# OneDrive Authorization Testing Framework (Personal OneDrive)

## Introduction
This project probes authorization behavior on a **personal** OneDrive using Microsoft Graph. It creates files with different sharing states (private, view link, edit link, direct invite), exercises them with multiple audiences (owner, invited user, normal user), and compares observed API outcomes to an expected policy.

## Methodology
- **Policy model:** `policy_model.py` defines expected ALLOW/DENY for (audience × visibility × action) in a personal OneDrive context.
- **Client wrapper:** `onedrive_client.py` wraps Graph calls for file CRUD and sharing, including share-link access via `/shares/{shareId}/driveItem` and direct invites via `/invite`.
- **Test harness:** `test_framework.py` sets up four files, applies sharing (view/edit links, direct invite), then runs all policy scenarios per audience and records results/responses.
- **Tokens:** Uses three tokens (owner, invited user, normal user) loaded from `owner_token.txt`, `collab_token.txt`, `external_token.txt`. Tokens are acquired with `test_token.py <outfile>`, which runs MSAL interactive auth.

## Experimental Setup
- **Environment:** Python with `requests`, MSAL (`msal`), and access to Microsoft Graph for a personal account.
- **Files created:** `private_file.txt` (no sharing), `public_view.txt` (anonymous view link), `public_edit.txt` (anonymous edit link), `collab_file.txt` (direct invite with write role).
- **Sharing artifacts:** For non-owner access, the harness stores `share_id` from `share_file`/`invite_user` responses and uses `/shares/{shareId}/driveItem` for read/write/delete/share.
- **Running tests:** `python test_framework.py` (requires populated token files). Results export to `results/test_results_*.json` and raw API responses to `results/test_api_responses_*.json`. Summary takeaways in `takeaways.md`.

## Experimental Results
Recent run highlights (see `takeaways.md` for details):
- Owner: 16/16 scenarios passed as expected.
- Invited user (write invite on `collab_file.txt`): 11/16 passed. Anonymous links DENY when accessed via another user’s bearer token; collab invite allowed delete/share (write role grants broad edit).
- Normal user: 13/16 passed. Same anonymous link behavior—DENY via token.

Key takeaway: Anonymous links must be tested anonymously (using the `webUrl` without a token) or treated as DENY when accessed through a different user’s Graph token. Write invites allow delete/share unless you invite with `role='read'` or adjust expectations accordingly.

## References
- [Microsoft Graph OneDrive API](https://learn.microsoft.com/graph/api/resources/onedrive)  
- [CreateLink](https://learn.microsoft.com/graph/api/driveitem-createlink)  
- [Invite](https://learn.microsoft.com/graph/api/driveitem-invite)  
- [Shares resource / encoded URLs](https://learn.microsoft.com/graph/api/resources/shares)  
