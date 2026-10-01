# Contributing to UEFN Dream Bot Team

Thank you for contributing to **UEFN Dream Bot Team**.

This project is designed to help Fortnite / UEFN creators build, review, test, and maintain projects using AI-assisted workflows, agents, skills, templates, and automation.

Contributions are welcome, but changes should preserve the project's core principles:

* Keep workflows predictable and reproducible.
* Keep agents focused on clearly defined responsibilities.
* Prefer small, reviewable changes over large rewrites.
* Never bypass independent review gates without a documented reason.
* Keep UEFN and Verse guidance technically accurate.
* Update documentation when behavior or workflows change.

---

## 📋 Before You Contribute

Before opening an issue or pull request:

1. Read the project documentation.
2. Search existing Issues and Discussions.
3. Check whether your change affects an existing agent, skill, hook, template, or workflow.
4. Prefer extending an existing component over creating a duplicate.
5. Keep unrelated changes out of the same pull request.
6. Test your changes before submitting them.

For larger changes, open an Issue first so the proposed architecture can be discussed before implementation.

---

# 🐛 Reporting Bugs

If you find a bug, please use the **Bug Report** issue template.

A useful bug report should include:

* What you expected to happen.
* What actually happened.
* Steps to reproduce the problem.
* The affected agent, skill, hook, template, or workflow.
* Relevant error messages or logs.
* UEFN / Verse version when relevant.
* Claude Code or other AI tooling version when relevant.
* Screenshots or examples when useful.

### Good bug report

> The Verse review agent reports that a device reference is valid, but the generated code fails compilation because the referenced API is not available in the current UEFN version.

### Less useful bug report

> The agent doesn't work.

The more reproducible the problem is, the easier it is to fix.

---

# ✨ Feature Requests

For new functionality, use the **Feature Request** template.

Please explain:

### Problem

What problem are you trying to solve?

### Proposed solution

What would you like the system to do?

### Alternatives

Did you consider another approach?

### Impact

Identify which components could be affected:

* Agent
* Skill
* Hook
* Project template
* Documentation
* Tests
* Agent Console
* Workflow

### Compatibility

Explain whether the change:

* Is backward compatible.
* Changes an existing workflow.
* Requires migration.
* Could affect existing UEFN projects.

---

# 🤖 Contributing Agents

Agents are one of the most important parts of this project.

When creating or modifying an agent, keep its responsibility narrow and explicit.

An agent should clearly define:

* Its purpose.
* Its inputs.
* Its expected outputs.
* Its responsibilities.
* Its limitations.
* The tools it may use.
* The conditions under which it should stop or request human input.
* How its output is reviewed.

Avoid creating agents that duplicate the responsibilities of existing agents.

## Agent Independence

Agents should not be responsible for approving their own work.

Where appropriate, the workflow should separate:

```text
Planning
   ↓
Implementation
   ↓
Independent Review
   ↓
Validation
   ↓
Documentation
```

An implementation agent should not be treated as the final authority on the correctness of its own implementation.

---

# 🧩 Contributing Skills

Skills should be:

* Focused.
* Reusable.
* Documented.
* Deterministic where possible.
* Independent from unrelated project-specific assumptions.

Before creating a new skill, check whether an existing skill can be extended.

Avoid duplicating instructions across multiple skills when a shared source of truth is more appropriate.

When modifying a skill, consider whether existing agents depend on its current behavior.

---

# 🪝 Contributing Hooks and Automation

Hooks and automation can affect the entire development workflow.

Changes to hooks should therefore be conservative.

Before submitting a hook change, verify:

* The hook runs only when intended.
* Failure behavior is understood.
* It does not create infinite loops.
* It does not silently modify unrelated files.
* It does not expose credentials or sensitive information.
* It does not bypass review or validation stages.
* Existing workflows continue to function.

If a hook executes commands, clearly document what it executes and why.

---

# 🎮 UEFN / Verse Contributions

Changes related to UEFN or Verse should take the target UEFN version into account.

When documenting or generating Verse:

* Do not assume an API exists without verification.
* Avoid relying on deprecated APIs when a supported alternative exists.
* Preserve existing project architecture unless a structural change is intentional.
* Consider multiplayer behavior.
* Consider player lifecycle events.
* Consider device lifecycle and initialization order.
* Consider persistence and player data.
* Consider late joining players.
* Consider player elimination and respawn.
* Consider race conditions and concurrent events.

When fixing a bug, prefer the smallest change that solves the problem without introducing unrelated architectural changes.

---

# 🧪 Testing

Every functional change should be validated before submitting a pull request.

Depending on the change, testing may include:

* Automated tests.
* Static validation.
* UEFN compilation.
* In-editor testing.
* Multiplayer testing.
* Regression testing.
* Agent workflow testing.
* Documentation validation.

For UEFN gameplay changes, consider testing at least:

```text
1 player
2 players
3 players
4 players
```

when multiplayer behavior is relevant.

Also consider:

* Player joining late.
* Player leaving.
* Player elimination.
* Respawn.
* Round restart.
* Map restart.
* Persistence.
* Unexpected device state.
* Repeated execution of the same event.

Not every change requires every test. Use the smallest test set that provides reasonable confidence.

---

# 🔍 Pull Requests

Pull requests should be focused and easy to review.

A good pull request should answer:

1. What changed?
2. Why was it changed?
3. Which components are affected?
4. How was it tested?
5. Are there breaking changes?
6. Does documentation need to be updated?

## Keep PRs Focused

Prefer:

```text
PR #1
Fix agent validation logic
```

over:

```text
PR #1
Fix agent validation + redesign README + rename skills + change hooks + reorganize templates
```

Small changes are easier to understand, test, review, and revert.

---

# ✅ Pull Request Checklist

Before submitting a PR, verify:

* [ ] The change has a clear purpose.
* [ ] Existing functionality was not changed unintentionally.
* [ ] No unrelated files were modified.
* [ ] Tests or validation were performed.
* [ ] Documentation was updated when necessary.
* [ ] No secrets or credentials were committed.
* [ ] No unnecessary generated files were committed.
* [ ] Breaking changes are clearly documented.
* [ ] The relevant agent / skill / workflow was identified.
* [ ] Independent review requirements were preserved.

---

# 🔐 Security

Never commit:

* API keys.
* Access tokens.
* Passwords.
* Private credentials.
* Personal authentication data.
* Private MCP configuration containing secrets.
* Production secrets.
* Private project data that should not be public.

If you discover a security vulnerability, do **not** publish sensitive exploit details in a public Issue.

Follow the project's security reporting process described in `SECURITY.md`.

Code-scanning alerts (CodeQL) and Copilot Autofix pull requests: read [`docs/code-scanning-lessons.md`](docs/code-scanning-lessons.md) first, and run `python tests/test_skills_lib.py` and `python tests/test_skills_safety.py` on the fix before merging it.

---

# 📚 Documentation

Documentation is part of the implementation.

If a change modifies:

* An agent's behavior.
* A skill.
* A workflow.
* A command.
* A project template.
* A hook.
* Installation instructions.
* Configuration.
* Expected outputs.

update the relevant documentation in the same pull request whenever practical.

Avoid documenting behavior that the code does not actually implement.

---

# 🔄 Breaking Changes

Breaking changes should be explicitly identified.

Examples include:

* Renaming an agent.
* Removing an agent.
* Changing an agent's input format.
* Changing a skill's expected output.
* Changing project-template structure.
* Changing hook behavior.
* Changing configuration formats.
* Removing supported workflows.

A breaking change should include:

1. What changed.
2. Why it changed.
3. Who is affected.
4. How existing users can migrate.

---

# 🧠 AI-Generated Contributions

AI-assisted contributions are welcome.

However, contributors are responsible for reviewing and validating the code or documentation they submit.

Do not assume that an AI-generated answer is correct simply because it compiles or looks plausible.

For UEFN / Verse contributions in particular, verify:

* API availability.
* Syntax.
* Device behavior.
* Multiplayer behavior.
* Persistence behavior.
* Runtime behavior.
* Compatibility with the target UEFN version.

AI should accelerate development, not replace engineering judgment.

---

# 🔁 Review Philosophy

The project uses independent review as a quality-control mechanism.

A simplified workflow is:

```text
┌──────────────┐
│    TASK      │
└──────┬───────┘
       ↓
┌──────────────┐
│     PLAN     │
└──────┬───────┘
       ↓
┌──────────────┐
│ IMPLEMENTATION│
└──────┬───────┘
       ↓
┌────────────────────┐
│ INDEPENDENT REVIEW │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ VALIDATION / TESTS │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│ DOCUMENTATION      │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│      RELEASE       │
└────────────────────┘
```

The exact workflow may evolve, but the principle remains:

> **Implementation and verification should be separated whenever practical.**

---

# 🌱 Community Contributions

Contributions do not need to be limited to code.

Useful contributions include:

* Bug reports.
* Feature ideas.
* Documentation improvements.
* New skills.
* New agents.
* Better prompts.
* Workflow improvements.
* Testing.
* UEFN compatibility fixes.
* Examples.
* Tutorials.
* Performance improvements.
* Developer experience improvements.

If you are unsure whether an idea belongs in the project, open an Issue and start the discussion.

---

# 💬 Discussions

Use GitHub Discussions when you want to discuss:

* Ideas.
* Architecture.
* New workflows.
* Agent design.
* UEFN development practices.
* Community experiments.
* Questions that do not represent a confirmed bug.

Use Issues for actionable work that can be tracked and closed.

---

# 📝 Commit Messages

Keep commit messages short and descriptive.

Recommended format:

```text
type: short description
```

Examples:

```text
feat: add Verse review agent
fix: correct agent validation workflow
docs: update installation guide
test: add multiplayer workflow checks
refactor: simplify skill discovery
chore: update project template
```

Recommended types:

* `feat` - new functionality
* `fix` - bug fix
* `docs` - documentation
* `test` - tests
* `refactor` - code restructuring
* `chore` - maintenance

---

# 🚫 What Not to Do

Please avoid:

* Large unrelated rewrites.
* Copying large amounts of duplicated instructions.
* Removing validation without explanation.
* Bypassing review gates.
* Committing secrets.
* Adding undocumented behavior.
* Introducing dependencies without justification.
* Changing multiple unrelated systems in one PR.
* Assuming an AI-generated solution is correct without validation.
* Making destructive changes without a migration path.

---

# 🤝 Maintainer Review

Maintainers may request:

* Additional tests.
* Documentation updates.
* Smaller commits.
* Separation of unrelated changes.
* Architectural clarification.
* Compatibility checks.
* Independent review.
* Changes to agent boundaries.

This is intended to keep the project maintainable as the number of agents, skills, workflows, and contributors grows.

---

# 🚀 Getting Started

If you are new to the project:

1. Read the `README.md`.
2. Explore the project structure.
3. Review existing agents and skills.
4. Look at open Issues and Discussions.
5. Start with a small documentation, testing, or bug-fix contribution.
6. Open a Pull Request using the provided template.

Welcome to the UEFN Dream Bot Team community.

Build carefully. Review independently. Share what works.
