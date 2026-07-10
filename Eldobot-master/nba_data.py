import pandas as pd
import numpy as np
import os

STAT_COLS = ['ppg', 'rpg', 'apg', 'spg', 'bpg', 'tov', 'mpg', 'fg_pct', 'tp_pct', 'ft_pct']
WEIGHTS = np.array([1.5, 1.0, 1.2, 0.8, 0.8, 0.5, 0.7, 0.8, 1.0, 0.5])

_df = None
_z_matrix = None
_means = None
_stds = None


def load():
    global _df, _z_matrix, _means, _stds
    path = os.path.join(os.path.dirname(__file__), 'static', 'nba_player_seasons.csv')
    df = pd.read_csv(path)

    # Filter: modern era, minimum games
    df = df[df['season'] >= 1990]
    df = df[df['g'] >= 20]

    # Rename columns to our standard names
    df = df.rename(columns={
        'pts_per_game': 'ppg',
        'trb_per_game': 'rpg',
        'ast_per_game': 'apg',
        'stl_per_game': 'spg',
        'blk_per_game': 'bpg',
        'tov_per_game': 'tov',
        'mp_per_game': 'mpg',
        'fg_percent': 'fg_pct',
        'x3p_percent': 'tp_pct',
        'ft_percent': 'ft_pct',
    })

    # Convert percentages from 0-1 to 0-100 to match BBGM scale
    for col in ['fg_pct', 'tp_pct', 'ft_pct']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) * 100

    # Fill any remaining NaN stat values with 0
    for col in STAT_COLS:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    _df = df.reset_index(drop=True)

    # Pre-compute z-score normalization
    stats = _df[STAT_COLS].values.astype(float)
    _means = stats.mean(axis=0)
    _stds = stats.std(axis=0)
    _stds[_stds == 0] = 1
    _z_matrix = (stats - _means) / _stds


def find_similar(bbgm_stats, top_n=3):
    """Find the top_n most statistically similar real NBA player-seasons.

    bbgm_stats: dict with keys matching STAT_COLS (ppg, rpg, apg, etc.)
                Percentages should be 0-100 scale.
    Returns list of dicts with player, season, team, distance, and key stats.
    """
    if _df is None:
        return []

    vec = np.array([float(bbgm_stats.get(c, 0)) for c in STAT_COLS])
    z_vec = (vec - _means) / _stds
    diffs = _z_matrix - z_vec
    distances = np.sqrt(np.sum(WEIGHTS * diffs ** 2, axis=1))
    indices = np.argsort(distances)[:top_n]

    results = []
    for i in indices:
        row = _df.iloc[i]
        results.append({
            'player': row['player'],
            'season': int(row['season']),
            'team': row['team'],
            'distance': float(distances[i]),
            'ppg': row['ppg'],
            'rpg': row['rpg'],
            'apg': row['apg'],
            'spg': row['spg'],
            'bpg': row['bpg'],
            'fg_pct': row['fg_pct'],
            'tp_pct': row['tp_pct'],
            'ft_pct': row['ft_pct'],
        })
    return results
