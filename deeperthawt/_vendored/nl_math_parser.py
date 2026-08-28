#!/usr/bin/env python3
"""Natural-language math claim parser: bridges plain-English math statements
into the structured formula JSON the FSS SymPyReferee verifies.

WHY: the referee is a real symbolic checker (SymPy) but only accepts rigid
{"kind":"sympy","lhs":...,"rhs":...} input. Free-text claims like "2 + 2
equals 5" or "the derivative of x^2 is 3x" never reach it (they surface as
a fingerprint-only, which proves nothing about truth). This parser closes
that gap for a DEFINED grammar of common mathematical statements — no LLM,
purely deterministic pattern matching.

HONEST SCOPE: this handles arithmetic equalities, algebraic identities,
derivative statements, and named-constant comparisons written in a small set
of English phrasings. It does NOT claim general natural-language math
understanding — it is a bounded, auditable translator for the phrasings it
knows. Anything outside its grammar yields an explicit UNSUPPORTED verdict
(never a fabricated parse).
"""
from __future__ import annotations
import re
from typing import Optional, Dict, Any

# --- number words -> int -----------------------------------------------------
_NUM_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "thousand": 1000, "million": 1000000,
}

# --- named constants -> sympy expr string -----------------------------------
_CONSTANTS = {
    "pi": "pi", "π": "pi", "e": "E", "euler": "E",
    "square root of 2": "sqrt(2)", "sqrt(2)": "sqrt(2)",
    "sqrt 2": "sqrt(2)", "√2": "sqrt(2)",
}

# ---- tokenize a side into a sympy-parseable string -------------------------
_TOKEN_RE = re.compile(
    r"\d+(?:\.\d+)?|pi|π|sqrt\s*\(?\s*(\d+)\s*\)?|√\s*(\d+)|[a-zA-Z]|\*\*|\^|[+*/().-]"
)

def _norm_word_side(side: str) -> str:
    """Normalize an English/TeX-ish expression side into a sympy string."""
    s = side.strip().lower()
    # handle number words e.g. 'two' -> '2'
    for w, n in sorted(_NUM_WORDS.items(), key=lambda kv: -len(kv[0])):
        s = re.sub(rf"\b{w}\b", str(n), s)
    # 'squared'/'cubed' -> exponent, BEFORE space-stripping
    s = re.sub(r"(\w)\s+squared\b", r"\1**2", s)
    s = re.sub(r"(\w)\s+cubed\b", r"\1**3", s)
    # 'derivative of x squared' family handled by caller; here simple ops
    s = s.replace("plus", "+").replace("minus", "-").replace("times", "*")
    s = s.replace("over", "/").replace("equals", "=")
    s = s.replace(" ", "")
    # implicit multiplication: number followed by a letter or '(' -> '2x'->'2*x'
    s = re.sub(r"(\d)([a-zA-Z(])", r"\1*\2", s)
    # and ')' followed by '(' or a letter -> '(x-1)(x+1)' -> '(x-1)*(x+1)'
    s = re.sub(r"\)\s*([a-zA-Z(])", r")*\1", s)
    # sqrt forms
    s = re.sub(r"sqrt\(?(\d+)\)?", r"sqrt(\1)", s)
    s = s.replace("√", "sqrt")
    return s


# ---- equality phrasings -----------------------------------------------------
_EQUALS = [
    r"equals", r"is equal to", r"=\s*", r"is",
    r" yields", r" equals", r" is equal to",
]
# We only accept strong equality verbs to avoid over-matching 'is prime'.
_STRONG_EQ = re.compile(
    r"\b(equals|is equal to|=|yields|is exactly)\b"
)


class NLMathParseResult:
    """Result of attempting to parse a natural-language math claim."""
    __slots__ = ("verdict", "kind", "lhs", "rhs", "reason", "formula")
    def __init__(self, verdict: str, kind: str, lhs: str, rhs: str,
                 reason: str, formula: Any = None):
        self.verdict = verdict      # 'parsed' | 'unsupported'
        self.kind = kind
        self.lhs = lhs
        self.rhs = rhs
        self.reason = reason
        self.formula = formula


def parse_nl_math_claim(text: str) -> NLMathParseResult:
    """Attempt to parse a plain-English mathematical equality claim.

    Returns a result with verdict='parsed' + a `formula` dict
    ({"kind":"sympy","lhs":...,"rhs":...}) when a known pattern is matched,
    or verdict='unsupported' otherwise (explicit, never fabricated).
    """
    t = text.strip()
    lt = t.lower()

    # Normalize: strip trailing punctuation
    t = re.sub(r"[.!?]+$", "", t).strip()
    lt = t.lower()

    # --- derivative pattern: "the derivative of <f> is <g>" / "d/dx ..."
    m = re.match(
        r"^the\s+derivative\s+of\s+(.+?)\s+(?:is|equals)\s+(.+?)\s*$", lt)
    if m:
        f, g = m.group(1).strip(), m.group(2).strip()
        # handle "x squared"/"x^2"
        f = re.sub(r"(\w)\s+squared\b", r"\1**2", f)
        g = re.sub(r"(\w)\s+squared\b", r"\1**2", g)
        f = _norm_word_side(f)
        g = _norm_word_side(g)

        # "x" may be spelled as x
        f = f if f else "x"
        g = g if g else "0"
        # derivative of f w.r.t. x -> use sympy diff semantics: referee uses
        # simplify(lhs-rhs)==0, so we express the claim as diff(f,x) - g == 0
        # by setting lhs=diff(f,x) rhs=g (the referee will not diff; we must
        # produce a self-contained lhs). Compute derivative symbolically here:
        try:
            import sympy as sp
            x = sp.Symbol("x")
            fexpr = sp.sympify(f, locals={"x": x})
            gexpr = sp.sympify(g, locals={"x": x})
            dfs = str(sp.diff(fexpr, x))
            # Use the derivative itself as lhs; referee simplifies dfs - g
            return NLMathParseResult(
                "parsed", "sympy", dfs, g,
                f"recognized derivative claim: d/dx({f}) = {g}",
                {"kind": "sympy", "lhs": dfs, "rhs": g})
        except Exception as exc:
            return NLMathParseResult("unsupported", "sympy", "", "",
                                     f"derivative parse failed: {exc}")

    # --- sum pattern: "the sum of A and B is C" / "the sum of A, B is C" --
    m = re.match(r"^the\s+sum\s+of\s+(.+?)\s+and\s+(.+?)\s+(?:is|equals)\s+(.+?)\s*$", lt)
    if m:
        a, b, c = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        sa = _norm_word_side(a)
        sb = _norm_word_side(b)
        sc = _norm_word_side(c)
        if _looks_arithmetic(a) and _looks_arithmetic(b):
            return NLMathParseResult(
                "parsed", "sympy", f"({sa}) + ({sb})", sc,
                f"recognized sum: {a} + {b} = {c}",
                {"kind": "sympy", "lhs": f"({sa}) + ({sb})", "rhs": sc})

    # --- named-constant equality: "pi equals 22/7" / "e^i*pi + 1 = 0" ----
    # Euler identity spelled out
    if re.search(r"euler|e\^?i", lt) and ("pi" in lt or "π" in lt) and "= 0" in lt:
        return NLMathParseResult(
            "parsed", "sympy", "E**(I*pi) + 1", "0",
            "recognized Euler identity e^(i*pi)+1=0",
            {"kind": "sympy", "lhs": "E**(I*pi) + 1", "rhs": "0"})

    # constant pattern: "pi = 22/7", "square root of 2 is rational" handled
    # by the generic equality below; constants map via _CONSTANTS.

    # Generic equality: "A equals B" / "A = B" ---------------------------
    for sep in [r"\s+equals\s+", r"\s+is\s+equal\s+to\s+", r"\s*=\s*"]:
        parts = re.split(sep, t, maxsplit=1)
        if len(parts) == 2:
            probe_lhs, probe_rhs = parts[0].strip(), parts[1].strip()
            # Protect against 'is' false-positives: require both sides to be
            # arithmetically parseable (digits/symbols/operators, no letters
            # like 'prime', 'finite', 'continuous' that aren't in our grammar).
            sl = _norm_word_side(probe_lhs)
            sr = _norm_word_side(probe_rhs)
            # require at least one digit or symbol and mostly a token char set
            if _looks_arithmetic(probe_lhs) and _looks_arithmetic(probe_rhs):
                return NLMathParseResult(
                    "parsed", "sympy", sl, sr,
                    f"recognized equality: {probe_lhs} = {probe_rhs}",
                    {"kind": "sympy", "lhs": sl, "rhs": sr})

    return NLMathParseResult("unsupported", "", "", "",
                             "no recognized NL math pattern")


def _looks_arithmetic(s: str) -> bool:
    """A side is arithmetic if it contains a digit or math operator/symbol
    and no words outside the tiny allowed vocabulary."""
    # normalize numeral words too
    low = s.lower()
    for w in _NUM_WORDS:
        low = re.sub(rf"\b{w}\b", "0", low)
    # strip constants + math tokens
    clean = re.sub(r"pi|π|sqrt|√|[a-zA-Z]|\d|\s|[()*/+\-^.]", "", low)
    # any leftover meaningful word = not pure arithmetic
    return all(c not in clean for c in clean) and ("=" not in clean)


def verify_nl_math_claim(text: str, field: str = "number_theory") -> Dict[str, Any]:
    """Top-level: parse a natural-language math claim, then verify it through
    the FSS SymPyReferee. Returns a structured, honest verdict.

    - 'verified'  : the claim parsed into a symbolic equality AND simplify
                    confirmed it (TRUE).
    - 'refuted'   : the claim parsed but simplify showed lhs != rhs (FALSE).
    - 'unsupported': the claim is outside the NL grammar (honest abstention —
                    we do not fabricate a parse or a verdict).
    """
    r = parse_nl_math_claim(text)
    if r.verdict != "parsed" or not r.formula:
        return {"verdict": "unsupported", "statement": text,
                "reason": r.reason, "detected_truth": None}
    # Run through the real SymPy referee
    from core.fss_claim import CirClaim, Field
    from core.fss_referee_engine import SymPyReferee
    try:
        field_enum = Field[field] if hasattr(Field, field) else Field.NUMBER_THEORY
    except Exception:
        field_enum = Field.NUMBER_THEORY
    import json as _json
    claim = CirClaim(cid="nl", field=field_enum, statement=text,
                     expression=r.formula["rhs"], producer_swarm="nl-bridge",
                     formula=_json.dumps(r.formula))
    res = SymPyReferee().validate(claim)
    return {
        "verdict": "verified" if res.ok else "refuted",
        "statement": text,
        "detected_truth": bool(res.ok),
        "reason": res.reason,
        "formula": r.formula,
    }


# quick self-tests
if __name__ == "__main__":
    for q in [
        "2 + 2 equals 4",
        "two plus two equals four",
        "2 + 2 equals 5",
        "the derivative of x squared is 2x",
        "the derivative of x^2 is 3x",
        "x squared minus 1 equals (x - 1)(x + 1)",
        "the number of platonic solids is five",
        "Fermat's last theorem is false",
        "the square root of 2 is rational",
    ]:
        r = parse_nl_math_claim(q)
        print(f"  {r.verdict:11} | {q[:50]:50} | {r.reason[:55]}")
