"""Compositional playstyle classifier using 2K's actual build vocabulary.

Names players by mapping their BBGM rating clusters onto the same 250+ build
names NBA 2K25/2K26 use. The catalog and naming pattern come straight from 2K
(prefixes 2 Way / Diming / Stretch / Inside Out / 3 Level / Glass Cleaning /
Slashing / Sharpshooting / Playmaking, plus evocative primary nouns); only the
classification formulas underneath are our own.

Z-score normalizes against the league's own rating distribution so a player
who's the league's best shooter gets the elite shooter label whether their
raw rating is 75 or 95.
"""

# Normalized-rating thresholds — every atom is now stored as its percentile rank
# (0=worst in league, 100=best). 2K-style: one consistent 0-100 scale everywhere.
# Approximate percentile values for the bell-curve equivalents:
#   z=-0.5  -> ~31st pctile -> WEAK
#   z= 0.35 -> ~64th        -> SOFT  (2-Way prefix bar)
#   z= 0.45 -> ~67th        -> FALLBACK_STRONG (compositional fallback)
#   z= 0.6  -> ~73rd        -> STRONG (secondary trait)
#   z= 1.3  -> ~90th        -> ELITE  (primary-quality trait)
#   z= 2.3  -> ~99th        -> TRANSCENDENT (one-in-a-hundred)
WEAK = 30
SOFT = 64
FALLBACK_STRONG = 67
STRONG = 73
ELITE = 90
TRANSCENDENT = 99

# Top-tier (composite) percentile gates — same scale, just different ceilings.
P_GENERATIONAL = 99.7
P_MULTI = 99
P_VERSATILE = 97
P_RARE = 98
P_THREAT = 97
P_SPEC = 98

# League-elite OVR fallback bars (kept for raw-OVR sanity floors in stars).
ELITE_PCTILE = 5
STAR_PCTILE = 2

_RATING_KEYS = ('tp', 'ft', 'ins', 'dnk', 'pss', 'drb', 'spd', 'jmp', 'diq', 'reb', 'hgt', 'stre', 'oiq', 'endu', 'fg')


def _ratings_for_season(p, season):
    """Return the player's rating dict as-of `season`, or None if they have none."""
    for r in p.get('ratings') or []:
        if r.get('season') == season:
            return r
    return None


def _was_active_in_season(p, season):
    """True if the player played for any team in the given season."""
    for s in p.get('stats') or []:
        if s.get('season') == season and s.get('tid', -1) >= 0:
            return True
    return False


def _ranking_pool(players, season=None):
    """Players that count toward league baselines and percentile ranks.

    Current season (season=None):
      - Signed players only (tid >= 0). Free agents are deliberately excluded
        from the comparison population: a build's percentiles describe how a
        player stacks up against the players actually on rosters. FAs still get
        a build + percentiles, but they're ranked *against* this pool rather
        than being part of it (see percentiles_against_pool).
    Historical (season=YYYY):
      - Players active in that season (existing behavior).

    Returns a list of (player, ratings_dict_to_use) tuples — the single
    source of truth for _league_dim_stats, _compute_player_percentiles and
    _pool_distributions so they all stay in sync.
    """
    if season is not None:
        out = []
        for p in players:
            if not _was_active_in_season(p, season):
                continue
            r = _ratings_for_season(p, season)
            if r is None:
                continue
            out.append((p, r))
        return out
    rostered = []
    for p in players:
        rl = p.get('ratings') or []
        if not rl:
            continue
        if p.get('tid', -1) >= 0:
            rostered.append((p, rl[-1]))
    return rostered


def _league_dim_stats(players, season=None):
    """Compute league rating baselines.

    Pool: signed players (current season) or season-active players
    (historical). See _ranking_pool.
    """
    sums = {k: 0.0 for k in _RATING_KEYS}
    sqs = {k: 0.0 for k in _RATING_KEYS}
    n = 0
    ovrs = []
    for p, r in _ranking_pool(players, season):
        if all(r.get(k, 0) == 0 for k in _RATING_KEYS):
            continue
        bad_row = False
        for k in _RATING_KEYS:
            v = r.get(k, 0)
            if not isinstance(v, (int, float)):
                # Skip players whose ratings dict has a non-numeric value
                # for a rating key (corruption / historical schema oddity);
                # otherwise ovrs.sort() and z-score math blow up.
                bad_row = True
                break
            sums[k] += v
            sqs[k] += v * v
        if bad_row:
            continue
        ovr_v = r.get('ovr', 0)
        if not isinstance(ovr_v, (int, float)):
            continue
        n += 1
        ovrs.append(ovr_v)
    if n == 0:
        return None
    out = {}
    for k in _RATING_KEYS:
        mean = sums[k] / n
        var = max(0.0, sqs[k] / n - mean * mean)
        std = max(1.0, var ** 0.5)
        out[k] = (mean, std)
    # League-elite OVR bars (percentile cutoffs) used to gate star labels
    ovrs.sort()
    def pctile_cutoff(pct):
        if not ovrs:
            return 999
        idx = max(0, min(len(ovrs) - 1, int(len(ovrs) * (1 - pct / 100))))
        return ovrs[idx]
    out['_elite_ovr'] = pctile_cutoff(ELITE_PCTILE)
    out['_star_ovr']  = pctile_cutoff(STAR_PCTILE)
    return out


_RANK_RAW_KEYS = ('tp','ft','dnk','drb','pss','spd','jmp','diq','ins','stre','reb','oiq','fg')


def _composites_for(r, dim_stats):
    """The rankable composite+raw vector for one player's ratings dict.

    Single source of truth so pool members (_compute_player_percentiles) and
    off-pool players (percentiles_against_pool) are scored on identical math.
    """
    a = _compute_atoms(r, dim_stats)
    composites = {
        # 7 atoms (rankable)
        'shoot':       a['shoot'],
        'slash':       a['slash'],
        'playmake':    a['playmake'],
        'defend':      a['defend'],
        'glass':       a['glass'],
        'post':        a['post'],
        'rim_protect': a['rim_protect'],
        # super-composites
        'overall':     a['shoot'] + a['slash'] + a['playmake'] + a['defend'] + a['glass'] + a['post'] + a['rim_protect'],
        'scoring':     a['shoot'] + a['slash'] + a['post'],
        'shoot_slash': a['shoot'] + a['slash'],
        'slash_dnk':   a['slash'] + _z(r.get('dnk', 0), dim_stats, 'dnk'),
    }
    # Raw ratings as their own keys, prefixed with _ to match Easter-egg conventions
    for rk in _RANK_RAW_KEYS:
        composites['_' + rk] = r.get(rk, 0)
    return composites


def _pool_distributions(players, dim_stats, season=None):
    """Per-key sorted value arrays across the ranking pool.

    Lets us rank a player who is NOT in the pool (a free agent) against the
    signed-player population without re-scoring everyone. See
    percentiles_against_pool.
    """
    vals = {}
    for p, r in _ranking_pool(players, season):
        if all(r.get(k, 0) == 0 for k in _RATING_KEYS):
            continue
        for k, v in _composites_for(r, dim_stats).items():
            vals.setdefault(k, []).append(v)
    for k in vals:
        vals[k].sort()
    return vals


def percentiles_against_pool(r, dim_stats, distributions):
    """Percentile rank (0-100) of one player's composites vs a pool's
    distributions — the fraction of the pool that ranks at or below them.

    Used for free agents (and anyone outside the ranking pool) so their build
    context is measured against signed players. Returns None if no pool.
    """
    import bisect
    if not distributions:
        return None
    out = {}
    for k, v in _composites_for(r, dim_stats).items():
        arr = distributions.get(k)
        if not arr:
            continue
        out[k] = (bisect.bisect_right(arr, v) / len(arr)) * 100
    return out


def _compute_player_percentiles(players, dim_stats, season=None):
    """For each player in the ranking pool, compute their league-wide
    percentile rank in:
      - the 7 composite atoms (shoot, slash, playmake, defend, glass, post, rim_protect)
      - 4 super-composites (overall, scoring, shoot_slash, slash_dnk)
      - raw individual ratings (_tp, _ft, _dnk, _drb, _pss, _spd, _jmp, _diq, _ins, _stre, _reb, _oiq)

    All values 0-100 (100 = league-best within the pool). Pool is signed
    players for current season (historical seasons use season-active
    players). See _ranking_pool.
    """
    scored = []
    for p, r in _ranking_pool(players, season):
        if all(r.get(k, 0) == 0 for k in _RATING_KEYS):
            continue
        scored.append((p.get('pid'), _composites_for(r, dim_stats)))

    if not scored:
        return {}

    keys = list(scored[0][1].keys())
    pctiles_by_pid = {pid: {} for pid, _ in scored}
    n = len(scored)
    for key in keys:
        sorted_by_key = sorted(scored, key=lambda x: x[1][key])
        for rank, (pid, _) in enumerate(sorted_by_key):
            pctile = (rank / max(1, n - 1)) * 100
            pctiles_by_pid[pid][key] = pctile
    return pctiles_by_pid


def _z(value, dim_stats, key):
    if not dim_stats or key not in dim_stats:
        return 0.0
    mean, std = dim_stats[key]
    return (value - mean) / std


def _compute_atoms(ratings, dim_stats):
    z = lambda k: _z(ratings.get(k, 0), dim_stats, k)
    return {
        # Composite atoms
        'shoot':       (z('tp') + z('ft')) / 2,
        'slash':       (z('dnk') + z('spd') + z('ins')) / 3,
        'playmake':    (z('pss') + z('drb') + z('oiq')) / 3,
        'defend':      (z('diq') + z('spd')) / 2,
        # Height-aware composites mirroring BBGM's real rebounding (R) and
        # post (Po) sim formulas — see calccompsingle() in player_commands.
        # A short player with a high reb/ins rating no longer scores like an
        # elite rebounder/post when the sim would weight height just as heavily.
        'glass':       (2 * z('reb') + 2 * z('hgt') + 0.5 * z('diq')
                        + 0.5 * z('oiq') + 0.1 * z('stre') + 0.1 * z('jmp')) / 5.2,
        'post':        (z('hgt') + z('ins') + 0.6 * z('stre')
                        + 0.2 * z('spd') + 0.4 * z('oiq')) / 3.2,
        'rim_protect': (z('diq') + z('jmp') + z('hgt')) / 3,
        'mid_range':   z('fg'),
        # Raw z-scores for Easter-egg conditions
        '_tp':   z('tp'),
        '_ft':   z('ft'),
        '_dnk':  z('dnk'),
        '_spd':  z('spd'),
        '_jmp':  z('jmp'),
        '_drb':  z('drb'),
        '_pss':  z('pss'),
        '_diq':  z('diq'),
        '_ins':  z('ins'),
        '_stre': z('stre'),
        '_reb':  z('reb'),
        '_oiq':  z('oiq'),
        '_fg':   z('fg'),
    }


def _size_tier(ratings, dim_stats, position=None):
    """Categorize player size for archetype gates.

    Position-aware when supplied — a 6'5" PG should bucket as 'guard'
    even though height alone would put them in 'wing'. Falls back to
    height-only when no position is given. SF/PF still use height as a
    tiebreaker (a 6'10" SF is functionally a 'big')."""
    pos = position or ratings.get('pos', '')
    hgt = ratings.get('hgt', 0)
    z_hgt = _z(hgt, dim_stats, 'hgt')
    if pos in ('PG', 'SG'):
        return 'guard'
    if pos == 'C':
        return 'big'
    if pos == 'PF':
        return 'big' if (z_hgt >= 0.5 or hgt >= 65) else 'wing'
    if pos == 'SF':
        if z_hgt >= 0.9 or hgt >= 75:
            return 'big'
        if z_hgt <= -0.5 or hgt <= 55:
            return 'guard'
        return 'wing'
    # Unknown / no position — fall back to height alone
    if z_hgt >= 0.7 or hgt >= 70:
        return 'big'
    if z_hgt <= -0.4 or hgt <= 55:
        return 'guard'
    return 'wing'


# Map BBGM skill badges to the atom each provides evidence for. Used by
# the multi-elite compositional rules to nudge near-elite atoms into the
# elite set when the badge confirms the skill.
_BADGE_FOR_ATOM = {
    'shoot':       ('3', 'V'),
    'slash':       ('A', 'V'),
    'playmake':    ('Ps', 'B'),
    'defend':      ('Dp',),
    'glass':       ('R',),
    'post':        ('Po', 'V'),
    'rim_protect': ('Di',),
}


def _multi_elite_compositional(a, size, position, skills, soft_def):
    """Tier-1 compositional label naming WHICH elite atoms are present.

    Returns None when no specific combination matches — caller falls back
    to the generic Multi Faceted / Versatile Star labels.

    Two elite predicates:
    - is_elite_strict: pctile >= ELITE (90) only, no badge nudge.
      Used for the rarest archetype (Four-Level Maestro) so it stays
      reserved for genuine 4-skill outliers.
    - is_elite: ELITE OR (pctile >= BADGE_NEAR_ELITE AND badge confirms).
      Used for all other compositionals. The 85 floor (top 15%) keeps
      badge boost from collapsing scarcity at top tiers.
    """
    skill_set = set(skills or ())
    BADGE_NEAR_ELITE = 85

    def is_elite_strict(atom):
        return a.get(atom, 0) >= ELITE

    def is_elite(atom):
        v = a.get(atom, 0)
        if v >= ELITE:
            return True
        if v >= BADGE_NEAR_ELITE and any(b in skill_set for b in _BADGE_FOR_ATOM.get(atom, ())):
            return True
        return False

    main = ('shoot', 'slash', 'playmake', 'defend', 'glass', 'post', 'rim_protect')
    elite = {k for k in main if is_elite(k)}
    elite_strict = {k for k in main if is_elite_strict(k)}

    if len(elite) < 3:
        return None

    is_big = size == 'big'

    # 4-way scoring + creating — strict elite on all four AND top 1%
    # overall. Should fire on 0-1 players in a typical league.
    if (a.get('overall', 0) >= P_MULTI
            and {'shoot', 'slash', 'playmake', 'post'}.issubset(elite_strict)):
        return 'Four-Level Maestro'

    # Inside-out hub: post + shoot + playmake (Embiid, Cousins)
    if {'shoot', 'post', 'playmake'}.issubset(elite):
        return 'Inside-Out Hub'

    # 3-skill creator (Luka)
    if {'shoot', 'slash', 'playmake'}.issubset(elite):
        return 'Two-Way Three-Level Playmaker' if soft_def else 'Three-Level Playmaker'

    # 3-level scoring without creation
    if {'shoot', 'slash', 'post'}.issubset(elite):
        return '2 Way 3 Level Threat' if soft_def else '3 Level Threat'

    # Point center / hub big (Jokic)
    if is_big and ({'post', 'playmake', 'glass'}.issubset(elite) or {'post', 'playmake'}.issubset(elite)):
        return 'Point Center'

    # Triple-double threat — playmake + glass + slash (LeBron-lite)
    if {'playmake', 'glass', 'slash'}.issubset(elite):
        return 'Triple-Double Threat'

    # Defensive anchor — big with rim_protect + defend + glass (Gobert)
    if is_big and {'defend', 'rim_protect', 'glass'}.issubset(elite):
        return 'Anchor'

    # Two-Way Rim Wrecker — slash + defend + glass, no shooting (Giannis)
    if {'slash', 'defend', 'glass'}.issubset(elite) and 'shoot' not in elite:
        return 'Two-Way Rim Wrecker'

    # Two-Way Sniper — shoot + defend + secondary scoring (Kawhi, Mikal)
    if {'shoot', 'defend'}.issubset(elite) and (elite & {'slash', 'post', 'playmake'}):
        return 'Two-Way Sniper'

    # Inside-Out Scorer — shoot + post (KD, Dirk)
    if {'shoot', 'post'}.issubset(elite):
        return 'Two-Way Inside-Out Scorer' if soft_def else 'Inside-Out Scorer'

    # Defensive Wrecking Ball — defend + rim_protect alone
    if {'defend', 'rim_protect'}.issubset(elite):
        return 'Defensive Wrecking Ball'

    return None


def _named_archetype(a_z, size, position, ovr=0, elite_bar=999, star_bar=999, pctiles=None, skills=()):
    """Map atom profile onto a 2K-vocabulary name.

    Rules ordered most-specific first. Returns None if no rule matches
    (rare — the fallback covers it).
    """
    # `a` is now the NORMALIZED rating dict (0-100 percentile in each atom),
    # not the z-score dict. Everything below the rule entry-point speaks
    # the same 0-100 scale as 2K ratings.
    pctiles = pctiles or {}
    a = pctiles  # alias: rules use 'a' for compactness
    s = a.get('shoot', 0); sl = a.get('slash', 0); pm = a.get('playmake', 0)
    d = a.get('defend', 0); g = a.get('glass', 0); po = a.get('post', 0); rp = a.get('rim_protect', 0)
    # mid_range stays as raw z (no atom-percentile for it)
    mr = a_z.get('mid_range', 0)
    is_big = size == 'big'
    is_wing = size == 'wing'
    is_guard = size == 'guard'

    main = ('shoot','slash','playmake','defend','glass','post','rim_protect')
    strong_n = sum(1 for k in main if a.get(k, 0) >= STRONG)
    elite_n = sum(1 for k in main if a.get(k, 0) >= ELITE)
    trans_n = sum(1 for k in main if a.get(k, 0) >= TRANSCENDENT)

    def pct(key): return pctiles.get(key, 0)
    # 2-Way prefix tiering:
    #   soft_def (SOFT=64 pctile) — for tier 1/2 star labels (Two-Way Specimen, 2 Way 3 Level Threat)
    #   mid_def  (FALLBACK_STRONG=67 pctile) — for tier 3 named archetypes (2 Way Stretch Five, etc.)
    soft_def = d >= SOFT
    mid_def = d >= FALLBACK_STRONG
    has_shoot = s >= STRONG
    has_slash = sl >= STRONG
    has_play = pm >= STRONG
    has_glass = g >= STRONG
    has_post = po >= STRONG
    has_inside = sl >= STRONG or po >= STRONG
    three_level = s >= STRONG and (sl >= STRONG or po >= STRONG) and mr >= 0
    # elite_three_level kept for legacy Tier 3 wing rule below. Tier 2 now uses
    # the scoring-composite percentile gate.
    elite_three_level = (
        s >= STRONG and sl >= STRONG and po >= STRONG
        and (s >= TRANSCENDENT or sl >= TRANSCENDENT or po >= TRANSCENDENT)
    )

    # =================================================================
    # TIER 0 — Generational outlier (top 0.5% AND deep skill stack).
    # Reserved for the one player in a league who's an obvious cut above
    # — Kawhi-at-88-OVR types. Almost always exactly 1 per league.
    # =================================================================
    if pct('overall') >= P_GENERATIONAL and elite_n >= 6 and trans_n >= 2:
        return 'Generational'

    # =================================================================
    # TIER 1 — Star labels gated on BOTH percentile AND absolute z-floor.
    # Percentile keeps the label scarce; absolute floor prevents the
    # "best of the worst" problem in low-rating leagues.
    # =================================================================
    # Multi-elite compositional first — names the specific skill combo
    # (Three-Level Playmaker, Point Center, Two-Way Rim Wrecker, etc.)
    # before falling back to generic "Star" / "Specimen" labels.
    if pct('overall') >= P_VERSATILE:
        compound = _multi_elite_compositional(a, size, position, skills, soft_def)
        if compound:
            return compound
    if pct('overall') >= P_MULTI and elite_n >= 4:
        return 'Multi Faceted Star'
    if pct('overall') >= P_VERSATILE and elite_n >= 3 and soft_def:
        return 'Two-Way Specimen'
    if pct('overall') >= P_VERSATILE and elite_n >= 3:
        return 'Versatile Star'
    # Pure specialists — top percentile in that atom AND absolutely ELITE at it
    if pct('shoot') >= P_SPEC and s >= ELITE and strong_n <= 3:
        return 'Three-Point Titan' if is_guard else 'Stretch Sniper'
    if pct('playmake') >= P_SPEC and pm >= ELITE and strong_n <= 3:
        return 'The Creator' if not is_big else 'Pivot Playmaker'
    if pct('defend') >= P_SPEC and d >= ELITE and strong_n <= 3:
        return 'Straight Jacket'
    if pct('glass') >= P_SPEC and g >= ELITE and strong_n <= 3:
        return 'Boardmaster'
    if pct('post') >= P_SPEC and po >= ELITE and strong_n <= 3:
        return 'Low-Post Luminary'
    if pct('rim_protect') >= P_SPEC and rp >= ELITE:
        return 'Swat King'
    if pct('slash_dnk') >= P_SPEC and sl >= ELITE and a['_dnk'] >= ELITE:
        return 'Rim Rampager'

    # =================================================================
    # TIER 2 — Easter eggs (percentile + absolute z-floor gates)
    # =================================================================
    if pct('scoring') >= P_THREAT and s >= STRONG and sl >= STRONG and po >= STRONG and soft_def and not is_big:
        return '2 Way 3 Level Threat'
    if pct('scoring') >= P_THREAT and s >= STRONG and sl >= STRONG and po >= STRONG and not is_big:
        return '3 Level Threat'
    if pct('shoot_slash') >= P_RARE and s >= ELITE and sl >= ELITE and d < 50:
        return 'Walking Bucket'
    if pct('shoot_slash') >= P_RARE and s >= ELITE and sl >= ELITE and soft_def:
        return '2 Way Walking Bucket'
    if pct('slash') >= P_RARE and sl >= ELITE and a['_drb'] >= STRONG and pm < STRONG:
        return 'Iso King'
    if is_guard and a['_spd'] >= ELITE and a['_drb'] >= STRONG and a['_tp'] >= STRONG:
        return 'Flamethrower'
    if is_big and rp >= ELITE and a['_jmp'] >= STRONG:
        return 'Sky Fortress'
    if not is_big and a['_dnk'] >= ELITE and a['_jmp'] >= ELITE:
        return 'Highlight Reel'
    if is_big and po >= ELITE and g >= STRONG and s < WEAK:
        return 'Paint Beast'
    if is_guard and a['_spd'] >= ELITE and pm >= STRONG and sl >= STRONG:
        return 'Tempo Pushing Guard'
    if is_big and a['_jmp'] >= STRONG and d >= STRONG and elite_n == 0:
        return 'Energy Big'
    if a['_ft'] >= ELITE and a['_fg'] >= STRONG and a['_tp'] < STRONG:
        return 'Mid Range Assassin'
    if not is_big and a['_jmp'] >= STRONG and sl >= STRONG and a['_dnk'] >= STRONG:
        return 'Athletic Finisher'
    if is_wing and a['_jmp'] >= STRONG and rp >= STRONG:
        return 'Sky Fortress' if a['_jmp'] >= ELITE else 'Shot Blocking Wing'
    # Glue Guy: solid floor everywhere, ceiling nowhere (no atom below ~38th pctile)
    if elite_n == 0 and strong_n >= 3 and all(a.get(k, 0) >= 38 for k in main):
        return 'Jack of All Trades'

    # =================================================================
    # TIER 3 — Combinatorial named archetypes (the 2K name engine)
    # =================================================================

    # --- BIGS ---
    if is_big:
        # Stretch family
        if s >= ELITE:
            if mid_def and has_play: return '2 Way Stretch Playmaker'
            if mid_def:              return '2 Way Stretch Five' if position == 'C' else '2 Way Stretch Four'
            if has_play:             return 'Stretch Playmaker'
            if has_glass:            return 'Stretch Glass Cleaner'
            return 'Stretch Five' if position == 'C' else 'Stretch Four'
        if s >= STRONG and (has_post or has_glass):
            if mid_def: return '2 Way Skilled Stretch Five' if position == 'C' else '2 Way Skilled Stretch Four'
            return '2 Way Skilled Stretch' if mid_def else 'Court Extender'
        # Paint scorer family
        if po >= ELITE:
            if mid_def and has_play: return 'Playmaking Paint Beast'
            if has_play:             return '2 Way Post Playmaker' if mid_def else 'Post Playmaker'
            if has_glass and mid_def: return '2 Way 3 Level Interior Force' if s >= STRONG else 'Skilled Interior Force'
            if has_glass:            return 'Paint Bully' if s < 50 else 'Interior Force'
            if mid_def:              return 'Defensive Menace'
            return 'Low-Block Bully'
        # Playmaking big
        if pm >= ELITE:
            if mid_def: return 'Playmaking Defensive Anchor'
            return 'Pivot Playmaker'
        # Defensive / rebounding bigs
        if (rp >= ELITE or d >= ELITE) and s < 50 and po < STRONG:
            return 'Defensive Anchor'
        if rp >= ELITE:
            return 'The Protector'
        if has_glass and mid_def and s < 50:
            return 'Glass Cleaning Lockdown'
        if has_glass and mid_def:
            return '2 Way Glass Cleaner' if elite_n == 0 else 'Glass General'
        if g >= ELITE:
            return 'Board Hunter'
        if pm >= STRONG and po >= STRONG and s >= STRONG:
            return 'Universal Big'
        if has_post and has_glass:
            return 'Inside The Arc Glass Cleaner' if mr >= 0 else 'Interior Scorer'
        if has_post:
            return 'Post Scorer'
        if has_glass:
            return 'Glass Cleaner'
        if mid_def:
            return 'Hybrid Defender'

    # --- WINGS ---
    if is_wing:
        # 3 & D family
        if s >= STRONG and mid_def and sl < ELITE:
            if has_play: return '2 Way Sharpshooting Facilitator'
            if has_glass: return 'Glass Cleaning Lockdown'
            return '3 & D Wing'
        # Two-Way Wing combos
        if mid_def and sl >= STRONG and s >= STRONG:
            return '2 Way 3 Level Threat'
        if mid_def and sl >= ELITE:
            return 'Switchable Lockdown Defender'
        # Slashing combos
        if sl >= STRONG and pm >= STRONG and s < ELITE:
            if mid_def: return '2 Way Slashing Playmaker'
            return 'Slashing Playmaker'
        if sl >= ELITE:
            if mid_def: return '2 Way Inside The Arc Threat'
            return 'Inside The Arc Maestro'
        # Shooting wings
        if s >= ELITE:
            if has_play: return 'Sharpshooting Facilitator'
            return 'Sniper Sentinel' if mid_def else 'Floor Spacer'
        if s >= STRONG and has_play:
            if mid_def: return '2 Way Diming Sharpshooter'
            return 'Diming Sharpshooter'
        # Playmaking wings
        if pm >= ELITE:
            if mid_def: return '2 Way Point Forward'
            return 'Point Forward'
        if pm >= STRONG and (mid_def or has_glass):
            return 'Connector'
        # Post-up wing (rare)
        if has_post and s < 50:
            return 'Old-School Wing'
        if has_post and mid_def:
            return '2 Way Post Playmaker'
        # Versatile scorer wing
        if (sl >= STRONG or po >= STRONG) and s >= STRONG and pm < STRONG:
            return 'Scoring Machine' if mid_def else 'Balanced Scorer'
        # Glass-cleaning wing
        if has_glass and mid_def:
            return '2 Way Glass Cleaning Slasher' if has_slash else '2 Way Glass Cleaner'
        if has_glass:
            return 'Rebounding Wing'
        # Pure shooters
        if has_shoot:
            return 'Spot Up Threat'
        # Defenders
        if mid_def:
            return 'Wing Stopper'

    # --- GUARDS ---
    if is_guard:
        # Floor General family
        if pm >= ELITE and s >= STRONG:
            if mid_def: return '2 Way Floor General'
            return 'Floor General'
        if pm >= ELITE and s < 50:
            return 'Pure Point'
        if pm >= ELITE and sl >= STRONG:
            return '2 Way Slashing Playmaker' if mid_def else 'Dynamic Point'
        if pm >= ELITE:
            return 'Magician'
        # Three-Level scoring guards
        if three_level:
            if mid_def: return '2 Way 3 Level Scorer'
            if has_play: return '3 Level Playmaker'
            return '3 Level Scorer'
        # Shifty Sniper (handles + shoot)
        if s >= ELITE and a['_drb'] >= STRONG:
            return 'Shifty Sniper' if not mid_def else '2 Way Shot Creator'
        # Shooting guards
        if s >= ELITE:
            if has_play: return '2 Way Diming Sharpshooter' if mid_def else 'Diming Sharpshooter'
            if mid_def: return '2 Way Sharpshooter'
            return 'Sniper Guard'
        # 3 & D Guards
        if s >= STRONG and mid_def:
            if has_play: return 'Diming 3 & D Guard'
            return '3 & D Guard'
        if s >= STRONG and has_play:
            return 'Sharpshooting Facilitator'
        # Slashing guards
        if sl >= ELITE:
            if mid_def: return '2 Way Slasher'
            if has_play: return 'Slashing Playmaker'
            return 'Finesse Finisher' if a['_drb'] >= STRONG else 'Slasher'
        if sl >= STRONG and pm >= STRONG:
            return 'Slashing Playmaker'
        # Shot Creator
        if sl >= STRONG and s >= STRONG and a['_drb'] >= STRONG:
            return '2 Way Shot Creator' if mid_def else 'Shot Creator'
        # Defensive guards
        if d >= ELITE and s < 50 and pm < 50:
            return 'Ball Hawk'
        if d >= ELITE and a['_drb'] >= STRONG:
            return 'Pesky Defender'
        if d >= ELITE:
            return 'Point of Attack Stopper'
        if d >= STRONG and g >= STRONG and s < 50:
            return 'Gritty Guard'
        if d >= STRONG and has_glass:
            return 'Rebounding Guard'
        # Pure shooters
        if has_shoot and has_play:
            return 'Diming Sharpshooter'
        if has_shoot:
            return 'Sharpshooter'
        # Playmaker fallback
        if has_play:
            return 'Pass First Point' if s < 50 else 'Secondary Ball Handler'
        # Slasher fallback
        if has_slash:
            return 'Athletic Masher' if a['_dnk'] >= STRONG else 'Rim Attacker'

    # =================================================================
    # TIER 4 — single-pillar defaults (when nothing matched above)
    # =================================================================
    if s >= ELITE: return 'Sharpshooter'
    if d >= ELITE: return 'Lockdown Defender'
    if g >= ELITE: return 'Glass Cleaner'
    if pm >= ELITE: return 'Visionary'
    if po >= ELITE: return 'Post Scorer'
    if rp >= ELITE: return 'Shot Blocker'
    if sl >= ELITE: return 'Slasher'

    return None  # fall through to compositional


# Fallback compositional vocab (only used when no named archetype matched)
PRIMARY_FB = {
    'shoot': 'Sharpshooter', 'slash': 'Slasher', 'playmake': 'Playmaker',
    'defend': 'Lockdown', 'glass': 'Glass Cleaner', 'post': 'Post Scorer',
    'rim_protect': 'Rim Protector',
}
MODIFIER_FB = {
    'shoot': 'Sharpshooting', 'slash': 'Slashing', 'playmake': 'Diming',
    'defend': '2 Way', 'glass': 'Crashing', 'post': 'Bruising',
    'rim_protect': 'Shot-Blocking',
}


def _compose_label(atoms_pct, size, position):
    """atoms_pct is the per-player percentile dict (same scale 0-100 as
    _named_archetype uses). All thresholds below are percentile cutoffs."""
    main = ('shoot','slash','playmake','defend','glass','post','rim_protect')
    ranked = sorted(((k, atoms_pct.get(k, 0)) for k in main), key=lambda kv: -kv[1])
    primary_atom, primary_z = ranked[0]

    if primary_z < 50:
        return {'guard': 'Prospect', 'wing': 'Prospect', 'big': 'Prospect'}[size]
    if primary_z < FALLBACK_STRONG:
        # Below fallback threshold — mid-tier role labels (2K-flavored, position-aware)
        if size == 'guard':
            if position == 'PG': return 'Scrappy Point'
            return 'Scrappy Two Guard'
        if size == 'wing':
            return 'Scrappy Wing'
        return 'Skilled Big'

    # FALLBACK_STRONG ≤ primary_z < STRONG: light-named archetype (avoids "Scrappy" overflow)
    if primary_z < STRONG:
        if primary_atom == 'shoot':
            if size == 'guard': return 'Catch & Shoot Ace'
            if size == 'wing':  return 'Spot Up Threat'
            return 'Floor Spacer'
        if primary_atom == 'slash':
            return 'Lob Threat' if not is_big_size(size) else 'Energy Big'
        if primary_atom == 'playmake':
            return 'Pass First Point' if size == 'guard' else 'Secondary Ball Handler'
        if primary_atom == 'defend':
            if size == 'guard': return 'Junkyard Guard'
            if size == 'wing':  return 'Wing Stopper'
            return 'Hybrid Defender'
        if primary_atom == 'glass':
            if size == 'big':   return 'Rebounder'
            return 'Rebounding Wing'
        if primary_atom == 'post':
            return 'Interior Scorer'
        if primary_atom == 'rim_protect':
            return 'Paint Defender'
        # default
        return {'guard': 'Combo Guard', 'wing': 'Small Ball Wing', 'big': 'Skilled Big'}[size]

    # primary_z >= STRONG — full compositional name
    parts = []
    if atoms_pct.get('defend', 0) >= SOFT and primary_atom != 'defend':
        parts.append('2 Way')
    modifier_atom = None
    for atom, z in ranked[1:]:
        if z >= STRONG and atom != primary_atom and atom != 'defend':
            modifier_atom = atom; break
    if modifier_atom:
        parts.append(MODIFIER_FB[modifier_atom])
    parts.append(PRIMARY_FB[primary_atom])
    label = ' '.join(parts)
    if size == 'big' and atoms_pct.get('shoot', 0) >= STRONG and primary_atom != 'shoot' and 'Stretch' not in label and '2 Way' not in label:
        label = f'Stretch {label}'
    return label


def is_big_size(size):
    return size == 'big'


def classify(ratings, position, dim_stats=None, pid=None, league_leaders=None, pctiles=None):
    """Return the player's BASE build label (compositional/archetype).

    pctiles is the per-player percentile dict for this league (from
    league_pctiles_cached). Top-tier rules use it to enforce scarcity.
    """
    if all(ratings.get(k, 0) == 0 for k in _RATING_KEYS):
        return None
    # No league pctile context (e.g. free agents excluded from
    # _compute_player_percentiles): skip the build label rather than
    # mislabel everyone "Prospect".
    if not pctiles:
        return None
    atoms_z = _compute_atoms(ratings, dim_stats)  # still needed for mid_range and as fallback
    size = _size_tier(ratings, dim_stats, position)
    ovr = ratings.get('ovr', 0)
    elite_bar = dim_stats.get('_elite_ovr', 999) if dim_stats else 999
    star_bar = dim_stats.get('_star_ovr', 999) if dim_stats else 999
    skills = ratings.get('skills') or ()
    named = _named_archetype(atoms_z, size, position, ovr=ovr, elite_bar=elite_bar, star_bar=star_bar, pctiles=pctiles, skills=skills)
    if named:
        return named
    # Compose uses the same percentile scale — pass the per-player pctile dict
    return _compose_label(pctiles, size, position)


# Module-level cache, keyed by (id(export), season) — stored OUTSIDE the export
# dict so it doesn't get serialized into save_db() output. Bounded LRU so memory
# stays small even if many exports/seasons are queried over the bot's lifetime.
_BUILD_CACHE_LIMIT = 12  # ~12 entries across all exports * ~50KB each = ~600KB ceiling
_DIM_STATS_CACHE = {}    # {(id_export, season_key): dim_stats}
_PCTILES_CACHE = {}      # {(id_export, season_key): pctiles_by_pid}
_DIST_CACHE = {}         # {(id_export, season_key): pool_distributions}


def _lru_get(cache, key):
    if key in cache:
        cache[key] = cache.pop(key)  # bump to end
        return cache[key]
    return None


def _lru_put(cache, key, value, limit):
    cache[key] = value
    while len(cache) > limit:
        try:
            oldest = next(iter(cache))
            cache.pop(oldest, None)
        except StopIteration:
            break


def league_dim_stats_cached(export, season=None):
    """Cache league baselines per (export, season)."""
    if export is None:
        return None
    key = (id(export), season if season is not None else 'current')
    cached = _lru_get(_DIM_STATS_CACHE, key)
    if cached is not None:
        return cached
    stats = _league_dim_stats(export.get('players', []), season=season)
    if stats is not None:
        _lru_put(_DIM_STATS_CACHE, key, stats, _BUILD_CACHE_LIMIT)
    return stats


def league_pctiles_cached(export, season=None):
    """Cache per-player percentile ranks per (export, season)."""
    if export is None:
        return None
    key = (id(export), season if season is not None else 'current')
    cached = _lru_get(_PCTILES_CACHE, key)
    if cached is not None:
        return cached
    dim_stats = league_dim_stats_cached(export, season)
    if dim_stats is None:
        return None
    pctiles = _compute_player_percentiles(export.get('players', []), dim_stats, season=season)
    if pctiles is not None:
        _lru_put(_PCTILES_CACHE, key, pctiles, _BUILD_CACHE_LIMIT)
    return pctiles


def league_distributions_cached(export, season=None):
    """Cache per-key pool distributions per (export, season), for ranking
    off-pool players (free agents) against the signed-player population."""
    if export is None:
        return None
    key = (id(export), season if season is not None else 'current')
    cached = _lru_get(_DIST_CACHE, key)
    if cached is not None:
        return cached
    dim_stats = league_dim_stats_cached(export, season)
    if dim_stats is None:
        return None
    dist = _pool_distributions(export.get('players', []), dim_stats, season=season)
    if dist:
        _lru_put(_DIST_CACHE, key, dist, _BUILD_CACHE_LIMIT)
    return dist


def _purge_legacy_export_caches(export):
    """Strip any old in-dict caches that earlier versions wrote into the export.

    These bloated the saved JSON file by tens of MBs. Call once when an export
    is loaded so we don't carry forward the bloat.
    """
    if export is None:
        return
    for legacy_key in (
        '_build_zscore_stats',
        '_build_zscore_stats_cache',
        '_build_league_leaders',
        '_build_league_leaders_cache',
        '_build_pctiles_cache',
    ):
        export.pop(legacy_key, None)


def count_league_builds(players):
    dim_stats = _league_dim_stats(players)
    pctiles_by_pid = _compute_player_percentiles(players, dim_stats)
    counts = {}
    # Iterate the same ranking pool the percentiles are computed over
    # (signed players), so the distribution matches the percentile baseline.
    for p, r in _ranking_pool(players):
        position = r.get('pos', '')
        pid = p.get('pid')
        tag = classify(r, position, dim_stats=dim_stats, pctiles=pctiles_by_pid.get(pid))
        if tag is None:
            continue
        counts[tag] = counts.get(tag, 0) + 1
    return counts
