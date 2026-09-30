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
