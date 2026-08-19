"""Canonical FBGM archetype namer.

A faithful Python port of the community "FBGM Archetype Calculator v2.0"
spreadsheet. Given a player's raw FBGM ratings + position, it produces the
canonical archetype string, e.g.::

    "Athletic Deep Threat"
    "Oversized Powerful Run Stopper"
    "Prospect Scrambler"

The name is built by picking the best-matching descriptor from five ordered
categories and concatenating them:

    [Height] [Athleticism] [Scoring] [Skill]

Each non-scoring category scores every candidate row by

    1 - mean(|rating - anchor|) / 100

and takes the highest (ties → first row, matching Excel's MATCH). Scoring is
distribution-based with positional/threshold gates (see ``_scoring`` below).

**League-relative mode.** When a ``dim_stats`` baseline is supplied (the same
per-rating mean/std pool ``player_builds`` already builds for the percentile
caption), the ability dimensions — Athleticism, Skill, and the Scoring
*gates* — are first mapped onto a league-percentile scale (0-100 via the normal
CDF of each rating's z-score) before being matched against the 10/50/90 anchors.
So "50" means league-median, "90" means roughly top-30%, "10" bottom-30%: the
archetype reflects how a player ranks among peers rather than absolute rating
values, which adapts to the league's power level. Without ``dim_stats`` the
matcher falls back to the spreadsheet's original absolute behavior.

Two things stay absolute by design: the Scoring *style* (the  BSc, Elu, RtR, Hnd, Tck, PRs, RnS, PCv, PBk, RBk, ThV, ThP, ThA, KPw, KAc, PPw, PAc
mix, which is the player's intrinsic skill set) and Height (which maps to
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

# --- Athleticism: (name, STR, SPD, END). Order matters for tie-breaking. ---
_ATHLETICISM = [
    (None,            50, 50, 50),
    (None,            50, 50, 90),
    (None,            50, 50, 90),
    (None,            50, 50, 90),
    ('Quick',         50, 90, 50),
    ('Quick',         50, 90, 90),
    ('Athletic',      50, 90, 90),
    ('Athletic',      90, 90, 90),
    ('Physical',      90, 50, 50),
    ('Physical',      90, 50, 90),
    ('Powerful',      90, 50, 90),
    ('Powerful',      90, 50, 90),
    ('Explosive',     90, 90, 50),
    ('Explosive',     90, 90, 50),
    ('Freak Athlete', 90, 90, 90),
    ('Freak Athlete', 90, 90, 90),
    (None,            50, 50, 50),
    ('Below the Rim', 50, 50, 10),
    ('Below the Rim', 50, 50, 10),
    ('Slow',          50, 10, 50),
    ('Slow',          50, 10, 10),
    ('Sluggish',      50, 10, 50),
    ('Sluggish',      50, 10, 10),
    ('Soft',          10, 50, 50),
    ('Soft',          10, 50, 10),
    ('Fragile',       10, 50, 10),
    ('Fragile',       10, 50, 10),
    ('Unathletic',    10, 10, 50),
    ('Unathletic',    10, 10, 50),
    ('Unathletic',    10, 10, 10),
    ('Out of Shape',  10, 10, 10),
]

# --- Height: (name, position, anchor). Only rows matching the player's pos. ---
_HEIGHT = [
    (None,         'QB', 75,74,73),
    ('Undersized', 'QB', 72,71,70,69,68),
    ('Big',        'QB', 76,77,78,79,80),
    (None,         'RB', 70,71,72),
    ('Huge',       'RB', 72,73,74,75),
    ('Undersized', 'RB', 69,68,67,66),
    ('Lanky',      'WR', 75,76,77,78,79),
    ('Undersized', 'WR', 71,70,69,68,67),
    (None,         'WR', 72,73,74),
    ('Undersized', 'TE', 75,74,73),
    (None,         'TE', 76,77),
    ('Tall',       'TE', 78,79,80),
    (None,         'OL', 77,78),
    ('Husky',      'OL', 79,80,81,82),
    ('Undersized', 'OL', 76,75,74,73),
    ('Undersized', 'DL', 74,73,72,71),
    ('Giant',      'DL', 77,78,79,80),
    (None,         'DL', 75,76),
    ('Undersized', 'LB', 74,73,72,71),
    (None,         'LB', 75,76),
    ('Lengthy',    'LB', 76,77,78,79),
    ('Undersized', 'CB', 73,72,71,70),
    (None,         'CB', 74,75),
    ('Lanky',      'CB', 76,77,78,79),
    ('Undersized', 'S',  71,70,69,68),
    (None,         'S',  72,73),
    ('Lanky',      'S',  73,74,75,76),
    ('Undersized', 'K',  71,70,69),
    (None,         'K',  72,73),
    ('Tall',       'K',  74,75,76),
    (None,         'P',  72,73),
    ('Tall',       'P',  74,75,76),
    ('Undersized', 'P',  71,70,69),
]

# --- Scoring: (name, w_BSc, w_Elu, w_RtR, w_Hnd, w_Tck, w_PRs, w_RnS, w_PCv, w_PBk, w_RBk, w_ThV, w_ThP, w_ThA, w_KPw, w_KAc, w_PPw, w_PAc, w_Spd, w_Str, w_Hgt gate). Gate(ratings, pos) -> bool. ---
# Weights are target shares of (BSc, Elu, RtR, Hnd, Tck, PRs, RnS, PCv, PBk, RBk, ThV, ThP, ThA, KPw, KAc, PPw, PAc, Spd, Str, Hgt) scoring; match score is
# 1 - sum(|share - weight|) / 2. A row only competes when its gate passes.
# Gates receive ratings already on the gating scale (league-percentile when a
# baseline is supplied, raw otherwise) and compare against _SCORING_GATE.
def _g_route_threat(RtR, Hnd, Elu, Spd, pos):
    return RtR >= _SCORING_GATE and Hnd >= _SCORING_GATE and Elu >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('QB', 'RB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_speed_threat(RtR, Hnd, Spd, Elu, pos):
    return RtR >= _SCORING_GATE and Hnd >= _SCORING_GATE and Elu >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('QB', 'RB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_catch_threat(RtR, Hnd, Spd, Hgt, pos):
    return RtR >= _SCORING_GATE and Hnd >= _SCORING_GATE and Spd >= _SCORING_GATE and Hgt >= _SCORING_GATE and pos not in ('QB', 'RB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_big_arm(ThP, ThA, ThV, Hgt, pos):
    return ThP >= _SCORING_GATE and ThV >= _SCORING_GATE and ThA >= _SCORING_GATE and Hgt >= _SCORING_GATE and pos not in ('WR', 'RB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_dual_threat(ThP, ThA, ThV, Spd, pos):
    return ThP >= _SCORING_GATE and ThV >= _SCORING_GATE and ThA >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'RB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_run_threat(ThP, ThA, ThV, Spd, pos):
    return ThP >= _SCORING_GATE and ThV >= _SCORING_GATE and ThA >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'RB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_tackle_breaker(Elu, Str, BSc, Spd, pos):
    return Str >= _SCORING_GATE and Elu >= _SCORING_GATE and BSc >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_juke_threat(Elu, Str, BSc, Spd, pos):
    return Str >= _SCORING_GATE and Elu >= _SCORING_GATE and BSc >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_block_help(PBk, Str, RBk, Hnd, pos):
   return Str >= _SCORING_GATE and RBk >= _SCORING_GATE and PBk >= _SCORING_GATE and Hnd >= _SCORING_GATE and pos not in ('WR', 'QB', 'RB', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_vertical_threat(Hnd, Str, RBk, Spd, pos):
    return Str >= _SCORING_GATE and RBk >= _SCORING_GATE and Spd >= _SCORING_GATE and Hnd >= _SCORING_GATE and pos not in ('WR', 'QB', 'RB', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_route_blocker(RtR, Hnd, RBk, Spd, pos):
    return RtR >= _SCORING_GATE and RBk >= _SCORING_GATE and Spd >= _SCORING_GATE and Hnd >= _SCORING_GATE and pos not in ('WR', 'QB', 'RB', 'OL', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_full_wall(PBk, Str, RBk, Spd, pos):
   return Str >= _SCORING_GATE and PBk >= _SCORING_GATE and RBk >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'RB', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_rushing_wall(RBk, Str, PBk, Spd, pos):
    return Str >= _SCORING_GATE and PBk >= _SCORING_GATE and RBk >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'RB', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_all_around(RBk, Str, PBk, Spd, pos):
    return Str >= _SCORING_GATE and PBk >= _SCORING_GATE and RBk >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'RB', 'DL', 'CB', 'S', 'K', 'P', 'LB')
def _g_run_stop(RnS, Str, PRs, Tck, pos):
   return Str >= _SCORING_GATE and RnS >= _SCORING_GATE and PRs >= _SCORING_GATE and Tck >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'RB', 'CB', 'S', 'K', 'P', 'LB')
def _g_Speed_rush(PRs, Str, Tck, Spd, pos):
    return Str >= _SCORING_GATE and Spd >= _SCORING_GATE and PRs >= _SCORING_GATE and Tck >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'RB', 'CB', 'S', 'K', 'P', 'LB')
def _g_game_wreck(RnS, Spd, PRs, Str, pos):
    return Str >= _SCORING_GATE and Spd >= _SCORING_GATE and PRs >= _SCORING_GATE and RnS >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'RB', 'CB', 'S', 'K', 'P', 'LB')
def _g_patient_feet(Str, PCv, Tck, Spd, pos):
   return Str >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'S', 'K', 'P', 'LB')
def _g_ball_artist(Hgt, PCv, Tck, Spd, pos):
   return Hgt >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'S', 'K', 'P', 'LB')
def _g_slot_back(Str, PCv, Tck, Spd, pos):
     return Str >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'S', 'K', 'P', 'LB')
def _g_zone_hawk(Str, PCv, Tck, Spd, pos):
    return Str >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'CB', 'K', 'P', 'LB')
def _g_pick_artist(Str, PCv, Tck, Spd, pos):
   return Str >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'CB', 'K', 'P', 'LB')
def _g_tackle_machine(Str, PCv, Tck, Spd, pos):
  return Str >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'CB', 'K', 'P', 'LB')
def _g_zone_backer(RnS, PCv, Tck, Spd, pos):
   return RnS >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'CB', 'K', 'P', 'S')
def _g_gap_filler(RnS, PRs, Tck, Spd, pos):
   return RnS >= _SCORING_GATE and Tck >= _SCORING_GATE and PRs >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'CB', 'K', 'P', 'S')
def _g_hybrid_back(RnS, PCv, Tck, Spd, pos):
    return RnS >= _SCORING_GATE and Tck >= _SCORING_GATE and PCv >= _SCORING_GATE and Spd >= _SCORING_GATE and pos not in ('WR', 'QB', 'TE', 'OL', 'DL', 'RB', 'CB', 'K', 'P', 'S')



_SCORING = [
    ('Route-Threat',    0.25, 0.25, 0.25, 0.25, _g_route_threat),
    ('Speed-Threat',    0.20, 0.20, 0.20, 0.40, _g_speed_threat),
    ('Catch-Threat',      0.20, 0.20, 0.40, 0.20, _g_catch_threat),
    ('Big-Arm',       0.17, 0.17, 0.33, 0.33, _g_big_arm),
    ('Dual-Threat',       0.20, 0.40, 0.20, 0.20, _g_dual_threat),
    ('Run-Threat',            0.20, 0.40, 0.20, 0.20, _g_run_threat),
    ('Tackle-Breaker',          0.40, 0.20, 0.20, 0.20, _g_tackle_breaker),
    ('Juke-Threat',     0.29, 0.29, 0.13, 0.29, _g_juke_threat),
    ('Block-Help', 0.29, 0.29, 0.29, 0.13, _g_block_help),
    ('Vertical-Threat',0.25, 0.25, 0.25, 0.25, _g_vertical_threat),
    ('Route-Blocker',  0.20, 0.20, 0.20, 0.40, _g_route_blocker),
    ('Full-Wall',      0.20, 0.20, 0.40, 0.20, _g_full_wall),
    ('Rushing-Wall',   0.17, 0.17, 0.33, 0.33, _g_rushing_wall),
    ('All-Around',     0.20, 0.40, 0.20, 0.20, _g_all_around),
    ('Run-Stop',       0.20, 0.40, 0.20, 0.20, _g_run_stop),
    ('Speed-Rush',     0.40, 0.20, 0.20, 0.20, _g_Speed_rush),
    ('Game-Wreck',     0.29, 0.29, 0.13, 0.29, _g_game_wreck),
    ('Patient-Feet',   0.29, 0.29, 0.29, 0.13, _g_patient_feet),
    ('Ball-Artist',    0.25, 0.25, 0.25, 0.25, _g_ball_artist),
    ('Slot-Back',      0.20, 0.20, 0.20, 0.40, _g_slot_back),
    ('Zone-Hawk',      0.20, 0.20, 0.40, 0.20, _g_zone_hawk),
    ('Pick-Artist',    0.17, 0.17, 0.33, 0.33, _g_pick_artist),
    ('Tackle-Machine', 0.20, 0.40, 0.20, 0.20, _g_tackle_machine),
    ('Zone-Backer',            0.20, 0.40, 0.20, 0.20, _g_zone_backer),
    ('Gap-Filler',          0.40, 0.20, 0.20, 0.20, _g_gap_filler),
    ('Hybrid-Back',     0.29, 0.29, 0.13, 0.29, _g_hybrid_back),
]

# --- Prospect position groups ---
_PROSPECT_GROUP = {
    'QB': 'Quarter-Back', 
    'WR': 'Receiver',
    'RB': 'Wing-Back', 
    'OL': 'O-Line',
    'DL': 'D-Line',
    'LB': 'Backer', 
    'CB': 'Corner',
    'S':  'Safety', 
    'TE': 'Tight-End',
    'K':  'Kicker',
    'P':  'Punter',
}

_SKILL = {
    'QB': {
        (10, 10, 10): 'Strong Arm', 
        (10, 50, 10): 'Scrambler', 
        (10, 90, 10): 'Field General',
      
    },
    'RB': {
        (10, 10, 10): 'Elusive', 
        (10, 50, 10): 'Power', 
        (10, 90, 10): 'Receiving',  
      
    },
    'WR': {
        (10, 10, 10): 'Slot', 
        (10, 50, 10): 'Physical', 
        (10, 90, 10): 'Deep Threat', 
     
    },
    'TE': {
        (10, 10, 10): 'Vertical', 
        (10, 50, 10): 'Possession', 
        (10, 90, 10): 'Blocking', 
        
    },
    'OL': {
        (10, 10, 10): 'Agile', 
        (10, 50, 10): 'Run Block', 
        (10, 90, 10): 'Pass Block',
      
    },
    'LB': {
        (10, 10, 10): 'Speed Rusher', 
        (10, 50, 10): 'Run Stopper', 
        (10, 90, 10): 'Pass Rusher', 
     
    },
    'PF': {
        (10, 10, 10): 'Pass Defender',
        (10, 50, 10): 'Edge Rusher', 
        (10, 90, 10): 'Run Stuffer',
  
    },
    'CB': {
        (10, 10, 10): 'Slot', 
        (10, 50, 10): 'Man',
        (10, 90, 10): 'Zone', 
    
    },
    'S': {
        (10, 10, 10): 'Hybrid', 
        (10, 50, 10): 'Run Support', 
        (10, 90, 10): 'Coverage', 
     
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


def _scoringBSc,(Elu, RtR, Hnd, Tck, PRs, RnS, PCv, PBk, RBk, ThV, ThP, ThA, KPw, KAc, PPw, PAc, Spd, Str, Hgt, gate_Elu, gate_RtR, gate_Hnd, gate_Tck, gate_PRs, gate_RnS, gate_PCv, gate_PBk, gate_RBk, gate_ThV, gate_ThP, gate_ThA, gate_KPw, gate_KAc, gate_PPW, gate_PAc, gate_Spd, gate_Str, gate_Hgt ,pos):
    """Scoring descriptor + distinctiveness, as (word, dist). Shares (style) come
    from the raw Elu/RtR/Hnd/Tck/PRs/RnS/PCv/PBk/RBk/ThV/ThP/ThA/KPw/KAc/PPw/PAc/Spd/Str/Hgt; the gates that decide which descriptors a player
    qualifies for use the gate_* values (league-percentile in relative mode, else
    equal to raw). `dist` (0-1+) measures how lopsided the scoring profile is —
    used to rank descriptors when labels are trimmed."""
    total = Elu+RtR+Hnd+Tck+PRs+RnS+PCv+PBk+RBk+ThV+ThP+ThA+KPw+KAc+PPw+PAc+Spd+Str+Hgt
    if total <= 0:
        return ('', 0.0)
    shares = (Elu/RtR/Hnd/Tck/PRs/RnS/PCv/PBk/RBk/ThV/ThP/ThA/KPw/KAc/PPw/PAc/Spd/Str/Hgt/total)
    best_name, best_score = '', 0.0
    for name, wi, wd, w2, w3, gate in _SCORING:
        if not gate(gate_Elu, gate_RtR, gate_Hnd, gate_Tck, gate_PRs, gate_RnS, gate_PCv, gate_PBk, gate_RBk, gate_ThV, gate_ThP, gate_ThA, gate_KPw, gate_KAc, gate_PPW, gate_PAc, gate_Spd, gate_Str, gate_Hgt, pos):
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
    """Return the canonical FBGM archetype string for a player.

    `ratings` is a FBGM ratings dict (keys: BSc, Elu, RtR, Hnd, Tck, PRs, RnS, PCv, PBk, RBk, ThV, ThP, ThA, KPw, KAc, PPw, PAc, Spd, Hgt, Str). `position` is the FBGM pos string
    (QB/RB/WR/TE/OL/DL/LB/CB/S/K/P). `ovr`/`age` drive the Prospect/Veteran tier; if
    omitted, `ovr` falls back to ratings['ovr'] and tiers requiring age are
    skipped.

    `dim_stats` is an optional per-rating {key: (mean, std)} league baseline
    (as produced by player_builds._league_dim_stats). When supplied, the ability
    dimensions (Athleticism, Skill) and the Scoring gates are matched on the
    league-percentile scale instead of raw ratings — see the module docstring.
    Scoring style and Height remain absolute either way.

    `max_adjectives` caps how many descriptors precede the skill noun: the skill
    noun (the identity) is always kept, and only the N most distinctive adjectives
    (Height/Athleticism/Scoring — whichever the player deviates from average on
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

    skill = _skill(pos, rel('RtR'), rel('ThP'), rel('BSc'), rel('Elu'), rel('Hnd'), rel('PRs'), rel('Rns'), rel('ThV'), rel('ThA'), rel('PCv'), rel('Tck'), rel('PBk'),rel('RBk'), rel('KPw'),rel('KAc'), rel('PPw'), rel('PAc'), rel('Spd'), rel('Hgt'), rel('Str'))  # noun — always kept

    # Adjective candidates as (canonical_order, word, distinctiveness). Only
    # non-blank descriptors compete; blanks contribute nothing.
    hgt = g('Hgt', 0)  # absolute — physical measurable, not league-relative
    rel_athl = (rel('Str'), rel('Spd'), rel('End'))
    scoring_word, scoring_dist = _scoring(
        rel('BSc'), rel('Elu'), rel('RtR'), rel('ThV'), rel('ThA'), rel('Hnd', 0), rel('PBk'),rel('RBk'), rel('KPw'), rel('KAc'), rel('PPw'), rel('PAc'),
        rel('Tck'), rel('PRs'), rel('Rns'), rel('PCv'), pos)

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
