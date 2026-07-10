import shared_info
serversList = shared_info.serversList
import basics
import pull_info

# Coaches are a just-for-fun layer on top of the BBGM export. GMs can appoint one
# of their own roster players (a player-coach) or a retired player to coach their
# team; while a coach is assigned, their team's record accrues onto the coach.
#
# Eligibility: only a player on the GM's own team, or a retired player. You cannot
# hire another team's active player, a free agent, or a draft prospect.
#
# Storage lives in servers.json under serversList[serverId]['coaches'], keyed by
# str(pid). Committed (career) totals plus a baseline snapshot of the team's
# cumulative numbers at hire time; live stats = committed + (cumulative now - base):
#   {
#     "name": "Gary Harrison", "tid": 17,
#     "won": 50, "lost": 30,                 # committed regular-season record
#     "rings": 1, "seriesWon": 6, "playoffApps": 3,
#     "baseWon": 120, "baseLost": 80,        # team cumulative at hire (tid >= 0 only)
#     "baseRings": 2, "baseSeriesWon": 9, "basePlayoffApps": 4
#   }
# Playoff series losses are derived (appearances - rings), so they aren't stored.

RING = "\U0001F48D"  # 💍


def _get_coaches(serverId):
    server = serversList[serverId]
    if 'coaches' not in server:
        server['coaches'] = {}
    return server['coaches']


def _find_team(export, tid):
    for t in export['teams']:
        if t['tid'] == tid:
            return t
    return None


def _is_retired(player):
    try:
        return int(player.get('tid')) == -3
    except (TypeError, ValueError):
        return False


def _player_is_retired(export, pid):
    """True only if this coach's underlying player is currently retired in the
    export — i.e. actually hireable as a coach (active players are not)."""
    for p in export['players']:
        if str(p.get('pid')) == str(pid):
            return _is_retired(p)
    return False


def _playoff_games(export, tid):
    """Franchise all-time playoff GAME record (won, lost) from headToHeads.

    headToHeads stores each franchise pair once, with the lower tid as the
    outer key, so a team's full record is its own outer row PLUS the inverted
    entries where it appears as an inner (opponent) key. Returns (0, 0) when
    the export has no headToHeads data (some exports strip it)."""
    tid = str(tid)
    won = lost = 0
    for entry in export.get('headToHeads') or []:
        po = entry.get('playoffs') or {}
        for _opp, rec in (po.get(tid) or {}).items():
            won += rec.get('won', 0)
            lost += rec.get('lost', 0)
        for outer, row in po.items():
            if outer == tid:
                continue
            rec = row.get(tid)
            if rec:
                won += rec.get('lost', 0)   # inverted: opp's losses are our wins
                lost += rec.get('won', 0)
    return won, lost


def _team_cum(team, export):
    """Franchise all-time totals — all monotonic as seasons/playoffs progress.

    Championships use pull_info.playoff_result (the same helper -history uses),
    so ring detection handles both numGamesPlayoffSeries storage formats and
    stays consistent with the rest of the bot. Playoff game W-L comes from
    headToHeads (see _playoff_games).
    """
    won = lost = seriesWon = playoffApps = rings = 0
    playoffSettings = export['gameAttributes']['numGamesPlayoffSeries']
    for s in team['seasons']:
        won += s.get('won', 0)
        lost += s.get('lost', 0)
        prw = s.get('playoffRoundsWon', -1)
        if prw is not None and prw >= 0:
            playoffApps += 1
            seriesWon += prw
            if pull_info.playoff_result(prw, playoffSettings, s.get('season')) == '**won championship**':
                rings += 1
    poGW, poGL = _playoff_games(export, team['tid'])
    return {'won': won, 'lost': lost, 'seriesWon': seriesWon,
            'playoffApps': playoffApps, 'rings': rings, 'poGW': poGW, 'poGL': poGL}


def _coach_stats(coach, export):
    """Live career stats: committed plus pending from any active assignment."""
    won = coach.get('won', 0)
    lost = coach.get('lost', 0)
    rings = coach.get('rings', 0)
    seriesWon = coach.get('seriesWon', 0)
    playoffApps = coach.get('playoffApps', 0)
    poGW = coach.get('poGW', 0)
    poGL = coach.get('poGL', 0)
    tid = coach.get('tid', -1)
    if tid is not None and tid >= 0:
        team = _find_team(export, tid)
        if team is not None:
            cum = _team_cum(team, export)
            won += max(0, cum['won'] - coach.get('baseWon', cum['won']))
            lost += max(0, cum['lost'] - coach.get('baseLost', cum['lost']))
            rings += max(0, cum['rings'] - coach.get('baseRings', cum['rings']))
            seriesWon += max(0, cum['seriesWon'] - coach.get('baseSeriesWon', cum['seriesWon']))
            playoffApps += max(0, cum['playoffApps'] - coach.get('basePlayoffApps', cum['playoffApps']))
            poGW += max(0, cum['poGW'] - coach.get('basePoGW', cum['poGW']))
            poGL += max(0, cum['poGL'] - coach.get('basePoGL', cum['poGL']))
    seriesLost = max(0, playoffApps - rings)
    return {'won': won, 'lost': lost, 'rings': rings, 'seriesWon': seriesWon,
            'playoffApps': playoffApps, 'seriesLost': seriesLost,
            'poGW': poGW, 'poGL': poGL}


def _coach_team_record(coach, export, tid):
    """A coach's record with one specific team: banked stints plus, if they're
    coaching it right now, the live pending stint."""
    base = coach.get('teams', {}).get(str(tid), {})
    won = base.get('won', 0)
    lost = base.get('lost', 0)
    rings = base.get('rings', 0)
    if coach.get('tid', -1) == tid:
        team = _find_team(export, tid)
        if team is not None:
            cum = _team_cum(team, export)
            won += max(0, cum['won'] - coach.get('baseWon', cum['won']))
            lost += max(0, cum['lost'] - coach.get('baseLost', cum['lost']))
            rings += max(0, cum['rings'] - coach.get('baseRings', cum['rings']))
    return {'won': won, 'lost': lost, 'rings': rings}


def top_team_coaches(coachData, export, tid, n=3):
    """Top-n coaches for a team by total wins with that team (wins+losses > 0)."""
    rows = []
    for pid, c in coachData.items():
        rec = _coach_team_record(c, export, tid)
        if rec['won'] + rec['lost'] > 0:
            rows.append((c['name'], rec['won'], rec['lost'], rec['rings']))
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:n]


def _record_str(st):
    """Compact one-liner: regular-season record then playoff GAME record.

    e.g. '45-30 · Playoffs 18-12'. Coaches who made the playoffs but whose
    game W-L is unavailable (no headToHeads) still read 'made playoffs'.
    Championship count is intentionally omitted here — coaches sort by rings,
    but the list stays clean. Rings live on the coach card."""
    base = f"{st['won']}-{st['lost']}"
    if st['poGW'] + st['poGL'] > 0:
        return f"{base} · Playoffs {st['poGW']}-{st['poGL']}"
    if st['playoffApps'] > 0:
        return f"{base} · made playoffs"
    if st['won'] + st['lost'] > 0:
        return f"{base} · missed playoffs"
    return base


def _stat_block(st):
    """Multi-line block for hire/fire confirmations."""
    lines = [f"Regular season: {st['won']}-{st['lost']}"]
    if st['poGW'] + st['poGL'] > 0:
        lines.append(f"Playoff games: {st['poGW']}-{st['poGL']} (W-L)")
    elif st['playoffApps'] > 0:
        lines.append("Playoffs: made it")
    else:
        lines.append("Playoffs: none")
    lines.append(f"Championships: {st['rings']} {RING * st['rings']}".rstrip())
    return '\n'.join(lines)


def _add_lines(embed, title, lines):
    """Add lines to the embed, chunking so no field exceeds Discord's 1024 cap."""
    if not lines:
        return
    name = title
    chunk = ''
    for line in lines:
        if len(chunk) + len(line) + 1 > 1000:
            embed.add_field(name=name, value=chunk, inline=False)
            chunk = ''
            name = '​'  # continuation field, blank header
        chunk += line + '\n'
    if chunk:
        embed.add_field(name=name, value=chunk, inline=False)


async def coaches(embed, text, commandInfo):
    serverId = commandInfo['serverId']
    export = shared_info.serverExports[serverId]
    coachData = _get_coaches(serverId)

    mode = 'all'
    if len(text) > 1:
        mode = str.lower(text[1])
    if mode not in ('all', 'hired', 'available'):
        mode = 'all'

    teamName = {t['tid']: pull_info.tinfo(t)['name'] for t in export['teams']}

    if mode == 'hired':
        embed.title = 'Hired Coaches'
        byTeam = {}
        for pid, c in coachData.items():
            tid = c.get('tid', -1)
            if tid is not None and tid >= 0:
                byTeam[tid] = c
        if not byTeam:
            embed.add_field(name='No coaches hired',
                            value='No teams currently have a coach. GMs can use `hirecoach [player]`.',
                            inline=False)
            return embed
        lines = []
        for tid in sorted(byTeam):
            st = _coach_stats(byTeam[tid], export)
            lines.append(f"**{teamName.get(tid, 'Team ' + str(tid))}** — {byTeam[tid]['name']} ({_record_str(st)})")
        _add_lines(embed, 'Teams & Coaches', lines)
        return embed

    if mode == 'available':
        embed.title = 'Available Coaches'
        rows = []
        for pid, c in coachData.items():
            tid = c.get('tid', -1)
            # Not currently coaching AND still a retired player (so actually
            # hireable — active players can't be hired as coaches).
            if (tid is None or tid < 0) and _player_is_retired(export, pid):
                rows.append((c['name'], _coach_stats(c, export)))
        if not rows:
            embed.add_field(name='None available',
                            value='No coaches are currently between jobs.',
                            inline=False)
            return embed
        rows.sort(key=lambda r: (r[1]['rings'], r[1]['won']), reverse=True)
        lines = [f"{name}: {_record_str(st)}" for name, st in rows]
        _add_lines(embed, 'Free to hire', lines)
        return embed

    # mode == 'all' — every currently-hired coach (even 0-0) plus anyone with a record
    embed.title = 'Coaches'
    rows = []
    for pid, c in coachData.items():
        st = _coach_stats(c, export)
        tid = c.get('tid', -1)
        hired = tid is not None and tid >= 0
        hasRecord = st['won'] > 0 or st['lost'] > 0
        if hired or hasRecord:
            rows.append((c['name'], st, tid))
    if not rows:
        embed.add_field(name='No coaches yet',
                        value='No coaches have been hired yet. GMs can use `hirecoach [player]`.',
                        inline=False)
        return embed
    rows.sort(key=lambda r: (r[1]['rings'], r[1]['won']), reverse=True)
    lines = []
    for name, st, tid in rows:
        where = teamName.get(tid, 'Team ' + str(tid)) if (tid is not None and tid >= 0) else 'FA'
        lines.append(f"{name}: {_record_str(st)} ({where})")
    _add_lines(embed, 'All-time records', lines)
    return embed


async def hirecoach(embed, text, commandInfo):
    serverId = commandInfo['serverId']
    userTid = commandInfo['userTid']
    export = shared_info.serverExports[serverId]

    if userTid is None or userTid < 0:
        embed.add_field(name='Not a GM',
                        value="You need to be a team's GM to hire a coach.",
                        inline=False)
        return embed
    if len(text) < 2:
        embed.add_field(name='Who?',
                        value="Usage: `hirecoach [player name]`",
                        inline=False)
        return embed

    name = ' '.join(text[1:])
    # Only retired players can coach — match the name against retired players only
    # so a similarly-named active player can't be picked then rejected.
    pool = [p for p in export['players'] if _is_retired(p)]
    if not pool:
        embed.add_field(name='No retired players',
                        value="There are no retired players to hire as a coach.",
                        inline=False)
        return embed
    subExport = {'players': pool, 'gameAttributes': export['gameAttributes']}
    pid = basics.find_match(name, subExport, settings=serversList[serverId])
    player = None
    for p in pool:
        if p['pid'] == pid:
            player = p
            break
    if player is None:
        embed.add_field(name='No match',
                        value=f"Couldn't find a retired player matching `{name}`.",
                        inline=False)
        return embed
    playerName = player['firstName'] + ' ' + player['lastName']

    coachData = _get_coaches(serverId)

    # Can't hire someone who's already coaching a team.
    existing = coachData.get(str(pid))
    if existing and existing.get('tid', -1) is not None and existing.get('tid', -1) >= 0:
        team = _find_team(export, existing['tid'])
        tn = pull_info.tinfo(team)['name'] if team else 'another team'
        embed.add_field(name='Already coaching',
                        value=f"{playerName} is already the coach of the {tn}.",
                        inline=False)
        return embed

    # One coach per team — make them fire the current one first.
    for pid2, c in coachData.items():
        if c.get('tid', -1) == userTid:
            embed.add_field(name='Team already has a coach',
                            value=f"Your team already has **{c['name']}** as coach. Use `firecoach` first.",
                            inline=False)
            return embed

    team = _find_team(export, userTid)
    teamName = pull_info.tinfo(team)['name']
    cum = _team_cum(team, export)
    base = {'baseWon': cum['won'], 'baseLost': cum['lost'], 'baseRings': cum['rings'],
            'baseSeriesWon': cum['seriesWon'], 'basePlayoffApps': cum['playoffApps'],
            'basePoGW': cum['poGW'], 'basePoGL': cum['poGL']}

    if existing:
        existing['name'] = playerName
        existing['tid'] = userTid
        existing.update(base)
    else:
        coachData[str(pid)] = dict(
            name=playerName, tid=userTid,
            won=0, lost=0, rings=0, seriesWon=0, playoffApps=0, poGW=0, poGL=0,
            **base,
        )
    serversList[serverId]['coaches'] = coachData
    await basics.save_db(serversList)

    st = _coach_stats(coachData[str(pid)], export)
    embed.add_field(name='Coach Hired',
                    value=f"**{playerName}** is now the coach of the **{teamName}**.\n{_stat_block(st)}",
                    inline=False)
    return embed


async def firecoach(embed, text, commandInfo):
    serverId = commandInfo['serverId']
    userTid = commandInfo['userTid']
    export = shared_info.serverExports[serverId]

    if userTid is None or userTid < 0:
        embed.add_field(name='Not a GM',
                        value="You need to be a team's GM to fire a coach.",
                        inline=False)
        return embed

    coachData = _get_coaches(serverId)
    target = None
    for pid, c in coachData.items():
        if c.get('tid', -1) == userTid:
            target = c
            break
    team = _find_team(export, userTid)
    teamName = pull_info.tinfo(team)['name'] if team else 'your team'
    if target is None:
        embed.add_field(name='No coach',
                        value="Your team doesn't have a coach to fire.",
                        inline=False)
        return embed

    # Bank the pending stint onto this team's per-team record before releasing.
    if team is not None:
        cum = _team_cum(team, export)
        stintWon = max(0, cum['won'] - target.get('baseWon', cum['won']))
        stintLost = max(0, cum['lost'] - target.get('baseLost', cum['lost']))
        stintRings = max(0, cum['rings'] - target.get('baseRings', cum['rings']))
        teamRec = target.setdefault('teams', {}).setdefault(
            str(userTid), {'won': 0, 'lost': 0, 'rings': 0})
        teamRec['won'] += stintWon
        teamRec['lost'] += stintLost
        teamRec['rings'] += stintRings

    # Commit the pending stint onto the coach's career totals before releasing.
    st = _coach_stats(target, export)
    target['won'] = st['won']
    target['lost'] = st['lost']
    target['rings'] = st['rings']
    target['seriesWon'] = st['seriesWon']
    target['playoffApps'] = st['playoffApps']
    target['poGW'] = st['poGW']
    target['poGL'] = st['poGL']
    target['tid'] = -1
    for k in ('baseWon', 'baseLost', 'baseRings', 'baseSeriesWon', 'basePlayoffApps',
              'basePoGW', 'basePoGL'):
        target.pop(k, None)
    serversList[serverId]['coaches'] = coachData
    await basics.save_db(serversList)

    embed.add_field(name='Coach Fired',
                    value=f"**{target['name']}** is no longer the coach of the **{teamName}**.\n{_stat_block(st)}",
                    inline=False)
    return embed
