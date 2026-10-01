# Security Policy

## Supported versions

Only the latest release of the UEFN Dream Bot Team kit receives fixes. Please update to the
newest [GitHub Release](https://github.com/mimmo-the-root/UEFN-dream-bot-team/releases) before
reporting.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through GitHub:
[Report a vulnerability](https://github.com/mimmo-the-root/UEFN-dream-bot-team/security/advisories/new).

Include: what is affected (agent, hook, script, or console page), steps to reproduce, and the
impact you expect. You can expect an acknowledgement within a few days and a fix or mitigation
plan as soon as it is reproduced.

## Scope

In scope for this repo:

* The local Agent Console servers (`agent-console-server.ps1` / `.py`) — e.g. path traversal,
  exposure beyond localhost, injection through displayed data.
* Hooks and scripts that run on your machine (`tool/`, `project-template/` hooks).
* Anything that could leak private data: the private `local/` layer of genre skills, API keys,
  tokens, or map names/task IDs ending up in commits, exports or releases.
* Agent definitions or skills that could cause an agent to run destructive or exfiltrating
  commands.

Out of scope: vulnerabilities in UEFN, Fortnite, Verse, Claude Code or other third-party
software (report those to their vendors), and issues in your own UEFN projects.

## Handling secrets

Never paste API keys, tokens or personal data into issues, pull requests or screenshots. If you
accidentally committed a secret, revoke it first, then tell us.
