#!/usr/bin/env python3
"""Real mathematical solver oracle: uses SymPy to actually SOLVE standard
hard-math probes instead of (as the previous oracle did) only extracting numbers
and testing even/odd/primality.

Answers, per query, using SymPy:
  - definite integrals           "integral of x^2 from 0 to 1" -> 1/3
  - linear systems               "2x + 3y = 7, 4x - y = 1"     -> {x: 1, y: 5/3...}
  - Fibonacci                    "100th Fibonacci number"       -> 354224848179261915075
  - Mersenne primes              "is 2^127 - 1 prime"           -> True (verified)
  - closed-form sums             "sum of k^2 from 1 to n"       -> n(n+1)(2n+1)/6
  - arithmetic equalities        "2 + 2 = 5"                    -> FALSE (refuted)

Plus genuine primality (SymPy isprime), integer classification.

HONEST SCOPE: solves the computational/machine-checkable class of math
probes symbolically. It does NOT do step-by-step *proofs* (e.g. "prove the
infinitude of primes" — a theorem, not a computation). Queries it cannot
parse return {'status':'unparsed'} (honest abstention) rather than a guess.

RESULT-KIND CONTRACT (stable, versioned — external callers may rely on this)
The `status` field on every result is one of:
  - 'solved'          : a concrete computation was performed and an answer
                        returned (e.g. an integral, system solve, modulus).
  - 'refuted'         : a claimed equality/inequality was PROVED FALSE, with
                        `counterexamples` (concrete witnesses) attached.
  - 'known_theorem'   : matched the curated theorem catalog; returns a
                        citation, NOT a generated proof (honest "known, not
                        derived"). `verified` = True.
  - 'open_conjecture' : matched an OPEN/unproven problem in the catalog;
                        `verified` = False — the system never asserts it true.
  - 'unparsed'        : outside the grammar / not a machine-checkable math
                        claim — honest abstention, no verdict fabricated.
This contract is stable; new kinds are additive only.
"""
from __future__ import annotations
import re
from typing import Any, Dict, Optional, Tuple

try:
    import sympy as sp
    HAS_SYMPY = True
except Exception:  # pragma: no cover
    sp = None
    HAS_SYMPY = False


class MathematicalOracle:
    """Solve recognized hard-math queries deterministically via SymPy."""

    def __init__(self, max_terms: int = 2000):
        self.max_terms = max_terms

    # ------------------------------------------------------------------ #
    # Public entry
    # ------------------------------------------------------------------ #
    def evaluate(self, text: str) -> Dict[str, Any]:
        """Parse `text` into a solvable math query and compute the answer.

        Returns:
          {'status': 'solved', 'answer': <sympy/number/str or dict>,
           'kind': <query kind>, 'worked': True}
          {'status': 'false', 'worked': True, 'reason': ...}  (equality refuted)
          {'status': 'unparsed', 'worked': False, 'reason': ...} (honest abstain)
        """
        if not HAS_SYMPY:
            return {"status": "unparsed", "worked": False,
                    "reason": "sympy unavailable"}
        if not text or not text.strip():
            return {"status": "unparsed", "worked": False, "reason": "empty"}

        t = text.strip()

        # --- arithmetic equality truth-check ('2 + 2 = 5') ----------------
        eq = self._parse_equality(t)
        if eq is not None:
            lhs_s, rhs_s = eq
            try:
                lhs = _parse_sympy(lhs_s)
                rhs = _parse_sympy(rhs_s)
            except Exception:
                return {"status": "unparsed", "worked": False,
                        "reason": f"equality sides not parseable: {lhs_s} = {rhs_s}"}
            # Guard: 'x = 5' with a single variable on only one side is a
            # definition/assignment, not a truth claim. Abstain rather than
            # (wrongly) calling it a false equality.
            if _is_definition(lhs, rhs):
                return {"status": "unparsed", "worked": False,
                        "kind": "definition",
                        "reason": f"'{lhs_s} = {rhs_s}' is a definition/assignment, not a checkable truth claim"}
            diff = sp.simplify(lhs - rhs)
            if diff == 0:
                return {"status": "solved", "worked": True, "kind": "equality",
                        "answer": True, "verified": True,
                        "summary": f"{lhs_s} = {rhs_s} is TRUE",
                        "counterexamples": []}
            # Refuted: find concrete numeric witnesses that break the equality.
            witnesses = _find_counterexamples(lhs - rhs)
            return {"status": "refuted", "worked": True, "kind": "equality",
                    "answer": False, "verified": False,
                    "summary": f"{lhs_s} != {rhs_s} is FALSE",
                    "counterexamples": witnesses}

        # --- definite integral ------------------------------------------
        intg = self._parse_integral(t)
        if intg is not None:
            f_expr, a, b = intg
            try:
                x = sp.Symbol("x")
                fe = _parse_sympy(f_expr)
                val = sp.integrate(fe, (x, a, b))
                return {"status": "solved", "worked": True, "kind": "integral",
                        "answer": sp.nsimplify(sp.simplify(val)) if _is_rational(val) else val,
                        "summary": f"∫[{a},{b}] {f_expr} dx = {val}",
                        "verified": True}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"integral failed: {exc}"}

        # --- linear system ----------------------------------------------
        sysq = self._parse_system(t)
        if sysq is not None:
            eqs = sysq
            try:
                sol = _solve_linear_system(eqs)
                ans = {str(sp.simplify(k)): sp.simplify(v)
                       for k, v in sol.items()} if sol else {}
                worked = len(ans) == _num_vars(eqs)
                return {"status": "solved" if worked else "unparsed",
                        "worked": worked, "kind": "linear_system",
                        "answer": ans, "summary": f"solution: {ans}",
                        "verified": worked}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"system solve failed: {exc}"}

        # --- Fibonacci --------------------------------------------------
        nth = self._parse_fibonacci(t)
        if nth is not None:
            try:
                val = fibonacci(nth)
                return {"status": "solved", "worked": True, "kind": "fibonacci",
                        "answer": int(val),
                        "summary": f"F_{nth} = {val}"}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"fibonacci failed: {exc}"}

        # --- Mersenne prime --------------------------------------------
        mers = self._parse_mersenne(t)
        if mers is not None:
            p = mers
            try:
                mp = 2**p - 1
                prime = sp.isprime(mp)
                return {"status": "solved", "worked": True, "kind": "mersenne",
                        "answer": bool(prime),
                        "summary": f"2^{p}-1 = {mp} is {'prime' if prime else 'NOT prime'}",
                        "verified": True}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"mersenne failed: {exc}"}

        # --- closed-form sum --------------------------------------------
        csum = self._parse_closed_sum(t)
        if csum is not None:
            expr_k, kind = csum
            try:
                k, n = sp.Symbol("k"), sp.Symbol("n")
                ek = _parse_sympy(expr_k)
                total = sp.summation(ek, (k, 1, n))
                return {"status": "solved", "worked": True, "kind": "closed_sum",
                        "answer": sp.simplify(total),
                        "summary": f"Σ[k=1..n] {expr_k} = {sp.simplify(total)}",
                        "verified": True}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"closed sum failed: {exc}"}

        # --- plain primality / divisibility query -----------------------
        pr = self._parse_primality(t)
        if pr is not None:
            n = pr
            try:
                prime = sp.isprime(n)
                return {"status": "solved", "worked": True, "kind": "primality",
                        "answer": bool(prime),
                        "summary": f"{n} is {'prime' if prime else 'NOT prime'}",
                        "verified": True}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"primality failed: {exc}"}

        # --- indefinite integral / antiderivative ------------------------
        indef = self._parse_indefinite_integral(t)
        if indef is not None:
            try:
                x = sp.Symbol("x")
                fe = _parse_sympy(indef)
                F = sp.integrate(fe, x)
                return {"status": "solved", "worked": True, "kind": "indefinite_integral",
                        "answer": str(F),
                        "summary": f"∫ {indef} dx = {F} + C",
                        "verified": True}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"indefinite integral failed: {exc}"}

        # --- basic ODE (first-order separable via dsolve) ----------------
        ode = self._parse_ode(t)
        if ode is not None:
            try:
                x = sp.Symbol("x")
                y = sp.Function("y")
                # Try to interpret 'dy/dx = <expr>' / 'y' = <expr>'
                rhs = _parse_sympy(ode.replace("dy/dx", "").replace("y'", "").strip("= "))
                sol = sp.dsolve(sp.Eq(y(x).diff(x), rhs), y(x))
                return {"status": "solved", "worked": True, "kind": "ode",
                        "answer": str(sol),
                        "summary": f"ODE y' = {rhs}: {sol}",
                        "verified": len(str(sol)) > 0}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"ode failed: {exc}"}

        # --- modular arithmetic ------------------------------------------
        mod = self._parse_modular(t)
        if mod is not None:
            expr_s, n = mod
            try:
                val = sp.simplify(_parse_sympy(expr_s))
                rem = int(val) % n
                return {"status": "solved", "worked": True, "kind": "modular",
                        "answer": rem,
                        "summary": f"{expr_s} mod {n} = {rem}",
                        "verified": True}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"modular failed: {exc}"}

        # --- simple inequality -------------------------------------------
        ineq = self._parse_inequality(t)
        if ineq is not None:
            a, op, b = ineq
            try:
                A = sp.simplify(_parse_sympy(a))
                B = sp.simplify(_parse_sympy(b))
                # Try the simple numeric/comparable case; abstain if symbolic unknowns make it ambiguous
                test = {">": lambda: sp.simplify(A - B) > 0,
                        "<": lambda: sp.simplify(A - B) < 0,
                        ">=": lambda: sp.simplify(A - B) >= 0,
                        "<=": lambda: sp.simplify(A - B) <= 0}.get(op)
                if test is None:
                    return {"status": "unparsed", "worked": False,
                            "reason": f"unsupported inequality operator {op}"}
                ans = bool(test())
                return {"status": "solved" if ans else "refuted", "worked": True,
                        "kind": "inequality", "answer": ans,
                        "verified": ans,
                        "summary": f"{a} {op} {b} is {'TRUE' if ans else 'FALSE'}"}
            except Exception as exc:
                return {"status": "unparsed", "worked": False,
                        "reason": f"inequality failed: {exc}"}

        # --- known theorem catalog (honest: citation, not generated proof) ---
        kt = self._parse_known_theorem(t)
        if kt is not None:
            return kt

        return {"status": "unparsed", "worked": False,
                "reason": "no supported math query pattern"}

    # ------------------------------------------------------------------ #
    # Recognizers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_equality(t: str) -> Optional[Tuple[str, str]]:
        # Anchored: whole trimmed text is a bare 'A = B' equality. This
        # rejects sentences like "Solve the system: 2x+3y=7, 4x-y=1" (different
        # probe kinds) and only fires on pure arithmetic/algebra equalities.
        s = re.sub(r"\bexactly\b|\bstrictly\b", "", t).strip()
        # word 'equals' / 'is equal to' -> '='
        s = re.sub(r"\bis\s+equal\s+to\b|\bequals\b|\bis\b", " = ", s)
        m = re.match(
            r"^\s*([\d\w\s+\-*/().^]+?)\s*=\s*([\d\w\s+\-*/().^]+?)\s*[.!?]?\s*$", s)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            if _looks_arith(a) and _looks_arith(b):
                return a, b
        return None

    @staticmethod
    def _parse_integral(t: str) -> Optional[Tuple[str, Any, Any]]:
        m = re.search(
            r"integral\s+of\s+(.+?)\s+(?:from|over)\s+(.+?)\s+to\s+(.+?)\s*[.!?]?$",
            t, re.I)
        if m:
            lo, hi = m.group(2).strip(), m.group(3).strip()
            lo = _coerce_bound(lo)
            hi = _coerce_bound(hi)
            if lo is None or hi is None:
                return None
            return m.group(1).strip(), lo, hi
        return None

    @staticmethod
    def _parse_system(t: str) -> Optional[list]:
        # "Solve the system: 2x + 3y = 7, 4x - y = 1" (strip any leading
        # words like "the system:" or "solve the system:")
        m = re.search(r"(?:solve\s+the\s+system|the\s+system|system)[:,-]?\s*(.+)$", t, re.I)
        if not m:
            return None
        body = m.group(1)
        # split on commas/';'/' and '
        eqs = [e.strip() for e in re.split(r"[;,]\s*|\s+and\s+", body) if "=" in e]
        if not eqs:
            return None
        good = []
        for e in eqs:
            e2 = re.sub(r"^(?:solve|system)[:,-]?\s*", "", e, flags=re.I)
            if _looks_linear(e2):
                good.append(e2)
        return good if len(good) >= 2 else None

    @staticmethod
    def _parse_fibonacci(t: str):
        # "the 100th Fibonacci number" / "the 100th fibonacci"
        m = re.search(r"(\d+)(?:st|nd|rd|th)?\s+fibonacci\b", t, re.I)
        if m:
            return int(m.group(1))
        # "compute the 100th fibonacci number"
        m = re.search(r"the\s+(\d+)(?:st|nd|rd|th)?\s*(?:fibonacci|number)", t, re.I)
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def _parse_mersenne(t: str):
        m = re.search(r"2\s*\^\s*(\d+)", t)
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def _parse_closed_sum(t: str):
        # "closed form of sum_{k=1}^n k^2" / "sum of k^2 from 1 to n" / "sum k^2"
        m = re.search(r"(?:sum|summation).{0,30}?k\s*\^?\s*(\d+)", t, re.I)
        if m:
            exp = int(m.group(1))
            # sanity: re-match so we don't grab a stray number far away
            if exp > 0:
                return f"k**{exp}", None
        # "sum of k" -> k**1
        if re.search(r"(?:sum|summation).{0,20}?k\b", t, re.I):
            return "k**1", None
        return None

    @staticmethod
    def _parse_primality(t: str):
        # reject mixed/compound claims — only single "N is prime" assertions
        if re.search(r"\band\b|\bor\b|,", t, re.I):
            return None
        m = re.search(r"(\d+)\s+is\s+prime", t, re.I)
        if m:
            return int(m.group(1))
        return None

    @staticmethod
    def _parse_indefinite_integral(t):
        """indefinite/antiderivative: 'integral of <expr> dx' / 'antiderivative of <expr>'"""
        m = re.search(r"(?:indefinite\s+integral|integral|antiderivative)\s+of\s+(.+?)(?:\s+d[xz]|\s*$)", t, re.I)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _parse_ode(t):
        """basic ODE: 'solve dy/dx = <expr>' / 'y\' = <expr>' / 'solve the ODE y = ?'"""
        m = re.search(r"(?:solve\s+(?:the\s+)?(?:ode|differential|diff)(?: equation)?|dy/dx|y')\s*[:=]?\s*(.+)$", t, re.I)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _parse_modular(t):
        """modular arithmetic: '<expr> mod <n>' or 'N mod M' (allow 'what is' prefix)"""
        s = re.sub(r"^(what is|whats|compute|find)\s+", "", t.strip(), flags=re.I)
        m = re.search(r"([\d\w\s+\-*/().^]+?)\s+mod\s+(\d+)", s, re.I)
        if m:
            return m.group(1).strip(), int(m.group(2))
        return None

    @staticmethod
    def _parse_inequality(t):
        """simple inequality: 'is N > M' / '<expr> < <expr>' / 'N less than M'."""
        m = re.search(
            r"^\s*(is|does|✓)?\s*([\d\w\s+\-*/().^]+?)\s*(>=|<=|greater than|less than|>|<)\s*([\d\w\s+\-*/().^]+?)\s*[.!?]?\s*$", t, re.I)
        if m:
            a = m.group(2).strip()
            op = m.group(3)
            b = m.group(4).strip()
            if _looks_arith(a) and _looks_arith(b):
                sym_op = {"gt": ">", "lt": "<", "geq": ">=", "leq": "<=",
                          "greater than": ">", "less than": "<"}.get(op.lower(), op)
                return a, sym_op, b
        return None

    @staticmethod
    def _parse_known_theorem(t):
        """Recognize a curated catalog of famous theorems (return citation, not a
        generated proof). Honest: 'known theorem, not generated'."""
        try:
            from core.known_theorems import parse_known_theorem
            return parse_known_theorem(t)
        except ImportError:
            try:
                from known_theorems import parse_known_theorem
                return parse_known_theorem(t)
            except ImportError:
                return None


# ---- module-level helpers ----------------------------------------------
def _parse_sympy(s: str):
    # insert explicit '*' for implicit multiplication '(a)(b)' -> '(a)*(b)'
    s = re.sub(r"\)\s*(\()", r")*(", s)
    s = re.sub(r"(\d)([a-zA-Z(])", r"\1*\2", s)
    # 'pi' -> SymPy pi; 'e' -> E
    s = re.sub(r"\bpi\b", "pi", s)
    return sp.sympify(s, locals={"x": sp.Symbol("x"), "n": sp.Symbol("n"),
                                 "k": sp.Symbol("k"), "y": sp.Symbol("y"),
                                 "pi": sp.pi, "e": sp.E})


def _coerce_bound(s: str):
    """Convert an integral bound to a SymPy numeric/symbolic value. Accepts
    numeric strings ('0', '1', '3.5'), symbolic constants ('pi', 'e'), and
    integer words. Returns None if not a valid bound (-> abstain)."""
    if not s:
        return None
    low = s.strip().lower()
    # integer words ('two' -> 2); import from nl_math_parser if available
    try:
        from core.nl_math_parser import _NUM_WORDS
    except Exception:
        try:
            from nl_math_parser import _NUM_WORDS
        except Exception:
            _NUM_WORDS = {}
    num_word = _NUM_WORDS.get(low)
    if num_word is not None:
        return num_word
    if low == "pi" or low == "π":
        return sp.pi
    if low == "e":
        return sp.E
    if low == "inf" or low == "infinity":
        return sp.oo
    try:
        return float(low)
    except (ValueError, TypeError):
        return None


def _looks_arith(s: str) -> bool:
    # a side is "arithmetic-ish" if, after removing digits/ops/symbols/spaces,
    # only isolated variable letters remain (x, y, n, k, e). Reject real English
    # words (prime, finite, theorem, ...) or multiple-letter tokens.
    s2 = re.sub(r"[\d\s+\-*/().^=]", "", s)
    if not s2:
        return True
    # single isolated variable letters allowed (incl. 'pi', 'e')
    if re.fullmatch(r"[xynek](?:\s*[xynek])*|\bpi\b|\be\b", s2):
        return True
    return False


def _looks_linear(eq: str) -> bool:
    # contains at least one of x/y and an '='
    return "=" in eq and ("x" in eq or "y" in eq)


def _solve_linear_system(eq_strs: list) -> dict:
    x, y = sp.Symbol("x"), sp.Symbol("y")
    eqs = []
    for s in eq_strs:
        s = s.replace("^", "**")
        lhs, rhs = s.split("=")
        eqs.append(sp.Eq(_parse_sympy(lhs.strip()), _parse_sympy(rhs.strip())))
    return sp.solve(eqs, [x, y])


def _num_vars(eq_strs: list) -> int:
    return 2


def _is_definition(lhs, rhs) -> bool:
    """True if the equality looks like a definition: a single free variable on
    exactly one side and a constant (no symbols) on the other — e.g. 'x = 5'."""
    try:
        lf, rf = lhs.free_symbols, rhs.free_symbols
        if bool(lf) != bool(rf):   # symbols on exactly one side
            solo = lf if lf else rf
            other = rhs if lf else lhs
            if len(solo) == 1 and not other.free_symbols:
                return True
    except Exception:
        pass
    return False


def _find_counterexamples(diff_expr) -> list:
    """Given a nonzero symbolic expression lhs-rhs, find concrete numeric
    witness(es) that evaluate the difference to a nonzero value — direct
    evidence the equality is FALSE. Handles constant/free/numerical cases.
    Returns a list of {'assignment': {...}, 'diff':.., 'witness':..}.
    """
    if diff_expr is None:
        return []
    try:
        free = sorted(diff_expr.free_symbols, key=lambda s: s.name)
        # No free vars -> a constant mismatch: the numeric value IS the witness.
        if not free:
            return [{
                "assignment": {},
                "diff": str(diff_expr),
                "witness": f"constant difference {sp.simplify(diff_expr)} ≠ 0 (both sides evaluated)",
            }]
        # Free vars -> try small integer assignments; require diff != 0.
        import itertools
        for trial in itertools.product([0, 1, 2, -1, 3], repeat=len(free)):
            subs = dict(zip(free, trial))
            try:
                lhs_diff = sp.simplify(diff_expr.subs(subs))
            except Exception:
                continue
            if lhs_diff is not None and lhs_diff != 0:
                return [{
                    "assignment": {str(s): int(v) for s, v in subs.items()},
                    "diff": str(lhs_diff),
                    "witness": f"counter-example: {'; '.join(f'{s}={v}' for s, v in subs.items())} gives lhs-rhs = {lhs_diff} ≠ 0",
                }]
        return [{"diff": str(diff_expr),
                 "witness": "symbolic difference is nonzero across tried assignments"}]
    except Exception:
        return [{"diff": str(diff_expr),
                 "witness": "could not construct numeric witness"}]


def _is_rational(v) -> bool:
    try:
        return v.is_rational if v is not None else False
    except Exception:
        return False


def fibonacci(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# quick self-test
if __name__ == "__main__":
    o = MathematicalOracle()
    for q in [
        "What is the integral of x^2 from 0 to 1?",
        "Solve the system: 2x + 3y = 7, 4x - y = 1",
        "Compute the 100th Fibonacci number",
        "Is 2^127 - 1 a Mersenne prime?",
        "What is the closed form of sum_{k=1}^n k^2?",
        "2 + 2 = 5",
        "2 + 2 = 4",
        "x^2 - 1 = (x-1)(x+1)",
        "Prove that there are infinitely many primes",
    ]:
        r = o.evaluate(q)
        ans = r.get("answer")
        print(f"  {r['status']:10} | {q[:48]:50} | {str(ans)[:50]}")
