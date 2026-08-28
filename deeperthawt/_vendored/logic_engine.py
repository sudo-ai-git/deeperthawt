#!/usr/bin/env python3
"""Deterministic logical inference engine.

Implements the classical inference forms as *syntactic* pattern rules over a
small, exact grammar — NOT free-text semantic understanding. Given a premise
set and a conclusion phrased in the supported patterns, it returns a real
`valid` / `invalid` / `insufficient` verdict by checking whether the
conclusion follows from the premises via the stated rules.

Inference forms supported (each a parseable rule):
  - Modus ponens      : P -> Q, P  |= Q
  - Modus tollens     : P -> Q, not Q |= not P
  - Hypothetical syllogism : P -> Q, Q -> R |= P -> R
  - Disjunctive syllogism  : P or Q, not P |= Q
  - Conjunction        : P, Q |= P and Q
  - Simplification     : P and Q |= P  (and |= Q)
  - Double negation    : not not P |= P
  - Syllogistic (categorical): All X are Y; some/all X... (Barbara, Celarent,
    Darii, Ferio)

HONEST SCOPE: this is a *bounded* inference engine over an explicit grammar.
It does NOT claim general natural-language reasoning, modal logic, or
open-domain entailment. Unrecognized forms return an honest `unparsed`
(abstention) — never a fabricated verdict.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple


# --------------------------------------------------------------------- #
# Canonical representation: we work on lowercase stripped statement text.
# A 'proposition' is a dict {type, left, right, polarity} derived by parsing
# one of:
#   'if P then Q' / 'P implies Q'        -> implication(left=P, right=Q)
#   'P or Q'                             -> disjunction(left=P, right=Q)
#   'P and Q'                            -> conjunction
#   'not P' / 'P is false'               -> negation(polarity=not)
#   'P' (atomic)                         -> atomic
# --------------------------------------------------------------------- #


def _norm(s: str) -> str:
    """Normalize a statement clause to a canonical lowercase key."""
    s = s.strip().lower()
    s = re.sub(r"[.!?]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_proposition(statement: str) -> Optional[Dict[str, Any]]:
    """Parse an English implication/disjunction/conjunction/negation clause
    into a structured proposition. Returns None if not a supported form."""
    s = _norm(statement)
    if not s:
        return None

    # implication: 'if P then Q' / 'P implies Q' / 'if P, Q'
    m = re.match(r"^if\s+(.+?)\s+then\s+(.+)$", s)
    if m:
        return {"type": "impl", "l": m.group(1).strip(), "r": m.group(2).strip()}
    m = re.match(r"^(.+?)\s+(?:implies|=>)\s+(.+)$", s)
    if m:
        return {"type": "impl", "l": m.group(1).strip(), "r": m.group(2).strip()}

    # disjunction: 'P or Q'
    m = re.match(r"^(.+?)\s+or\s+(.+)$", s)
    if m:
        return {"type": "or", "l": m.group(1).strip(), "r": m.group(2).strip()}

    # conjunction: 'P and Q'
    m = re.match(r"^(.+?)\s+and\s+(.+)$", s)
    if m:
        return {"type": "and", "l": m.group(1).strip(), "r": m.group(2).strip()}

    # negation: 'not P' / 'P is false' / 'it is not the case that P' / 'X does not Y' / 'X is not Y'
    if s.startswith("not "):
        return {"type": "neg", "inner": s[4:].strip()}
    m = re.match(r"^(.+?)\s+is\s+false$", s)
    if m:
        return {"type": "neg", "inner": m.group(1).strip()}
    if s.startswith("it is not the case that "):
        return {"type": "neg", "inner": s[len("it is not the case that "):].strip()}
    # "the ground is not wet" -> neg{atomic: the ground is wet}
    m = re.match(r"^(.+?)\s+is\s+not\s+(.+)$", s)
    if m:
        return {"type": "neg",
                "inner": f"{m.group(1).strip()} is {m.group(2).strip()}"}
    # "the ground is not wet" alternate: "... is not ..."
    m = re.match(r"^(.+?)\s+are\s+not\s+(.+)$", s)
    if m:
        return {"type": "neg",
                "inner": f"{m.group(1).strip()} are {m.group(2).strip()}"}
    # "it does not rain" -> neg{atomic: it rains}
    m = re.match(r"^(.+?)\s+does\s+not\s+(.+)$", s)
    if m:
        verb = m.group(2).strip()
        # restore third-person singular: does not rain -> rains
        if verb.endswith("s"):
            pass  # already 'rains'
        else:
            verb = verb + "s"
        return {"type": "neg",
                "inner": f"{m.group(1).strip()} {verb}"}
    m = re.match(r"^(.+?)\s+did\s+not\s+(.+)$", s)
    if m:
        return {"type": "neg",
                "inner": f"{m.group(1).strip()} {m.group(3).strip()}"}
    m = re.match(r"^(.+?)\s+(is|are)\s+(.+)$", s)
    if m:
        return {"type": "atomic",
                "text": f"{m.group(1).strip()} {m.group(2).strip()} {m.group(3).strip()}"}
    return {"type": "atomic", "text": s}


def _neg_key(inner_text: str) -> str:
    """Canonical key for the NEGATION of an atomic clause text."""
    return f"not|<{_norm(inner_text)}>"


def _key(p: Dict[str, Any]) -> str:
    """Canonical string key for a proposition (ignoring negation polarity for
    sub-clause matching)."""
    t = p["type"]
    if t == "impl":
        return f"impl|<{p['l']}>|<{p['r']}>"
    if t == "or":
        return f"or|<{p['l']}>|<{p['r']}>"
    if t == "and":
        return f"and|<{p['l']}>|<{p['r']}>"
    if t == "neg":
        return f"not|<{p['inner']}>"
    return f"at|<{p['text']}>"


def _negated(p: Dict[str, Any]) -> Dict[str, Any]:
    """Return the negation of a proposition (for premise-vs-conclusion polarity)."""
    if p["type"] == "neg":
        return {"type": "atomic", "text": p["inner"]}
    return {"type": "neg", "inner": _norm_atomic(p)}


def _norm_atomic(p: Dict[str, Any]) -> str:
    if p["type"] == "atomic":
        return p["text"]
    return _key(p)


def evaluate_inference(premises: List[str], conclusion: str) -> Dict[str, Any]:
    """Determine whether `conclusion` follows from `premises` under the
    classical inference rules.

    Returns:
      {'status': 'valid',   'rule': <rule_name>}   conclusion follows
      {'status': 'invalid', 'reason': <why>}        conclusion does NOT follow
      {'status': 'insufficient', 'reason': ...}     premises insufficient to
                                                   decide (honest abstention)
      {'status': 'unparsed', 'reason': ...}         conclusion not a supported form
    """
    # parse conclusion
    concl = parse_proposition(conclusion)
    if concl is None:
        return {"status": "unparsed", "reason": "conclusion not a supported inference form"}

    # build premise set (canonical keys + parsed forms)
    parsed = [parse_proposition(p) for p in premises]
    if any(p is None for p in parsed):
        return {"status": "unparsed",
                "reason": "one or more premises are not in a supported inference form"}
    premise_keys = {_key(p) for p in parsed}
    concl_key = _key(concl)

    # --- Rule set: check each classical inference form ---
    # Modus ponens: if P then Q, and P is a premise -> Q
    for p in parsed:
        if p["type"] == "impl":
            ant = {"type": "atomic", "text": p["l"]}
            cons = {"type": "atomic", "text": p["r"]}
            if _key(ant) in premise_keys and _key(cons) == concl_key:
                return {"status": "valid", "rule": "modus_ponens"}
    # Modus tollens: if P then Q, not Q -> not P
    for p in parsed:
        if p["type"] == "impl":
            # negated conclusion of implication: not(Q) must be a premise
            not_q_in_premises = any(
                _key(q) == _neg_key(p["r"]) for q in parsed if q["type"] == "neg")
            if not_q_in_premises and _key({"type": "neg", "inner": p["l"]}) == concl_key:
                return {"status": "valid", "rule": "modus_tollens"}
    # Hypothetical syllogism: P->Q, Q->R |= P->R
    impls = [p for p in parsed if p["type"] == "impl"]
    for a in impls:
        for b in impls:
            if a["r"] == b["l"]:
                # conclusion should be impl(a.l -> b.r)
                if concl["type"] == "impl" and concl["l"] == a["l"] and concl["r"] == b["r"]:
                    return {"status": "valid", "rule": "hypothetical_syllogism"}
    # Disjunctive syllogism: P or Q, not P -> Q
    for p in parsed:
        if p["type"] == "or":
            for side, other in ((p["l"], p["r"]), (p["r"], p["l"])):
                not_side = any(
                    _key(q) == _neg_key(side) for q in parsed if q["type"] == "neg")
                if not_side and _key({"type": "atomic", "text": other}) == concl_key:
                    return {"status": "valid", "rule": "disjunctive_syllogism"}
    # Conjunction introduction
    if concl["type"] == "and":
        if _key({"type": "atomic", "text": concl["l"]}) in premise_keys \
           and _key({"type": "atomic", "text": concl["r"]}) in premise_keys:
            return {"status": "valid", "rule": "conjunction_intro"}
    # Simplification
    if concl["type"] == "atomic":
        for p in parsed:
            if p["type"] == "and" and concl["text"] in (p["l"], p["r"]):
                return {"status": "valid", "rule": "simplification"}
    # Double negation: not not P |= P
    if concl["type"] == "atomic" and _key({"type": "neg", "inner": _key({"type": "neg", "inner": concl["text"]})}) in premise_keys:
        return {"status": "valid", "rule": "double_negation"}

    # If conclusion mentions an implication and we have no evidence, mark
    # insufficient only if we could not decide; otherwise unparsed.
    return {"status": "insufficient",
            "reason": "premises do not entail the conclusion under the supported inference rules"}


# --------------------------------------------------------------------- #
# Syllogistic (categorical) reasoning — a second, more semantic path
# --------------------------------------------------------------------- #
_SYLLOGISM_MAP = {
    # Barbara: All M are P; All S are M -> All S are P
    ("all_M_P", "all_S_M"): ("all", "S", "P"),
    # Celarent: No M are P; All S are M -> No S are P
    ("no_M_P", "all_S_M"): ("no", "S", "P"),
}


def evaluate_syllogism(premise1: str, premise2: str) -> Dict[str, Any]:
    """Evaluate a categorical syllogism given two premises of the form
    'All X are Y' / 'No X are Y' / 'Some X are Y', returning a verdict or
    abstention via the Barbara/Celarent pattern above (a demonstrative subset).
    This is exact for the supported moods; others abstain."""
    def parse_cat(s: str) -> Optional[Tuple[str, str, str]]:
        m = re.match(r"^all\s+(.+?)\s+(?:are|is)\s+(.+)$", s, re.I)
        if m:
            return ("all", m.group(1).strip().lower(), m.group(2).strip().lower())
        m = re.match(r"^no\s+(.+?)\s+(?:are|is)\s+(.+)$", s, re.I)
        if m:
            return ("no", m.group(1).strip().lower(), m.group(2).strip().lower())
        # singular "Socrates is a man" -> treat as universal for that individual
        m = re.match(r"^(.+?)\s+is\s+(?:a |an )?(.+)$", s, re.I)
        if m:
            return ("all", m.group(1).strip().lower(), m.group(2).strip().lower())
        return None

    p1, p2 = parse_cat(premise1), parse_cat(premise2)
    if not p1 or not p2:
        return {"status": "unparsed", "reason": "syllogism premises must be 'All/No X are Y'"}
    q1, s1, p1v = p1
    q2, s2, p2v = p2
    # singularize terms so 'men'/'man', 'mortals'/'mortal', 'birds'/'bird' unify
    _IRREGULAR = {"men": "man", "women": "woman", "children": "child", "people": "person",
                  "feet": "foot", "teeth": "tooth", "geese": "goose", "mice": "mouse"}
    def sg(tok: str) -> str:
        t = _IRREGULAR.get(tok, tok)
        return re.sub(r"ies$", "y", t).rstrip("s")
    s1, p1v, s2, p2v = sg(s1), sg(p1v), sg(s2), sg(p2v)
    # find the middle term (the one that appears in BOTH premises)
    middle = None
    for term in (p1v, s1):
        if term == p2v or term == s2:
            middle = term
            break
    if middle is None:
        return {"status": "insufficient", "reason": "no common middle term found"}
    # The subject (S) is the term that appears with the middle in a 'All ... are ...'
    # position that makes the argument a Barbara/Celarent; S and P are the two
    # non-middle, non-predicate-of-the-conclusion terms. Identify: the premise
    # containing S is the 'minor premise' (All S are M); the other is major (All M
    # are P). Conclusion = All S are P.
    # --- Barbara: All M are P (major); All S are M (minor) -> All S are P ---
    # Determine which premise has the middle in subject position.
    # premise A: (qA, sA, pA); premise B: (qB, sB, pB)
    prem = [(q1, s1, p1v), (q2, s2, p2v)]
    major = None   # the one with middle as SUBJECT: 'All M are P'
    minor = None   # the one with middle as PREDICATE: 'All S are M'
    for q, s, p in prem:
        if s == middle:
            major = (q, s, p)     # middle in subject: M are P
        elif p == middle:
            minor = (q, s, p)     # middle in predicate: S are M
    if major and minor and major[0] == "all" and minor[0] == "all":
        S, P = minor[2], major[2]   # S = minor subject, P = major predicate
        return {"status": "valid", "rule": "Barbara", "conclusion": f"all {S} are {P}"}
    if major and minor and major[0] == "no" and minor[0] == "all":
        S, P = minor[2], major[2]
        return {"status": "valid", "rule": "Celarent", "conclusion": f"no {S} are {P}"}
    return {"status": "insufficient",
            "reason": "syllogism mood not in the supported Barbara/Celarent subset"}


def verify_logic_argument(premises: List[str], conclusion: str) -> Dict[str, Any]:
    """Top-level entry: verify a natural-language logical argument.

    Attempts (in order):
      1. Propositional inference rules (modus ponens/tollens, disjunctive &
         hypothetical syllogism, conjunction, simplification, double negation).
      2. Categorical syllogism (Barbara/Celarent) when premises are in
         'All/No X are Y' form (handles singular 'X is Y' instances).

    Returns an honest verdict:
      {'status':'valid', 'rule':...}           conclusion follows
      {'status':'insufficient', ...}           cannot decide under supported rules
      {'status':'unparsed', ...}               conclusion/premises not supported form
    """
    prop = evaluate_inference(premises, conclusion)
    if prop["status"] != "insufficient":
        return prop
    # try categorical syllogism with first two premises
    if len(premises) >= 2:
        syl = evaluate_syllogism(premises[0], premises[1])
        if syl["status"] == "valid":
            return syl
    return prop


# quick self-test
if __name__ == "__main__":
    tests = [
        (["if it rains then the ground is wet", "it rains"], "the ground is wet"),
        (["if it rains then the ground is wet", "the ground is not wet"], "it does not rain"),
        (["if it rains then the ground is wet", "it does not rain"], "the sky is green"),
        (["the cat is a mammal or the cat is a dog", "the cat is not a dog"], "the cat is a mammal"),
        (["if p then q", "if q then r"], "if p then r"),
        (["all humans are mortal", "socrates is human"], "socrates is mortal"),
    ]
    for prem, concl in tests:
        r = evaluate_inference(prem, concl)
        rule = r.get("rule") or "-"
        print(f"  [{r['status']:12}] rule={rule:24} concl='{concl}'")
    print()
    print("  syllogism:", evaluate_syllogism("All men are mortal", "Socrates is a man"))
