import pandas as pd
import numpy as np
import os

# Matching features. We deliberately match on pace-adjusted efficiency (ortg/drtg)
# and pace itself rather than raw ppg/opp_ppg — raw scoring tracks era/pace more than
# team identity, so a high-scoring sim team would otherwise always glom onto high-pace
# eras regardless of how good it actually is. ortg/drtg = points per 100 possessions.
STAT_COLS = ['ortg', 'drtg', 'pace', 'tp_attempts_pg', 'fg_pct', 'tp_pct', 'apg', 'tov_pg', 'rpg']
#                ortg  drtg  pace  3PA   fg%   3p%   apg   tov   rpg
WEIGHTS = np.array([1.7, 1.7, 1.3, 1.0, 0.7, 0.7, 0.9, 0.8, 0.8])

# Raw CSV columns we coerce to numeric before deriving ortg/drtg.
_RAW_NUMERIC = ['ppg', 'opp_ppg', 'pace', 'tp_attempts_pg', 'fg_pct', 'tp_pct', 'apg', 'tov_pg', 'rpg']

# Full team name (as it appears in the team-season CSV) -> 3-letter abbrev used in
# the player-season CSV. Covers every franchise that appears in either CSV from 1990+.
TEAM_NAME_TO_ABBREV = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BRK', 'New Jersey Nets': 'NJN',
    'Charlotte Hornets': 'CHO', 'Charlotte Bobcats': 'CHA',
    'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET', 'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM', 'Vancouver Grizzlies': 'VAN',
    'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP', 'New Orleans Hornets': 'NOH',
    'New Orleans/Oklahoma City Hornets': 'NOK',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC', 'Seattle SuperSonics': 'SEA',
    'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHO', 'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS', 'Washington Bullets': 'WSB',
}

_df = None
_z_matrix = None
_means = None
_stds = None
_stars_by_key = {}  # (season:int, abbrev:str) -> "Star1 / Star2"


def _load_stars(team_df):
    """Compute top-2 PPG players per (season, team_abbrev) from the player CSV."""
    global _stars_by_key
    player_path = os.path.join(os.path.dirname(__file__), 'static', 'nba_player_seasons.csv')
    if not os.path.exists(player_path):
        return
    p = pd.read_csv(player_path, usecols=['season', 'team', 'player', 'g', 'pts_per_game'])
    # Skip multi-team rows
    p = p[~p['team'].astype(str).str.match(r'^\d?TOT$|^\d+TM$|^TOT$', na=False)]
    p['g'] = pd.to_numeric(p['g'], errors='coerce').fillna(0)
    p['ppg'] = pd.to_numeric(p['pts_per_game'], errors='coerce').fillna(0)
    p = p[p['g'] >= 30]
    # Top 2 scorers per (season, team)
    p = p.sort_values(['season', 'team', 'ppg'], ascending=[True, True, False])
    out = {}
    for (season, abbrev), group in p.groupby(['season', 'team']):
        top = group.head(2)['player'].tolist()
        if top:
            out[(int(season), str(abbrev))] = ' / '.join(top)
    _stars_by_key = out


def load():
    global _df, _z_matrix, _means, _stds
    path = os.path.join(os.path.dirname(__file__), 'static', 'nba_team_seasons.csv')
    df = pd.read_csv(path)

    df = df[pd.to_numeric(df['g'], errors='coerce').fillna(0) >= 50]

    for col in _RAW_NUMERIC:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['srs'] = pd.to_numeric(df.get('srs'), errors='coerce').fillna(0)

    # Need a real pace to pace-adjust scoring; drop the handful of old seasons with no pace.
    df = df[df['pace'] > 0]
    df['ortg'] = df['ppg'] / df['pace'] * 100
    df['drtg'] = df['opp_ppg'] / df['pace'] * 100

    df['abbrev'] = df['team'].map(TEAM_NAME_TO_ABBREV)
    _df = df.reset_index(drop=True)

    stats = _df[STAT_COLS].values.astype(float)
    _means = stats.mean(axis=0)
    _stds = stats.std(axis=0)
    _stds[_stds == 0] = 1
    _z_matrix = (stats - _means) / _stds

    _load_stars(_df)


def find_similar_teams(bbgm_team_stats, top_n=2):
    """Find the top_n most statistically similar real NBA team-seasons.

    bbgm_team_stats: dict with keys matching STAT_COLS.
                     Percentages on 0-100 scale.
    Returns list of dicts with team, season, wins, losses, key stats, distance, stars.
    """
    if _df is None:
        return []

    vec = np.array([float(bbgm_team_stats.get(c, 0)) for c in STAT_COLS])
    z_vec = (vec - _means) / _stds
    diffs = _z_matrix - z_vec
    distances = np.sqrt(np.sum(WEIGHTS * diffs ** 2, axis=1))
    indices = np.argsort(distances)[:top_n]

    results = []
    for i in indices:
        row = _df.iloc[i]
        abbrev = row.get('abbrev') if pd.notna(row.get('abbrev')) else None
        stars = _stars_by_key.get((int(row['season']), abbrev)) if abbrev else None
        # Calibrated similarity: identical profile = 100%, decaying with weighted
        # z-distance. Scale tuned to the dataset's nearest-neighbor distances so a
        # tight comp (~0.75) reads ~88% and a loose one (~2.0) ~70% — keeps the top
        # comps differentiated instead of all pinning at 100% (which a raw
        # closer-than-X%-of-teams percentile does, since NN distances are tiny).
        match_pct = round(100 * float(np.exp(-distances[i] / 5.5)))
        results.append({
            'team': row['team'],
            'abbrev': abbrev,
            'season': int(row['season']),
            'wins': int(row['wins']) if pd.notna(row.get('wins')) else None,
            'losses': int(row['losses']) if pd.notna(row.get('losses')) else None,
            'distance': float(distances[i]),
            'match_pct': match_pct,
            'stars': stars,
            'ppg': float(row['ppg']),
            'opp_ppg': float(row['opp_ppg']),
            'ortg': float(row['ortg']),
            'drtg': float(row['drtg']),
            'pace': float(row['pace']),
            'srs': float(row['srs']) if pd.notna(row.get('srs')) else None,
            'fg_pct': float(row['fg_pct']),
            'tp_pct': float(row['tp_pct']),
            'apg': float(row['apg']),
            'rpg': float(row['rpg']),
            'tov_pg': float(row['tov_pg']),
            'tp_attempts_pg': float(row['tp_attempts_pg']),
        })
    return results
