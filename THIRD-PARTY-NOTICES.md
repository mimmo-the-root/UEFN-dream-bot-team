# Third-party notices

## autoharness (design ideas adapted in `project-template/Claude/hooks/skills_lib.py`)

The Skill Harness (Skills page, `skills_lib.py`) adapts ideas and a few patterns from
[tigerless-labs/autoharness](https://github.com/tigerless-labs/autoharness): a deterministic
verification gate before anything is written, a per-item provenance ledger, secret/PII redaction
rules, use counters and reversible archiving. The code in this kit is an independent implementation
written for UEFN genre skills; the redaction rule patterns are adapted from autoharness'
`redaction_rules.toml`.

autoharness is licensed under the MIT License:

    MIT License

    Copyright (c) 2026 ryan

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

## uefn-mcp-server (adapted in `project-template/Claude/hooks/uefn_session.py`)

The editor state detection (editor log markers, process and crash-reporter checks, Load on Startup setting) and the relaunch idea are adapted from
[KirChuvakov/uefn-mcp-server](https://github.com/KirChuvakov/uefn-mcp-server) (`uefn_session.py`, `win_procs.py`), MIT License. The kit's version is a smaller,
stdlib-only rewrite with a stricter rule: it never closes or kills a running editor and relaunches only after a crash, with the owner's opt-in.

## Dream Router (user-level-hooks/dream_router.py, v1.124.0)

The router is our own code, written in Python. Its design and parts of its logic were adapted from:

- **freellmapi** - Copyright (c) 2026 Tashfeen Ahmed - MIT License - https://github.com/tashfeenahmed/freellmapi (Anthropic Messages to OpenAI translation, fallback loop, error classes, tool-call rescue, usage ledger, routed-via header).
- **claude-code-router** - Copyright (c) 2025 musistudio - MIT License - https://github.com/musistudio/claude-code-router (request transformers, model mapping by kind of work).
- **OmniRoute** - Copyright (c) 2026 diegosouzapw - MIT License - https://github.com/diegosouzapw/OmniRoute (provider circuit breaker, per-key cooldown honouring Retry-After, per-model lockout).

The MIT License: Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

Ideas only, no code: RouteLLM (Apache-2.0, LMSYS) and free-claude-code (AGPL-3.0, Ali Khokhar).
