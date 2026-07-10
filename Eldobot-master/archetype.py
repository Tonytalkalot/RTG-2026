"""Canonical BBGM archetype namer.

A faithful Python port of the community "BBGM Archetype Calculator v2.0"
spreadsheet. Given a player's raw BBGM ratings + position, it produces the
canonical archetype string, e.g.::

    "Athletic Two-Way Shooting Point Forward"
    "Oversized Powerful Defensive Paint Center"
    "Prospect Guard"

The name is built by picking the best-matching descriptor from five ordered
categories and concatenating them:

    [Height] [Athleticism] [IQ] [Scoring] [Skill]

Each non-scoring category scores every candidate row by

    1 - mean(|rating - anchor|) / 100

and takes the highest (ties → first row, matching Excel's MATCH). Scoring is
distribution-based with positional/threshold gates (see ``_scoring`` below).

**League-relative mode.** When a ``dim_stats`` baseline is supplied (the same
per-rating mean/std pool ``player_builds`` already builds for the percentile
caption), the ability dimensions — Athleticism, IQ, Skill, and the Scoring
*gates* — are first mapped onto a league-percentile scale (0-100 via the normal
CDF of each rating's z-score) before being matched against the 10/50/90 anchors.
So "50" means league-median, "90" means roughly top-30%, "10" bottom-30%: the
archetype reflects how a player ranks among peers rather than absolute rating
values, which adapts to the league's power level. Without ``dim_stats`` the
matcher falls back to the spreadsheet's original absolute behavior.

Two things stay absolute by design: the Scoring *style* (the ins/dnk/2pt/3pt
mix, which is the player's intrinsic shot profile) and Height (which maps to
real inches and shouldn't inflate with league quality).

Note on tiers: the shipped spreadsheet's Prospect/Veteran prefix never fires
(its UI formula reads an empty column) and even its intended concatenation drops
spaces. This port implements the clearly-intended behavior — a sub-50-overall
under-24 becomes "Prospect <Group>", a sub-50 over-34 gets a "Veteran" prefix —
with proper spacing.
"""

import math

# Relative scoring-gate bar: on the league-percentile scale, a rating must reach
# the 60th percentile to count toward a scoring descriptor. In absolute mode
# (no dim_stats) this is just the spreadsheet's raw >= 60 threshold.
_SCORING_GATE = 60

# --- Athleticism: (name, STR, SPD, JMP, END). Order matters for tie-breaking. ---
_ATHLETICISM = [
    (None,            50, 50, 50, 50),
    (None,            50, 50, 50, 90),
    (None,            50, 50, 90, 50),
    (None,            50, 50, 90, 90),
    ('Quick',         50, 90, 50, 50),
    ('Quick',         50, 90, 50, 90),
    ('Athletic',      50, 90, 90, 50),
    ('Athletic',      50, 90, 90, 90),
    ('Physical',      90, 50, 50, 50),
    ('Physical',      90, 50, 50, 90),
    ('Powerful',      90, 50, 90, 50),
    ('Powerful',      90, 50, 90, 90),
    ('Explosive',     90, 90, 50, 50),
    ('Explosive',     90, 90, 50, 90),
    ('Freak Athlete', 90, 90, 90, 50),
    ('Freak Athlete', 90, 90, 90, 90),
    (None,            50, 50, 50, 10),
    ('Below the Rim', 50, 50, 10, 50),
    ('Below the Rim', 50, 50, 10, 10),
    ('Slow',          50, 10, 50, 50),
    ('Slow',          50, 10, 50, 10),
    ('Sluggish',      50, 10, 10, 50),
    ('Sluggish',      50, 10, 10, 10),
    ('Soft',          10, 50, 50, 50),
    ('Soft',          10, 50, 50, 10),
    ('Fragile',       10, 50, 10, 50),
    ('Fragile',       10, 50, 10, 10),
    ('Unathletic',    10, 10, 50, 50),
    ('Unathletic',    10, 10, 50, 10),
    ('Unathletic',    10, 10, 10, 50),
    ('Out of Shape',  10, 10, 10, 10),
]

# --- IQ: (name, OIQ, DIQ) ---
_IQ = [
    ('Raw',                10, 10),
    ('Limited Offense',    10, 50),
    ('Defense Specialist', 10, 90),
    ('Limited Defense',    50, 10),
    (None,                 50, 50),
    ('Defensive',          50, 90),
    ('Offense Specialist', 90, 10),
    ('Offensive',          90, 50),
    ('Two-Way',            90, 90),
]

# --- Height: (name, position, anchor). Only rows matching the player's pos. ---
_HEIGHT = [
    (None,         'PG', 30),
    ('Oversized',  'PG', 50),
    (None,         'G',  30),
    ('Oversized',  'G',  50),
    (None,         'SG', 30),
    (None,         'SG', 50),
    ('Undersized', 'GF', 30),
    (None,         'GF', 50),
    ('Undersized', 'SF', 30),
    (None,         'SF', 50),
    ('Oversized',  'SF', 70),
    (None,         'F',  50),
    ('Oversized',  'F',  70),
    (None,         'PF', 50),
    (None,         'PF', 70),
    ('Undersized', 'FC', 50),
    (None,         'FC', 70),
    ('Undersized', 'C',  50),
    (None,         'C',  70),
]

# --- Scoring: (name, w_ins, w_dnk, w_2pt, w_3pt, gate). Gate(ratings, pos) -> bool. ---
# Weights are target shares of (ins, dnk, 2pt, 3pt) scoring; match score is
# 1 - sum(|share - weight|) / 2. A row only competes when its gate passes.
# Gates receive ratings already on the gating scale (league-percentile when a
# baseline is supplied, raw otherwise) and compare against _SCORING_GATE.
def _g_three_level(ins, dnk, fg, tp, pos):
    return ins >= _SCORING_GATE and dnk >= _SCORING_GATE and fg >= _SCORING_GATE and tp >= _SCORING_GATE
def _g_three_point(ins, dnk, fg, tp, pos):
    return tp >= _SCORING_GATE
def _g_mid_range(ins, dnk, fg, tp, pos):
    return fg >= _SCORING_GATE
def _g_shooting(ins, dnk, fg, tp, pos):
    return fg >= _SCORING_GATE and tp >= _SCORING_GATE
def _g_slashing(ins, dnk, fg, tp, pos):
    return dnk >= _SCORING_GATE and pos not in ('PF', 'FC', 'C')
def _g_rim(ins, dnk, fg, tp, pos):
    return dnk >= _SCORING_GATE and pos in ('PF', 'FC', 'C')
def _g_paint(ins, dnk, fg, tp, pos):
    return ins >= _SCORING_GATE
def _g_inside_out(ins, dnk, fg, tp, pos):
    return ins >= _SCORING_GATE and dnk >= _SCORING_GATE and tp >= _SCORING_GATE
def _g_inside_arc(ins, dnk, fg, tp, pos):
    return ins >= _SCORING_GATE and dnk >= _SCORING_GATE and fg >= _SCORING_GATE

_SCORING = [
    ('Three-Level',    0.25, 0.25, 0.25, 0.25, _g_three_level),
    ('Three Point',    0.20, 0.20, 0.20, 0.40, _g_three_point),
    ('Mid-Range',      0.20, 0.20, 0.40, 0.20, _g_mid_range),
    ('Shooting',       0.17, 0.17, 0.33, 0.33, _g_shooting),
    ('Slashing',       0.20, 0.40, 0.20, 0.20, _g_slashing),
    ('Rim',            0.20, 0.40, 0.20, 0.20, _g_rim),
    ('Paint',          0.40, 0.20, 0.20, 0.20, _g_paint),
    ('Inside Out',     0.29, 0.29, 0.13, 0.29, _g_inside_out),
    ('Inside the Arc', 0.29, 0.29, 0.29, 0.13, _g_inside_arc),
]

# --- Prospect position groups ---
_PROSPECT_GROUP = {
    'PG': 'Guard', 'G': 'Guard', 'SG': 'Guard',
    'GF': 'Wing',
    'SF': 'Forward', 'F': 'Forward', 'PF': 'Forward',
    'FC': 'Big',
    'C': 'Center',
}

_SKILL = {
    'PG': {
        (10, 10, 10): 'Off-Ball Guard', (10, 10, 50): 'Off-Ball Guard', (10, 10, 90): 'Hustle Guard',
        (10, 50, 10): 'Point Guard', (10, 50, 50): 'Point Guard', (10, 50, 90): 'Point Guard',
        (10, 90, 10): 'Distributor Guard', (10, 90, 50): 'Distributor Guard', (10, 90, 90): 'Distributor Guard',
        (50, 10, 10): 'Point Guard', (50, 10, 50): 'Point Guard', (50, 10, 90): 'Point Guard',
        (50, 50, 10): 'Point Guard', (50, 50, 50): 'Point Guard', (50, 50, 90): 'Point Guard',
        (50, 90, 10): 'Facilitator Guard', (50, 90, 50): 'Facilitator Guard', (50, 90, 90): 'Facilitator Guard',
        (90, 10, 10): 'Shot Creator Guard', (90, 10, 50): 'Shot Creator Guard', (90, 10, 90): 'Shot Creator Guard',
        (90, 50, 10): 'Shot Creator Guard', (90, 50, 50): 'Shot Creator Guard', (90, 50, 90): 'Shot Creator Guard',
        (90, 90, 10): 'Playmaker', (90, 90, 50): 'Playmaker', (90, 90, 90): 'Playmaker',
    },
    'G': {
        (10, 10, 10): 'Off-Ball Guard', (10, 10, 50): 'Off-Ball Guard', (10, 10, 90): 'Hustle Guard',
        (10, 50, 10): 'Combo Guard', (10, 50, 50): 'Combo Guard', (10, 50, 90): 'Combo Guard',
        (10, 90, 10): 'Distributor Guard', (10, 90, 50): 'Distributor Guard', (10, 90, 90): 'Distributor Guard',
        (50, 10, 10): 'Combo Guard', (50, 10, 50): 'Combo Guard', (50, 10, 90): 'Combo Guard',
        (50, 50, 10): 'Combo Guard', (50, 50, 50): 'Combo Guard', (50, 50, 90): 'Combo Guard',
        (50, 90, 10): 'Facilitator Guard', (50, 90, 50): 'Facilitator Guard', (50, 90, 90): 'Facilitator Guard',
        (90, 10, 10): 'Shot Creator Guard', (90, 10, 50): 'Shot Creator Guard', (90, 10, 90): 'Shot Creator Guard',
        (90, 50, 10): 'Shot Creator Guard', (90, 50, 50): 'Shot Creator Guard', (90, 50, 90): 'Shot Creator Guard',
        (90, 90, 10): 'Playmaker', (90, 90, 50): 'Playmaker', (90, 90, 90): 'Playmaker',
    },
    'SG': {
        (10, 10, 10): 'Off-Ball Guard', (10, 10, 50): 'Off-Ball Guard', (10, 10, 90): 'Hustle Guard',
        (10, 50, 10): 'Shooting Guard', (10, 50, 50): 'Shooting Guard', (10, 50, 90): 'Shooting Guard',
        (10, 90, 10): 'Distributor Guard', (10, 90, 50): 'Distributor Guard', (10, 90, 90): 'Distributor Guard',
        (50, 10, 10): 'Shooting Guard', (50, 10, 50): 'Shooting Guard', (50, 10, 90): 'Shooting Guard',
        (50, 50, 10): 'Shooting Guard', (50, 50, 50): 'Shooting Guard', (50, 50, 90): 'Shooting Guard',
        (50, 90, 10): 'Facilitator Guard', (50, 90, 50): 'Facilitator Guard', (50, 90, 90): 'Facilitator Guard',
        (90, 10, 10): 'Shot Creator Guard', (90, 10, 50): 'Shot Creator Guard', (90, 10, 90): 'Shot Creator Guard',
        (90, 50, 10): 'Shot Creator Guard', (90, 50, 50): 'Shot Creator Guard', (90, 50, 90): 'Shot Creator Guard',
        (90, 90, 10): 'Playmaker', (90, 90, 50): 'Playmaker', (90, 90, 90): 'Playmaker',
    },
    'GF': {
        (10, 10, 10): 'Off-Ball Wing', (10, 10, 50): 'Off-Ball Wing', (10, 10, 90): 'Hustle Wing',
        (10, 50, 10): 'Wing', (10, 50, 50): 'Wing', (10, 50, 90): 'Wing',
        (10, 90, 10): 'Distributor Wing', (10, 90, 50): 'Distributor Wing', (10, 90, 90): 'Distributor Wing',
        (50, 10, 10): 'Wing', (50, 10, 50): 'Wing', (50, 10, 90): 'Wing',
        (50, 50, 10): 'Wing', (50, 50, 50): 'Wing', (50, 50, 90): 'Wing',
        (50, 90, 10): 'Facilitator Wing', (50, 90, 50): 'Facilitator Wing', (50, 90, 90): 'Facilitator Wing',
        (90, 10, 10): 'Shot Creator Wing', (90, 10, 50): 'Shot Creator Wing', (90, 10, 90): 'Shot Creator Wing',
        (90, 50, 10): 'Shot Creator Wing', (90, 50, 50): 'Shot Creator Wing', (90, 50, 90): 'Shot Creator Wing',
        (90, 90, 10): 'Point Wing', (90, 90, 50): 'Point Wing', (90, 90, 90): 'Point Wing',
    },
    'SF': {
        (10, 10, 10): 'Off-Ball Forward', (10, 10, 50): 'Off-Ball Forward', (10, 10, 90): 'Hustle Forward',
        (10, 50, 10): 'Small Forward', (10, 50, 50): 'Small Forward', (10, 50, 90): 'Small Forward',
        (10, 90, 10): 'Distributor Forward', (10, 90, 50): 'Distributor Forward', (10, 90, 90): 'Distributor Forward',
        (50, 10, 10): 'Small Forward', (50, 10, 50): 'Small Forward', (50, 10, 90): 'Small Forward',
        (50, 50, 10): 'Small Forward', (50, 50, 50): 'Small Forward', (50, 50, 90): 'Small Forward',
        (50, 90, 10): 'Facilitator Forward', (50, 90, 50): 'Facilitator Forward', (50, 90, 90): 'Facilitator Forward',
        (90, 10, 10): 'Shot Creator Forward', (90, 10, 50): 'Shot Creator Forward', (90, 10, 90): 'Shot Creator Forward',
        (90, 50, 10): 'Shot Creator Forward', (90, 50, 50): 'Shot Creator Forward', (90, 50, 90): 'Shot Creator Forward',
        (90, 90, 10): 'Point Forward', (90, 90, 50): 'Point Forward', (90, 90, 90): 'Point Forward',
    },
    'F': {
        (10, 10, 10): 'Off-Ball Forward', (10, 10, 50): 'Off-Ball Forward', (10, 10, 90): 'Rebounding Forward',
        (10, 50, 10): 'Forward', (10, 50, 50): 'Forward', (10, 50, 90): 'Forward',
        (10, 90, 10): 'Distributor Forward', (10, 90, 50): 'Distributor Forward', (10, 90, 90): 'Distributor Forward',
        (50, 10, 10): 'Forward', (50, 10, 50): 'Forward', (50, 10, 90): 'Forward',
        (50, 50, 10): 'Forward', (50, 50, 50): 'Forward', (50, 50, 90): 'Forward',
        (50, 90, 10): 'Facilitator Forward', (50, 90, 50): 'Facilitator Forward', (50, 90, 90): 'Facilitator Forward',
        (90, 10, 10): 'Shot Creator Forward', (90, 10, 50): 'Shot Creator Forward', (90, 10, 90): 'Shot Creator Forward',
        (90, 50, 10): 'Shot Creator Forward', (90, 50, 50): 'Shot Creator Forward', (90, 50, 90): 'Shot Creator Forward',
        (90, 90, 10): 'Point Forward', (90, 90, 50): 'Point Forward', (90, 90, 90): 'Point Forward',
    },
    'PF': {
        (10, 10, 10): 'Off-Ball Forward', (10, 10, 50): 'Off-Ball Forward', (10, 10, 90): 'Rebounding Forward',
        (10, 50, 10): 'Power Forward', (10, 50, 50): 'Power Forward', (10, 50, 90): 'Power Forward',
        (10, 90, 10): 'Distributor Forward', (10, 90, 50): 'Distributor Forward', (10, 90, 90): 'Distributor Forward',
        (50, 10, 10): 'Power Forward', (50, 10, 50): 'Power Forward', (50, 10, 90): 'Power Forward',
        (50, 50, 10): 'Power Forward', (50, 50, 50): 'Power Forward', (50, 50, 90): 'Power Forward',
        (50, 90, 10): 'Facilitator Forward', (50, 90, 50): 'Facilitator Forward', (50, 90, 90): 'Facilitator Forward',
        (90, 10, 10): 'Shot Creator Forward', (90, 10, 50): 'Shot Creator Forward', (90, 10, 90): 'Shot Creator Forward',
        (90, 50, 10): 'Shot Creator Forward', (90, 50, 50): 'Shot Creator Forward', (90, 50, 90): 'Shot Creator Forward',
        (90, 90, 10): 'Point Forward', (90, 90, 50): 'Point Forward', (90, 90, 90): 'Point Forward',
    },
    'FC': {
        (10, 10, 10): 'Off-Ball Big', (10, 10, 50): 'Off-Ball Big', (10, 10, 90): 'Rebounding Big',
        (10, 50, 10): 'Big Man', (10, 50, 50): 'Big Man', (10, 50, 90): 'Big Man',
        (10, 90, 10): 'Distributor Big', (10, 90, 50): 'Distributor Big', (10, 90, 90): 'Distributor Big',
        (50, 10, 10): 'Big Man', (50, 10, 50): 'Big Man', (50, 10, 90): 'Rebounding Big',
        (50, 50, 10): 'Big Man', (50, 50, 50): 'Big Man', (50, 50, 90): 'Big Man',
        (50, 90, 10): 'Facilitator Big', (50, 90, 50): 'Facilitator Big', (50, 90, 90): 'Facilitator Big',
        (90, 10, 10): 'Face Up Big', (90, 10, 50): 'Face Up Big', (90, 10, 90): 'Face Up Big',
        (90, 50, 10): 'Face Up Big', (90, 50, 50): 'Face Up Big', (90, 50, 90): 'Face Up Big',
        (90, 90, 10): 'Point Center', (90, 90, 50): 'Point Center', (90, 90, 90): 'Point Center',
    },
    'C': {
        (10, 10, 10): 'Off-Ball Center', (10, 10, 50): 'Off-Ball Center', (10, 10, 90): 'Rebounding Center',
        (10, 50, 10): 'Center', (10, 50, 50): 'Center', (10, 50, 90): 'Center',
        (10, 90, 10): 'Distributor Center', (10, 90, 50): 'Distributor Center', (10, 90, 90): 'Distributor Center',
        (50, 10, 10): 'Center', (50, 10, 50): 'Center', (50, 10, 90): 'Center',
        (50, 50, 10): 'Center', (50, 50, 50): 'Center', (50, 50, 90): 'Center',
        (50, 90, 10): 'Facilitator Center', (50, 90, 50): 'Facilitator Center', (50, 90, 90): 'Facilitator Center',
        (90, 10, 10): 'Face Up Center', (90, 10, 50): 'Face Up Center', (90, 10, 90): 'Face Up Center',
        (90, 50, 10): 'Face Up Center', (90, 50, 50): 'Face Up Center', (90, 50, 90): 'Face Up Center',
        (90, 90, 10): 'Point Center', (90, 90, 50): 'Point Center', (90, 90, 90): 'Point Center',
    },
}

# Anchor order within a position's skill table, preserved for tie-breaking
# (Excel MATCH returns the first occurrence of the max). dict insertion order
# above mirrors the spreadsheet's row order exactly.
_SKILL_ORDER = {pos: list(table.keys()) for pos, table in _SKILL.items()}


def _best(candidates, ratings, anchor_idx):
    """Pick the descriptor whose anchors best match `ratings` (mean abs diff).

    `candidates` is an ordered list of rows; `anchor_idx` slices each row's
    anchor numbers. Returns the winning row's name (element 0). Ties go to the
    first row, matching Excel's MATCH(MAX(...)).
    """
    best_name = ''
    best_score = None
    for row in candidates:
        anchors = row[anchor_idx]
        n = len(anchors)
        diff = sum(abs(r - a) for r, a in zip(ratings, anchors))
        score = 1 - diff / (100 * n)
        if best_score is None or score > best_score:
            best_score = score
            best_name = row[0] or ''
    return best_name


def _height(pos, hgt):
    rows = [r for r in _HEIGHT if r[1] == pos]
    if not rows:
        return ''
    best_name, best_score = '', None
    for name, _p, anchor in rows:
        score = 1 - abs(hgt - anchor) / 100
        if best_score is None or score > best_score:
            best_score, best_name = score, name or ''
    return best_name


def _scoring(ins, dnk, fg, tp, gate_ins, gate_dnk, gate_fg, gate_tp, pos):
    """Scoring descriptor + distinctiveness, as (word, dist). Shares (style) come
    from the raw ins/dnk/fg/tp; the gates that decide which descriptors a player
    qualifies for use the gate_* values (league-percentile in relative mode, else
    equal to raw). `dist` (0-1+) measures how lopsided the scoring profile is —
    used to rank descriptors when labels are trimmed."""
    total = ins + dnk + fg + tp
    if total <= 0:
        return ('', 0.0)
    shares = (ins / total, dnk / total, fg / total, tp / total)
    best_name, best_score = '', 0.0
    for name, wi, wd, w2, w3, gate in _SCORING:
        if not gate(gate_ins, gate_dnk, gate_fg, gate_tp, pos):
            continue
        weights = (wi, wd, w2, w3)
        diff = sum(abs(s - w) for s, w in zip(shares, weights))
        score = 1 - diff / 2
        if score > best_score:
            best_score, best_name = score, name
    # Spreadsheet's row-11 fallback: when nothing gated in, the descriptor is
    # blank (no scoring word).
    if not best_name:
        return ('', 0.0)
    dist = max(abs(s - 0.25) for s in shares) / 0.4
    return (best_name, dist)


def _skill(pos, drb, pss, reb):
    order = _SKILL_ORDER.get(pos)
    if not order:
        return ''
    table = _SKILL[pos]
    best_key, best_score = None, None
    for key in order:
        diff = abs(drb - key[0]) + abs(pss - key[1]) + abs(reb - key[2])
        score = 1 - diff / 300
        if best_score is None or score > best_score:
            best_score, best_key = score, key
    return table[best_key]


def _dev(values):
    """Distinctiveness of an ability descriptor: how far the player sits from the
    neutral 50 anchor, averaged across the category's ratings. ~1.0 means a
    descriptor anchored at the 10/90 extreme; ~0 means league-average."""
    if not values:
        return 0.0
    return (sum(abs(v - 50) for v in values) / len(values)) / 40.0


def _height_dist(pos, hgt):
    """Distinctiveness of a height descriptor: how far the player's height sits
    from the position's normal anchor (the unnamed row in _HEIGHT)."""
    normal = None
    for name, p, anchor in _HEIGHT:
        if p == pos and not name:
            normal = anchor
            break
    if normal is None:
        normal = 50
    return abs(hgt - normal) / 20.0


def _rel_value(raw, dim_stats, key):
    """Map a raw rating onto the league-percentile scale (0-100) via the normal
    CDF of its z-score, so 50 = league median, ~90 = top ~10%, ~10 = bottom
    ~10%. Returns the raw value unchanged when no baseline is available."""
    if not dim_stats or key not in dim_stats:
        return raw
    mean, std = dim_stats[key]
    if not std or std <= 0:
        return raw
    z = (raw - mean) / std
    return 100.0 * 0.5 * (1.0 + math.erf(z / math.sqrt(2)))


def _tier(ovr, age):
    """Return 'Prospect', 'Veteran', or '' per the spreadsheet's Tier_String."""
    if ovr is not None and ovr < 50:
        if age is not None and age < 24:
            return 'Prospect'
        if age is not None and age > 34:
            return 'Veteran'
    return ''


def archetype(ratings, position, ovr=None, age=None, dim_stats=None,
              max_adjectives=None):
    """Return the canonical BBGM archetype string for a player.

    `ratings` is a BBGM ratings dict (keys: hgt, stre, spd, jmp, endu, ins, dnk,
    ft, fg, tp, oiq, diq, drb, pss, reb). `position` is the BBGM pos string
    (PG/SG/SF/PF/C/G/GF/F/FC). `ovr`/`age` drive the Prospect/Veteran tier; if
    omitted, `ovr` falls back to ratings['ovr'] and tiers requiring age are
    skipped.

    `dim_stats` is an optional per-rating {key: (mean, std)} league baseline
    (as produced by player_builds._league_dim_stats). When supplied, the ability
    dimensions (Athleticism, IQ, Skill) and the Scoring gates are matched on the
    league-percentile scale instead of raw ratings — see the module docstring.
    Scoring style and Height remain absolute either way.

    `max_adjectives` caps how many descriptors precede the skill noun: the skill
    noun (the identity) is always kept, and only the N most distinctive adjectives
    (Height/Athleticism/IQ/Scoring — whichever the player deviates from average on
    most) survive; the rest are dropped to keep labels short. None = keep all
    (faithful to the spreadsheet). The Veteran tier prefix is always kept and does
    not count toward the cap.

    Returns '' if the position is unknown or ratings are missing.
    """
    if not ratings or not position:
        return ''
    pos = position
    if pos not in _SKILL:
        return ''
    if ovr is None:
        ovr = ratings.get('ovr')

    g = ratings.get
    tier = _tier(ovr, age)
    if tier == 'Prospect':
        return ('Prospect ' + _PROSPECT_GROUP.get(pos, '')).strip()

    def rel(key):
        return _rel_value(g(key, 0), dim_stats, key)

    skill = _skill(pos, rel('drb'), rel('pss'), rel('reb'))  # noun — always kept

    # Adjective candidates as (canonical_order, word, distinctiveness). Only
    # non-blank descriptors compete; blanks contribute nothing.
    hgt = g('hgt', 0)  # absolute — physical measurable, not league-relative
    rel_athl = (rel('stre'), rel('spd'), rel('jmp'), rel('endu'))
    rel_iq = (rel('oiq'), rel('diq'))
    scoring_word, scoring_dist = _scoring(
        g('ins', 0), g('dnk', 0), g('fg', 0), g('tp', 0),
        rel('ins'), rel('dnk'), rel('fg'), rel('tp'), pos)

    adjectives = []
    h_word = _height(pos, hgt)
    if h_word:
        adjectives.append((0, h_word, _height_dist(pos, hgt)))
    a_word = _best(_ATHLETICISM, rel_athl, slice(1, 5))
    if a_word:
        adjectives.append((1, a_word, _dev(rel_athl)))
    q_word = _best(_IQ, rel_iq, slice(1, 3))
    if q_word:
        adjectives.append((2, q_word, _dev(rel_iq)))
    if scoring_word:
        adjectives.append((3, scoring_word, scoring_dist))

    if max_adjectives is not None and len(adjectives) > max_adjectives:
        adjectives = sorted(adjectives, key=lambda x: -x[2])[:max_adjectives]
    adjectives.sort(key=lambda x: x[0])  # restore canonical order

    parts = [tier] + [w for _, w, _ in adjectives] + [skill]
    return ' '.join(p for p in parts if p).strip()
