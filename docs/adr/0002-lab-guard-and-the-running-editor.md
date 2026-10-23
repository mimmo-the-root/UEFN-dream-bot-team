# ADR 0002: The lab guard is never worked around, and a running editor is never closed

Status: accepted (2026-10, kit 1.106-1.107)

**Context.** Agents drive a live editor through the MCP. UEFN crashes often and some calls are destructive. An agent that rewords a refused call, or kills a stuck editor, can lose the owner's work.

**Decision.** (1) `mcp_lab.py` refuses what is unsafe (paths on the disk, writes outside the lab, `save_assets` without a list of assets, quitting the editor). A refusal is reported and never reworded; the guard changes only with the owner's approval. (2) A running editor is never closed or killed by an agent. After a crash only `uefn_session.py recover` may relaunch it, opt-in, at most 2 times in 30 minutes. (3) A call that changes something and times out is never replayed blindly: the state is read first.

**Rejected.** Letting the agent kill and restart a stuck editor (it can destroy unsaved work); retrying on timeout (duplicate devices, entities and sessions).

**Consequence.** Some calls stop and wait for the owner. That is intended.
