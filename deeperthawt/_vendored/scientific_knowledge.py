#!/usr/bin/env python3
"""Curated scientific-knowledge lookup.

A small, referenced fact table for well-established scientific facts — the
honest form of 'explanation' this system can deliver: retrieval with a
citation, never causal/explanatory reasoning about how/why beyond the stated
fact. Unknown topics return an explicit abstention.

Scope note: This provides *referenced factual retrieval* for a curated set of
established facts. It does NOT (and cannot) explain quantum entanglement,
derive superconductivity from first principles, or generate novel science.
That boundary is deliberate.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# Each entry: keyword keys, the fact text, an optional plain 'why' restatement,
# and a reference/citation.
FACTS: List[Dict[str, Any]] = [
    {
        "keys": ["superconductiv", "zero resistance", "meissner"],
        "fact": ("Superconductivity is a phenomenon in which certain materials, "
                 "below a critical temperature, exhibit exactly zero electrical "
                 "resistance and expel magnetic fields (the Meissner effect)."),
        "why": ("Below Tc, cooper pairs of electrons condense into a single "
                "quantum state that carries current without scattering (BCS "
                "mechanism for conventional superconductors)."),
        "reference": "Onnes (1911); Bardeen, Cooper & Schrieffer (1957).",
    },
    {
        "keys": ["quantum entangle", "entanglement"],
        "fact": ("Quantum entanglement is a quantum-mechanical correlation in "
                 "which the quantum state of each particle cannot be described "
                 "independently of the others."),
        "why": ("Entangled particles share a joint wavefunction; measuring one "
                "instantly fixes the state of the other, as formalized by the "
                "Bell inequalities and their experimental violation."),
        "reference": "Bell (1964); Aspect, Dalibard & Roger (1982).",
    },
    {
        "keys": ["sky", "blue"],
        "fact": ("The sky appears blue because air molecules scatter shorter "
                 "(blue) wavelengths of sunlight more strongly than longer "
                 "(red) wavelengths — Rayleigh scattering."),
        "why": ("Rayleigh scattering intensity scales as 1/lambda^4, so "
                "short-wavelength (blue) light is scattered far more than red."),
        "reference": "Rayleigh (1871).",
    },
    {
        "keys": ["photosynthesis"],
        "fact": ("Photosynthesis is the process by which plants (and some "
                 "algae/bacteria) convert light energy, carbon dioxide, and "
                 "water into glucose and oxygen."),
        "why": ("Chlorophyll absorbs light; the light reactions produce ATP and "
                "NADPH; the Calvin cycle fixes CO2 into glucose."),
        "reference": "Calvin, Benson, Bassham (1950s); standard biochemistry.",
    },
    {
        "keys": ["crispr", "cas9", "gene edit"],
        "fact": ("CRISPR-Cas9 is a gene-editing system that uses a guide RNA to "
                 "target a specific DNA sequence, where the Cas9 nuclease makes "
                 "a double-strand break."),
        "why": ("The guide RNA base-pairs with target DNA; Cas9 cuts it; "
                "cellular repair machinery then edits the sequence."),
        "reference": "Jinek et al. (2012); Doudna & Charpentier (Nobel 2020).",
    },
    {
        "keys": ["water", "h2o", "chemical formula of water", "formula for water"],
        "fact": ("Water has the chemical formula H2O: two hydrogen atoms bonded "
                 "to one oxygen atom."),
        "why": ("Water's bent geometry (104.5 degree bond angle) makes it polar "
                "and an excellent solvent."),
        "reference": "Standard chemistry.",
    },
    {
        "keys": ["gravity", "gravitational attraction", "newton law of gravitation"],
        "fact": ("Gravity is the mutual attractive force between masses, "
                 "described by Newton's law F = G*m1*m2/r^2."),
        "why": ("G is the gravitational constant (6.674e-11 N m2/kg2); the force "
                "falls off as the inverse square of separation."),
        "reference": "Newton, Principia (1687).",
    },
    {
        "keys": ["radioactive decay", "half-life", "half life"],
        "fact": ("Radioactive decay is the spontaneous transformation of an "
                 "unstable atomic nucleus, emitting radiation, at a rate "
                 "characterized by the half-life (time for half to decay)."),
        "why": "Decay follows an exponential law N(t) = N0 * 2^(-t/T).",
        "reference": "Rutherford; standard nuclear physics.",
    },
    {
        "keys": ["evolution", "natural selection", "darwin"],
        "fact": ("Evolution by natural selection is the change in heritable "
                 "traits of a population over generations, driven by "
                 "differential survival and reproduction (fitness)."),
        "why": "Variation + heritability + differential reproduction produce adaptation.",
        "reference": "Darwin, Origin of Species (1859).",
    },
    {
        "keys": ["atom", "plum pudding", "nucleus", "electron cloud"],
        "fact": ("An atom consists of a dense, positively charged nucleus "
                 "(protons and neutrons) surrounded by a cloud of negatively "
                 "charged electrons."),
        "why": ("Protons give the atomic number; electrons occupy quantum "
                "shells that govern chemical behavior."),
        "reference": "Rutherford (1911); Bohr (1913).",
    },
    # -- physical constants used by the deterministic register/lab (hybrid-agi
    #    Maxwell-Lorentz FDTD). Values are the SAME constants the lab hard-codes
    #    (maxwell_lorentz_lab.py) and are externally locked against CODATA in
    #    fixtures_external/1d_analytic_references.py. Adding them makes the
    #    reasoning/knowledge surface agree with the lab's own physics. --
    {
        "keys": ["speed of light", "speed light", "299792458", "c0", "velocity of light", "light speed"],
        "fact": ("The speed of light in vacuum c0 = 299,792,458 m/s exactly (the "
                 "metre is defined so that c0 is exact). This is the speed at "
                 "which electromagnetic waves propagate in vacuum."),
        "why": ("c0 is a defining physical constant (SI); in the register/lab FDTD "
                "it sets the electromagnetic wave-propagation speed and the "
                "Courant stability limit dt <= dz/c0."),
        "reference": "SI definition of the metre (1983); CODATA 2018 (exact).",
    },
    {
        "keys": ["vacuum impedance", "free space impedance", "z0", "impedance of vacuum", "wave impedance"],
        "fact": ("The vacuum (free-space) impedance Z0 = 376.730313668 Ohm exactly, "
                 "given by Z0 = mu0*c0 = sqrt(mu0/eps0). It is the ratio of "
                 "electric to magnetic field amplitude for a plane wave in vacuum."),
        "why": ("Z0 = sqrt(mu0/eps0) follows from the wave impedance of a "
                "transverse electromagnetic (TEM) wave; with mu0=4*pi*1e-7 and "
                "c0 exact it equals 376.730313668 Ohm exactly."),
        "reference": "CODATA 2018 (exact via mu0 and c0).",
    },
    {
        "keys": ["vacuum permittivity", "electric constant", "eps0", "epsilon 0", "epsilon0", "permittivity of free space"],
        "fact": ("The vacuum permittivity eps0 = 8.8541878128e-12 F/m (CODATA 2018), "
                 "the constant relating electric field and displacement in vacuum "
                 "(Gauss's law: div D = rho, D = eps0*E)."),
        "why": ("eps0 enters Maxwell's equations and the Lorentz force; in the lab "
                "it sets the displacement-current term and how charge density "
                "produces electric field."),
        "reference": "CODATA 2018 (with uncertainty 0.000000005 e-12 F/m).",
    },
    {
        "keys": ["vacuum permeability", "magnetic constant", "mu0", "mu 0", "permeability of free space"],
        "fact": ("The vacuum permeability mu0 = 1.25663706212e-6 H/m (CODATA 2018). "
                 "It relates magnetic field and magnetizing field in vacuum "
                 "(Ampere's law), and gives the free-space impedance via Z0 = mu0*c0."),
        "why": ("Historically mu0 was defined as exactly 4*pi*1e-7 H/m; after the "
                "2019 SI redefinition it is a measured value with uncertainty. "
                "c0*mu0*eps0 = 1 in vacuum."),
        "reference": "CODATA 2018.", 
    },
    {
        "keys": ["electromagnetic wave", "em wave", "light wave", "propagates at c", "speed of em"],
        "fact": ("An electromagnetic wave in vacuum propagates at the speed of "
                 "light c0 = 299,792,458 m/s, with mutually perpendicular electric "
                 "(E) and magnetic (B) fields transverse to the direction of travel."),
        "why": ("EM waves follow from Maxwell's equations; in a TEM wave the "
                "electric and magnetic field magnitudes satisfy E/B = c0 and "
                "Hn = Z0*By (the lab's normalized magnetic field is Hn = Z0*By)."),
        "reference": "Maxwell (1865); the register/lab TEM gate (Hn = -Ez normalized).",
    },
    {
        "keys": ["lorentz force", "force on charge", "q e + v cross b", "lorentz"],
        "fact": ("The Lorentz force is the force on a point charge q with velocity v "
                 "in electric field E and magnetic field B: F = q*(E + v x B)."),
        "why": ("This is the mechanical force Maxwell-Lorentz dynamics uses to "
                "push charged particles through the lab's electromagnetic field; "
                "for v parallel to B the v x B term vanishes (the lab gate tests "
                "pure-E and pure-B cases to 0.0% against the analytic formula)."),
        "reference": "Hendrik Lorentz (1892); the register/lab E4 gate (Lorentz 0.0%).",
    },
]


def lookup_science_fact(text: str) -> Optional[Dict[str, Any]]:
    """Return the referenced fact for a known science topic, else None (abstain)."""
    if not text:
        return None
    t = text.lower()
    for entry in FACTS:
        if any(k in t for k in entry["keys"]):
            return dict(entry)  # copy, no mutation
    return None


def lookup_science_fact_combined(text: str) -> Dict[str, Any]:
    """Grounded-oracle-friendly lookup result."""
    fact = lookup_science_fact(text)
    if fact is None:
        return {"status": "no_science_fact", "found": False}
    return {
        "status": "science_fact",
        "found": True,
        "fact": fact["fact"],
        "why": fact.get("why", ""),
        "reference": fact["reference"],
        "note": "Referenced factual retrieval; NOT causal/derived explanation.",
    }


# quick self-test
if __name__ == "__main__":
    for q in [
        "What causes superconductivity?",
        "Explain quantum entanglement",
        "Why does the sky appear blue?",
        "What is the mechanism of CRISPR-Cas9?",
        "Describe photosynthesis",
        "What is the chemical formula for water?",
        "How does gravity work?",
        "What is the capital of France?",
    ]:
        r = lookup_science_fact_combined(q)
        print(f"  [{r['status']:14}] {q[:42]:44} ref={(r.get('reference') or '')[:38]}")
