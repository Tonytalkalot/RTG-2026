"""One-off scraper: fetch per-game team + opponent stats from Basketball Reference for each season 1990+.

Writes static/nba_team_seasons.csv with one row per team-season.

Run: python scripts/scrape_nba_teams.py

Be polite — sleeps 4s between requests (BR's rate limit is ~20/min on the public site).
"""
import os
import sys
import time
import io
import re
import urllib.request
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), '..', 'static', 'nba_team_seasons.csv')
START = 1990
END = 2026  # inclusive
HEADERS = {'User-Agent': 'Mozilla/5.0 (eldobot-team-data/1.0)'}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='ignore')


def parse_table(html, table_id):
    """BR hides some tables in HTML comments. Strip the comment markers, then let pandas find the table by id."""
    cleaned = html.replace('<!--', '').replace('-->', '')
    m = re.search(rf'<table[^>]*id="{re.escape(table_id)}"[^>]*>.*?</table>', cleaned, re.DOTALL)
    if not m:
        return None
    return pd.read_html(io.StringIO(m.group(0)))[0]


def normalize(df):
    """Flatten multi-index columns if any, lowercase."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[1] if c[1] and not str(c[1]).startswith('Unnamed') else c[0] for c in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def scrape_season(year):
    url = f'https://www.basketball-reference.com/leagues/NBA_{year}.html'
    html = fetch(url)

    team = parse_table(html, 'per_game-team')
    opp = parse_table(html, 'per_game-opponent')
    standings = parse_table(html, 'expanded_standings') or parse_table(html, 'advanced-team')

    if team is None or opp is None:
        print(f'  WARN {year}: missing per_game tables, skipping')
        return None

    team = normalize(team)
    opp = normalize(opp)

    # BR includes "League Average" rows — strip
    team = team[team['Team'].astype(str).str.strip().str.lower() != 'league average']
    opp = opp[opp['Team'].astype(str).str.strip().str.lower() != 'league average']

    # Strip trailing "*" from team names (playoff marker)
    team['team_clean'] = team['Team'].astype(str).str.replace('*', '', regex=False).str.strip()
    opp['team_clean'] = opp['Team'].astype(str).str.replace('*', '', regex=False).str.strip()

    # Pull what we need
    cols_team = {
        'team_clean': 'team',
        'G': 'g',
        'PTS': 'ppg',
        'TRB': 'rpg',
        'AST': 'apg',
        'TOV': 'tov_pg',
        '3PA': 'tp_attempts_pg',
        'FG%': 'fg_pct',
        '3P%': 'tp_pct',
        'FT%': 'ft_pct',
    }
    cols_opp = {'team_clean': 'team', 'PTS': 'opp_ppg'}

    missing_t = [c for c in cols_team if c not in team.columns]
    missing_o = [c for c in cols_opp if c not in opp.columns]
    if missing_t or missing_o:
        print(f'  WARN {year}: missing cols team={missing_t} opp={missing_o}')
        return None

    t = team[list(cols_team)].rename(columns=cols_team)
    o = opp[list(cols_opp)].rename(columns=cols_opp)
    merged = t.merge(o, on='team', how='inner')
    merged['season'] = year

    # Advanced (SRS, pace, W, L)
    adv = parse_table(html, 'advanced-team')
    if adv is not None:
        adv = normalize(adv)
        adv = adv[adv['Team'].astype(str).str.strip().str.lower() != 'league average']
        adv['team_clean'] = adv['Team'].astype(str).str.replace('*', '', regex=False).str.strip()
        keep = {'team_clean': 'team'}
        for src, dst in (('W', 'wins'), ('L', 'losses'), ('SRS', 'srs'), ('Pace', 'pace')):
            if src in adv.columns:
                keep[src] = dst
        a = adv[list(keep)].rename(columns=keep)
        merged = merged.merge(a, on='team', how='left')
    else:
        merged['wins'] = pd.NA
        merged['losses'] = pd.NA
        merged['srs'] = pd.NA
        merged['pace'] = pd.NA

    # Convert percentages 0-1 -> 0-100 to match nba_data.py
    for c in ('fg_pct', 'tp_pct', 'ft_pct'):
        merged[c] = pd.to_numeric(merged[c], errors='coerce') * 100

    out_cols = ['season', 'team', 'wins', 'losses', 'g', 'ppg', 'opp_ppg',
                'fg_pct', 'tp_pct', 'ft_pct', 'rpg', 'apg', 'tov_pg',
                'tp_attempts_pg', 'pace', 'srs']
    for c in out_cols:
        if c not in merged.columns:
            merged[c] = pd.NA
    return merged[out_cols]


def main():
    all_rows = []
    for year in range(START, END + 1):
        print(f'Scraping {year}...')
        try:
            df = scrape_season(year)
            if df is not None:
                all_rows.append(df)
                print(f'  {len(df)} teams')
        except Exception as e:
            print(f'  ERROR {year}: {e}')
        time.sleep(4)

    if not all_rows:
        print('No data scraped, aborting.')
        sys.exit(1)

    out = pd.concat(all_rows, ignore_index=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f'Wrote {len(out)} rows to {OUT}')


if __name__ == '__main__':
    main()
