# Quick start

From nothing to a first working session. Do part A once per computer and part B once per project.

This page is the short path. The repository keeps the long version, with every optional step, in [SETUP-GUIDE.md](https://github.com/mimmo-the-root/UEFN-dream-bot-team/blob/main/SETUP-GUIDE.md).

## Part A: once per computer

1. **Download the kit** from the [GitHub repo](https://github.com/mimmo-the-root/UEFN-dream-bot-team) (green Code button, then Download ZIP) and unzip it somewhere you will remember.
2. **Let UEFN talk to Claude.** In the UEFN installation folder (on Windows usually `C:\Program Files\Epic Games\Fortnite`), create a file named `.mcp.json` with this content, then start UEFN.

```
{
  "mcpServers": {
    "unreal-mcp": { "type": "http", "url": "http://127.0.0.1:8000/mcp" }
  }
}
```

3. **Turn the server on** in UEFN: Edit, Editor Preferences, Model Context Protocol, then switch on *Auto Start Server*.
4. **Install the agents and skills.** Copy everything inside the kit's `user-level-agents/` folder into `~/.claude/agents/` (on Windows `%USERPROFILE%\.claude\agents\`). Copy each folder inside `user-level-skills/` into `~/.claude/skills/`. Copy `user-level-memory/CLAUDE.md` to `~/.claude/CLAUDE.md`, or paste it at the end of yours if you already have one.
5. **Keep a copy for automatic updates.** Copy the whole `project-template/` folder into `~/.claude/kit-template/`. From then on every new session updates the kit files of the project you are in.
6. **Register the UEFN server once** by running this in a terminal:

```
claude mcp add --transport http unreal-mcp --scope user http://127.0.0.1:8000/mcp
```

> **Checkpoint** `claude mcp list` shows `unreal-mcp` with scope user.

## Part B: once per project

1. In UEFN, open **Project Settings** and enable *Python Editor Scripting* and *UEFN MCP Toolsets* for this project.
2. Copy the **contents** of the kit's `project-template/` folder into the project's `Content/` folder.
3. Open a terminal **inside that `Content/` folder** and start `claude`.
4. Tell it: *Read Claude/SETUP-INSTRUCTIONS.md and set up this project.* It checks the connection, asks what the project is, and sets up the rest.
5. On the first session, ask for **project-bootstrap**. With existing code it maps the project and writes a first spec and bug list. With an empty project it asks you questions instead of inventing anything.

> **Checkpoint** Open `http://127.0.0.1:8765/` in your browser. The console is running, and it shows 17 agents, all idle.

> **Tip** Open the console as that web address, not as a file from your disk, or it cannot talk to the local server.

## And then

Work as usual. Ask the coder agent for a feature, let the checks run, and ask the planner to update `STATUS.md` before you close. The next chapter, [Your team](ch:your-team), says who does what.
