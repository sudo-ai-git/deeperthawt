#!/usr/bin/env python3
"""Curated puzzle-knowledge lookup — classic puzzle archetypes w/ solution patterns.

This is the KNOWLEDGE layer of "puzzle solving": for a set of well-known puzzle
types it returns the canonical solution pattern / principle (retrieved, not
generated), so the deterministic reasoner can apply a known method rather than
guess. Unknown puzzles return an explicit abstention (None) — the engine then
falls back to the solver procedure, never fabricating.

Scope note: retrieval of known archetypes + honest abstention on novel puzzles.
A general puzzle SOLVER is the companion distilled-skill (procedure); this table
provides the referenced pattern lookups it can use (e.g. Monty Hall: switch.
Counterfeit coin: binary/witnessed weighing. River crossing: state-space BFS.
Lightbulb switch: sequential state inference.)
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


PUZZLES: List[Dict[str, Any]] = [
    {
        "keys": ["monty hall", "monty-ha", "three doors", "switch doors", "pick a door"],
        "fact": ("Monty Hall: you pick a door, the host (who knows) opens an "
                 "unpicked losing door, then offers you the choice to switch. "
                 "Switching wins with probability 2/3; staying wins with 1/3."),
        "why": ("Over the initial 1/3 picks that were correct, switching always "
                "loses; over the 2/3 picks that were wrong, the host's forced "
                "reveal leaves the prize behind the remaining closed door, so "
                "switching wins 2/3 of the time."),
        "reference": "Vos Savant (1990); standard probability.",
    },
    {
        "keys": ["counterfeit coin", "fake coin", "balance scale", "weighing puzzle",
                 "12 coins", "twelve coins", "one counterfeit"],
        "fact": ("Counterfeit-coin: among 12 coins one is lighter or heavier "
                 "(unknown direction); find it and its direction in 3 balance "
                 "weighings (information-theoretic optimum: 3 weighings x 3 "
                 "outcomes = 27 states, enough for 24 coin/direction cases)."),
        "why": ("Each weighing partitions into left-heavy/right-heavy/balanced "
                "with 1/3+1/3+1/3 weight; a ternary-split decision tree gives "
                "ceil(log3(2n)) weighings. For n=12, 3 weighings suffice."),
        "reference": "Classic puzzle; information theory (Shannon).",
    },
    {
        "keys": ["river crossing", "fox goose grain", "wolf goat cabbage", "missionaries cannibals"],
        "fact": ("River-crossing puzzles (wolf/goat/cabbage; missionaries and "
                 "cannibals) are solved as a shortest-path search over the "
                 "state space of who is on which bank, with the 'bad' "
                 "configurations excluded as forbidden states."),
        "why": ("Model each bank as a set; transitions move 1-2 items across; "
                "a forbidden set (e.g. goat-alone-with-cabbage) prunes the "
                "frontier. The classic wolf/goat/cabbage has a 7-move solution."),
        "reference": "Classic; solvable via BFS on the state graph.",
    },
    {
        "keys": ["lightbulb", "three switches", "switch and light bulb"],
        "fact": ("Three-switch/one-bulb: turn on switch 1, wait, turn it off, "
                 "turn on switch 2, then enter. The lit bulb is switch 2; the "
                 "warm-but-unlit bulb is switch 1; the cold bulb is switch 3 "
                 "(uses heat as a second observable beyond light)."),
        "why": ("Using two orthogonal observables (light on/off AND heat) gives "
                "3 distinguishable states from 2 binary measurements, mapping "
                "uniquely to 3 switches."),
        "reference": "Classic logic/observation puzzle.",
    },
    {
        "keys": ["two ropes", "rope burning", "45 minutes", "burning rope"],
        "fact": ("Two non-uniform ropes each burn in exactly 60 s; measure "
                 "45 minutes by lighting rope A at both ends and rope B at one "
                 "end, then lighting B's other end when A is consumed."),
        "why": ("A lit-at-both-ends rope burns in 30 s regardless of "
                "non-uniformity; the 30 s half of B plus the second half lit "
                "from both ends gives 15 s, totalling 45 s."),
        "reference": "Classic reasoning puzzle.",
    },
    {
        "keys": ["prisoner and hats", "prisoners and hats", "hat puzzle", "executioner hats", "prisoner hats"],
        "fact": ("N-prisoner hat puzzle (black/white, hear answers behind): the "
                 "BACK prisoner announces a parity/parity-sum that lets "
                 "everyone ahead deduce their own color by counting what they "
                 "see against what parity was signaled."),
        "why": ("A single parity bit of information cascades: prisoner i looks "
                "at all hats ahead, plus the known parity bit, and deduces "
                "their own; guaranteed N-1 of N survive, and the back one has "
                "50% chance."),
        "reference": "Classic information/logic puzzle.",
    },
]


def lookup_puzzle(text: str) -> Optional[Dict[str, Any]]:
    """Return the referenced puzzle pattern for a known archetype, else None."""
    if not text:
        return None
    t = text.lower()
    for entry in PUZZLES:
        if any(k in t for k in entry["keys"]):
            return dict(entry)  # copy, no mutation
    return None


def lookup_puzzle_combined(text: str) -> Dict[str, Any]:
    """Combined surface: {status, found, fact?, why?, reference?}."""
    e = lookup_puzzle(text)
    if not e:
        return {"status": "no_puzzle_pattern", "found": False}
    return {
        "status": "puzzle_pattern",
        "found": True,
        "fact": e["fact"],
        "why": e["why"],
        "reference": e["reference"],
    }


if __name__ == "__main__":
    for q in ["monty hall", "three switches and one bulb", "12 coins one fake",
              "wolf goat cabbage", "completely novel puzzle"]:
        print(f"{q!r:30} -> {lookup_puzzle_combined(q)}")
