# Analysis Data - 2026-11-20

**Package:** 304 (data analysis, read-only)
**Source:** Claude/logs/agent-console-tokens.json + ~/.dream-router/usage.json
**Date:** 2026-11-20

## Findings

1. **Console token tracking**: cache_read and cache_creation are ALWAYS 0 in `Claude/logs/agent-console-tokens.json` while input is ~149M. Router combines cache_read+cache_creation into "input" (line 1850 in dream_router.py). Console's "total" = input+output+cache_read+cache_creation; router's "input" already includes cache_read+cache_creation. Need a check comparing both sources.

2. **Provider errors**: OpenRouter inclusionai/ling-3.2-flash:free has 151 errors on 154 requests (98% error rate). Baidu ERNIE 5.5 Flash Preview Free has 0 errors on 2 requests (0% error rate).

3. **Free model usage**: Kilo nemotron-3.5-super-vl:free shows 54 errors on 190 requests (28% error rate), with 15.1M input and 62K output.

4. **Model count per provider**:
   - Claude Plan: 1 model (claude-sonnet-5)
   - Zai: 1 model (glm-4.7-flash)
   - Kilo: 1 model (nvidia/nemotron-3.5-super-vl:free)
   - Gemini: 1 model (gemini-flash-lite-latest)
   - OpenRouter: 2 models (inclusionai/ling-3.2-flash:free, baidu/ernie-5.5-flash-preview:free)

5. **Total token consumption (today)**: 149.3M total tokens (148.7M input + 0 cache_read + 0 cache_creation + 550K output).

6. **Recent activity**: Last request timestamp 1795178976 (2026-11-20), router uptime > 6 minutes, chain of 10 with airforce and orcarouter active.

7. **Provider performance ranking** (by error rate, lowest first):
   - Gemini Flash Lite (0% error rate, 2 requests)
   - Baidu ERNIE 5.5 Flash Preview Free (0% error rate, 2 requests)
   - Claude Sonnet 5 (0% error rate, 1017 requests)
   - Zai GLM-4.7 Flash (72 errors on 159 requests, 45% error rate)
   - Kilo Nemotron 3.5 Super VL Free (54 errors on 190 requests, 28% error rate)
   - OpenRouter InclusionAI Ling 3.2 Flash Free (151 errors on 154 requests, 98% error rate)

8. **Input vs output ratio**: Average input/output ratio is 270:1 (148.7M input / 550K output) across all providers today.

9. **Router state**: Router is running (uptime > 6 min), mode safe, chain of 10 active with airforce and orcarouter.

10. **Cache efficiency**: Zero cache_read and cache_creation in console logs indicates either no cache usage or a logging bug. Router's "input" field includes cache data, so the discrepancy should be investigated.

## Data Sources

- `Claude/logs/agent-console-tokens.json` (updated 2026-11-20T12:46:58.3118174Z)
- `~/.dream-router/usage.json` (last request 1795178976.4535778)
- `~/.dream-router/safety-samples.jsonl` (referenced in router config)
