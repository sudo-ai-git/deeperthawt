# DeeperThawt

**Deterministic verifiable reasoning engine** — solves hard math, verifies logic, retrieves cited knowledge, and detects semantically-near token waste — with **zero hallucination**, because the answers are computed, not guessed.

- **Symbolic math oracle** — deterministic SymPy solver: integrals, systems, Fibonacci, primes, modular arithmetic, inequality. Verifies true claims (`2 + 2 = 4` → **TRUE**), refutes false ones (`2 + 2 = 5` → **REFUTED**, with witnesses), and honestly abstains on what it can't prove.
- **Logic engine** — modus ponens/tollens, syllogism, conjunction, double-negation. `verified / invalid / insufficient` — never guesses.
- **Cited knowledge** — known theorems (Euclid, Fermat, etc.), science facts, Python knowledge. Retrieval with citations, *not* generation.
- **Semantic token intelligence** — the secret engine (gematria projection + fixed-parameter attention + trained latent adapter) runs **server-side** and returns only numbers. It finds the near-duplicate token waste exact-dedupe misses.

## Architecture: secret ingredients stay remote

```
  ┌────────────────────────────────────────────────────────────┐
  │  DeeperThawt (pip package, local)                           │
  │                                                            │
  │  · math oracle          (deterministic, SHIPPED)            │
  │  · logic engine         (deterministic, SHIPPED)            │
  │  · cited knowledge      (deterministic, SHIPPED)            │
  │  · semantic RPC client  (numeric-only, SHIPPED)             │
  │                        ╭───────────────────╮               │
  └────────────────────────┤  POST /assess     │───────────────┘
                           │  (de-identified)  │
                           │        ▼          │
                           │  REMOTE server    │
                           │  · gematria proj. │  ══ THE SECRET ══
                           │  · attention      │  engine + tuned
                           │  · trained adapter│  weights live
                           │  · tuned weights  │  ONLY HERE
                           ╰───────────────────╯
```

The **secret ingredients** — the semantic projection method, the fixed-parameter attention, the trained latent adapter, and the tuned weights — are **never shipped locally**. A local buyer gets a pip package with the deterministic solvers and a thin RPC client; the secret engine runs only on the remote DeeperThawt server behind a paid entitlement gate, returning **numbers only**.

## Service layer (unified product — thawt-api merged)

As of v2.0.0, the deterministic engine ships with a built-in no-LLM HTTP service
(`deeperthawt.service`). Run it locally:

```bash
python -m deeperthawt.service          # http://127.0.0.1:8105
# THAWT_HOST / THAWT_PORT / THAWT_API_KEY (optional bearer) / THAWT_DEBUG
```

Endpoints: `/healthz`, `/v1/math/verify`, `/v1/math/solve`, `/v1/logic/verify`,
`/v1/knowledge/{theorem,science,python}`, `/v1/semantic/assess`,
`/v1/evidence` (measured token-cost intelligence), `/v1/capabilities`.

> Merge note (2026-08-29): this service folds in the former `thawt-api` repo and
> calls the local `DeeperThawt` engine directly (the thawt-api repo carried
> byte-identical copies of the same engine files — a dual-vendor hazard now
> removed). `token-analytics` is wired in as the deterministic `/v1/evidence`
> data product. One product, one engine, one deployable service.

## Install

```bash
pip install deeperthawt
# or from source:
git clone https://github.com/sudo-ai-git/deeperthawt.git
cd deeperthawt && pip install -e .
```

## Quick start

```python
from deeperthawt import DeeperThawt

engine = DeeperThawt()

# Hard math — deterministic, no LLM guessing
engine.solve_math("integral of x^2 from 0 to 1")   # solved, 1/3
engine.solve_math("2 + 2 = 5")                     # refuted, with witness
engine.solve_math("2 + 2 = 4")                     # verified True

# Logic
engine.verify_logic(
    ["if it rains then the ground is wet", "it rains"],
    "the ground is wet")                           # {"status": "valid"}

# Cited knowledge
engine.knowledge_math_theorem("infinitely many primes")  # Euclid, cited
engine.knowledge_science("why is the sky blue")          # fact + reference

# Semantic token intelligence — runs on the REMOTE server
engine = DeeperThawt(api_base="https://mcp-token-saver-pro.fly.dev")
engine.semantic_assess([...messages...])            # returns numbers only
```

## CLI

```bash
deeperthawt math "integral of x^2 from 0 to 1"
deeperthawt logic "if it rains then the ground is wet; it rains" "the ground is wet"
deeperthawt theorem "infinitely many primes"
deeperthawt science "why is the sky blue"
deeperthawt python "list comprehension"
deeperthawt selfcheck        # 8/8 capability smoke test
```

## The honesty contract

1. **Deterministic** — same input → same answer, every time. No stochastic LLM in the scoring path. You can re-run and reproduce.
2. **No hallucination** — the engine solves/verifies/refutes what it can *prove*, and **abstains** (says "not verifiable") on what it can't. It never invents an answer.
3. **Opaque but auditable** — the deterministic solvers are open (AGPL). The semantic engine is server-side; you see the **contract and the number**, not the method.
4. **What it doesn't claim** — DeeperThawt does not generate prose, write code, or "reason" generally. It *computes* and *verifies*. The claims on this page are about provable operations.

## License: dual-license

- **Open core (AGPL-3.0)**: the deterministic solvers (math, logic, knowledge) are open source under AGPL.
- **Commercial license**: for embedding DeeperThawt inside a **closed-source product or SaaS** without AGPL obligations. View the full commercial grant in [`LICENSE.commercial.md`](LICENSE.commercial.md).

For a commercial license, contact the maintainer via the [landing page](https://sudo-ai-git.github.io/deeperthawt/).

© 2026 DeeperThawt maintainer.
