import pandas as pd
import numpy as np
import os

STAT_COLS = ['Cmp','Att','Pct','Yds','TD','Int','Rush','Tgt','Rec','PBW','PBA','PBWR','RBW','RBA','RBWR','SkAlw','SkAlw%','FGM','FGA','Pct','Lng','XPM','XPA','Pct','Tck','Sk','PD','Int','FF','FR']
WEIGHTS = np.array([1.5, 1.0, 1.2, 0.8, 0.8, 0.5, 0.7, 0.8, 1.0, 0.5])

_df = None
_z_matrix = None
_means = None
_stds = None


def load():
    global _df, _z_matrix, _means, _stds
    path = os.path.join(os.path.dirname(__file__), 'static', 'nfl_player_seasons.csv')
    df = pd.read_csv(path)

    # Filter: modern era, minimum games
    df = df[df['season'] >= 1990]
    df = df[df['g'] >= 20]

    # Rename columns to our standard names
    df = df.rename(columns={
        'Cmp_per_game': 'Cmp',
        'Att_per_game': 'Att',
        'Pct_per_game': 'FGPct',
        'Yds_per_game': 'Yds',
        'TD_per_game': 'TD',
        'Int_per_game': 'Int',
        'Rush_per_game': 'Rush',
        'Tgt_per_game': 'Tgt',
        'Rec_per_game': 'Rec',
        'PBW_per_game': 'PBW',
        'PBA_per_game': 'PBA',
        'PBWR_per_game': 'PBWR',
        'RBW_per_game': 'RBW',
        'RBA_per_game': 'RBA',
        'RBWR_per_game': 'RBWR',
        'SkAlw%_per_game': 'SkAlw%',
        'FGM_per_game': 'FGM',
        'FGA_per_game': 'FGA',
        'PD_per_game': 'PD',
        'Int_per_game': 'Int',
        'FF_per_game': 'FF',
        'FR_per_game': 'FR',
        'XPM_per_game': 'XPM',
        'XPA_per_game': 'XPA',
        'Pct_pct': 'XPPct',
        'Tck_per_game': 'Tck',
        'Sk_per_game': 'Sk',
        
    })

    # Convert percentages from 0-1 to 0-100 to match FBGM scale
    for col in ['Pct_pct', 'Pct_per_game']:
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
    """Find the top_n most statistically similar real NFL player-seasons.

    bbgm_stats: dict with keys matching STAT_COLS ('Cmp', 'Att', 'Pct',' Yds',' TD', 'Int', 'Rush', 'Tgt', 'Rec', 'PBW', 'PBA', 'PBWR', 'RBW', 'RBA', 'RBWR', 'SkAlw', 'SkAlw%', 'FGM', 'FGA', 'Pct', 'Lng', 'XPM', 'XPA', 'Pct', 'Tck', 'Sk', 'PD', 'Int', 'FF', 'FR' etc.)
                Percentages should be 0-100 scale.
    Returns list of dicts with player, season, team, distance, and key stats.
    """
    if _df is None:
        return []

    vec = np.array([float(fbgm_stats.get(c, 0)) for c in STAT_COLS])
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
        'Cmp_per_game': row ['Cmp'],
        'Att_per_game': row ['Att'],
        'Pct_per_game': row ['FGPct'],
        'Yds_per_game': row ['Yds'],
        'TD_per_game': row ['TD'],
        'Int_per_game': row ['Int'],
        'Rush_per_game': row ['Rush'],
        'Tgt_per_game': row ['Tgt'],
        'Rec_per_game': row ['Rec'],
        'PBW_per_game': row ['PBW'],
        'PBA_per_game': row ['PBA'],
        'PBWR_per_game': row ['PBWR'],
        'RBW_per_game': row ['RBW'],
        'RBA_per_game': row ['RBA'],
        'RBWR_per_game': row ['RBWR'],
        'SkAlw%_per_game': row ['SkAlw%'],
        'FGM_per_game': row ['FGM'],
        'FGA_per_game': row ['FGA'],
        'PD_per_game': row ['PD'],
        'Int_per_game': row ['Int'],
        'FF_per_game': row ['FF'],
        'FR_per_game': row ['FR]',
        'XPM_per_game': row ['XPM'],
        'XPA_per_game': row ['XPA'],
        'Pct_pct': row ['XPPct'],
        'Tck_per_game': row ['Tck'],
        'Sk_per_game': row ['Sk'],
        })
    return results
