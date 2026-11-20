#!/usr/bin/env python3
"""Race with an oracle (T-037).

Run the same small package on 2+ models in parallel (injected callables), run the
acceptance test as the oracle on each answer, and the first answer that passes
wins. Records the winner, its latency and which models lost (and why).

Pure module: no network, no file IO. Models are callables ``model(package) -> output``;
the oracle is ``oracle(output) -> bool``. A clock can be injected for tests.

Integration point (NOT wired here; dream_router.py is owned by another package):
in user-level-hooks/dream_router.py, where a T2 free-tier package is dispatched to a
single model, build ``models = {name: lambda pkg, n=name: call_free_model(n, pkg)}``
for two free models and call ``race(package, models, oracle=run_acceptance_test)``.
Use ``result["winner"]`` / ``result["output"]`` as the dispatch result and append
``result`` (without ``output``) to the routing telemetry to measure the gain in
acceptance rate and latency against a single run.
"""

import concurrent.futures as cf
import time
from typing import Callable, Dict, Optional


def race(package, models: Dict[str, Callable], oracle: Callable, clock: Callable[[], float] = time.monotonic,
         timeout: Optional[float] = None) -> dict:
    """Race ``models`` on ``package``. Returns a dict:

    ok       True if some model passed the oracle
    winner   name of the first passing model, or None
    output   winner's output, or None
    latency  seconds from start until the winner passed (or until all failed)
    losers   {name: "failed_oracle" | "error: <exc>" | "not_finished"}
    """
    if not models:
        raise ValueError("race needs at least one model")
    start = clock()
    pool = cf.ThreadPoolExecutor(max_workers=len(models))

    def run(name):
        out = models[name](package)
        return out, bool(oracle(out))

    futs = {pool.submit(run, n): n for n in models}
    losers, winner, output, latency = {}, None, None, None
    try:
        for f in cf.as_completed(futs, timeout=timeout):
            name = futs[f]
            try:
                out, passed = f.result()
            except Exception as e:  # a crashing model just loses
                losers[name] = "error: %s" % e
                continue
            if passed:
                winner, output, latency = name, out, clock() - start
                break
            losers[name] = "failed_oracle"
    except cf.TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    for n in models:
        if n != winner and n not in losers:
            losers[n] = "not_finished"
    if latency is None:
        latency = clock() - start
    return {"ok": winner is not None, "winner": winner, "output": output,
            "latency": latency, "losers": losers}
