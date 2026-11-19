# Remote Control compatibility by router mode

| mode  | works | why                                                          | what to do                         |
|-------|-------|--------------------------------------------------------------|------------------------------------|
| free  | NO    | uses placeholder token (dream-router-local); no plan login   | switch to auto, safe, or paid      |
| auto  | OK    | keeps the plan login; router only sits in the path           | nothing; use as-is                 |
| safe  | OK    | keeps the plan login; router only sits in the path           | nothing; use as-is                 |
| paid  | OK    | keeps the plan login; router only sits in the path           | nothing; use as-is                 |

Notes:
- Remote Control (phone app / claude remote-control) requires an authenticated session with the owner's plan login (OAuth). It does not work with API keys or placeholder tokens.
- The router's FREE_TOKEN ("dream-router-local") is a placeholder that lets free models work but breaks Remote Control.
- In auto, safe, and paid modes, the router sets ANTHROPIC_BASE_URL to localhost but OMITS ANTHROPIC_AUTH_TOKEN, so the user's saved login is used.
- Plan mode (--plan flag) bypasses the router entirely; Remote Control works normally but is not a router mode.