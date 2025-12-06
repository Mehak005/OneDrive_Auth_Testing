# OneDrive Auth Test Run (personal account) — Takeaways

- Owner (workload via `owner_token.txt`): 16/16 scenarios passed; owner can read/write/delete/share across all four files as expected.
- Invited user (`collab_token.txt`, write role on `collab_file.txt`): 11/16 passed. Failures:
  - Public links (view/edit) read/write returned 403 via `/shares/{shareId}/driveItem` with the collaborator token. Anonymous links are not honored when a different bearer token is presented; they work anonymously via the `webUrl`, not via Graph with another user’s token. Expected ALLOW should be treated as DENY for token-based access unless you hit the link without a token.
  - Collab invite delete/share returned ALLOW. With write permission, Graph allows delete/share on the invited item; policy expected DENY. If “write” is granted, adjust expectations to ALLOW delete/share or invite with role `read` instead.
- Normal user (`external_token.txt`): 13/16 passed. Failures mirror the public-link behavior: read (view/edit links) and write (edit link) returned 403/404 because anonymous links aren’t usable via another user’s bearer token; they require anonymous access via the link URL.

Key points:
- For personal OneDrive, anonymous sharing links should be tested either anonymously (no token, use the `webUrl`) or expected to DENY when accessed through another user’s Graph token.
- “Write” invites grant broad edit privileges, including delete/share, in Graph. Use `role='read'` if you need stricter behavior or update policy expectations accordingly.
- The current results reflect real Graph behavior; no code changes needed unless you want to align policy expectations with these findings.***
