import shared_info
from shared_info import serversList
import basics
import discord
import autopilot


VALID_POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C']
POSITION_ALIASES = {'G': ['PG', 'SG'], 'F': ['SF', 'PF']}


def get_tradeable_players(export, tid):
    """Get all tradeable players on a team with their values."""
    season = export['gameAttributes']['season']
    phase = export['gameAttributes']['phase']
    players = []
    for p in export['players']:
        if p['tid'] != tid or not p.get('ratings'):
            continue
        if p.get('gamesUntilTradable', 0) > 0:
            continue
        # Expiring contracts can't be traded during draft phase
        if phase in [3, 4, 5, 6] and p['contract']['exp'] == season:
            continue
        r = p['ratings'][-1]
        value = autopilot.calculate_player_pick_value(p, export)
        players.append({
            'pid': p['pid'],
            'type': 'player',
            'name': p['firstName'] + ' ' + p['lastName'],
            'pos': r.get('pos', '?'),
            'ovr': r.get('ovr', 0),
            'pot': r.get('pot', 0),
            'age': season - p['born']['year'],
            'salary': p['contract']['amount'] / 1000,
            'contract_exp': p['contract']['exp'],
            'value': value,
            'player_obj': p
        })
    return players


def get_tradeable_picks(export, tid):
    """Get all draft picks owned by a team with their values."""
    picks = []
    teams = export['teams']
    for dp in export['draftPicks']:
        if dp['tid'] != tid:
            continue
        value = autopilot.calculate_pick_value(dp, export)
        # Get original team abbrev
        orig_abbrev = ''
        for t in teams:
            if t['tid'] == dp['originalTid']:
                orig_abbrev = t['abbrev']
        if dp['originalTid'] != dp['tid']:
            descrip = f"{dp['season']} round {dp['round']} pick ({orig_abbrev})"
        else:
            descrip = f"{dp['season']} round {dp['round']} pick"
        picks.append({
            'dpid': dp['dpid'],
            'type': 'draftPick',
            'descrip': descrip,
            'season': dp['season'],
            'round': dp['round'],
            'originalTid': dp['originalTid'],
            'value': value
        })
    return picks


def find_target_players(export, my_tid, position):
    """Find players on other teams matching position filter."""
    season = export['gameAttributes']['season']
    # Expand position aliases
    if position in POSITION_ALIASES:
        positions = POSITION_ALIASES[position]
    elif position:
        positions = [position.upper()]
    else:
        positions = None

    targets = []
    for p in export['players']:
        if p['tid'] < 0 or p['tid'] == my_tid or not p.get('ratings'):
            continue
        if p.get('gamesUntilTradable', 0) > 0:
            continue
        r = p['ratings'][-1]
        pos = r.get('pos', '?')
        if positions and pos not in positions:
            continue
        # Skip low-value players (pot < 50)
        if r.get('pot', 0) < 50:
            continue
        value = autopilot.calculate_player_pick_value(p, export)
        targets.append({
            'pid': p['pid'],
            'type': 'player',
            'name': p['firstName'] + ' ' + p['lastName'],
            'tid': p['tid'],
            'pos': pos,
            'ovr': r.get('ovr', 0),
            'pot': r.get('pot', 0),
            'age': season - p['born']['year'],
            'salary': p['contract']['amount'] / 1000,
            'contract_exp': p['contract']['exp'],
            'value': value,
            'player_obj': p
        })
    return targets


def validate_trade_salary(my_tid, other_tid, outgoing, incoming, export, server_id):
    """Check if a trade package passes salary validation for both teams."""
    settings = serversList[str(server_id)]
    salary_cap = export['gameAttributes']['salaryCap'] / 1000
    hard_cap = float(settings.get('hardcap', 200))
    players = export['players']

    for tid, sending, receiving in [(my_tid, outgoing, incoming), (other_tid, incoming, outgoing)]:
        # Calculate current payroll
        payroll = 0
        for p in players:
            if p['tid'] == tid:
                payroll += p['contract']['amount'] / 1000

        salary_out = sum(a['salary'] for a in sending if a['type'] == 'player')
        salary_in = sum(a['salary'] for a in receiving if a['type'] == 'player')

        ending_payroll = payroll - salary_out + salary_in
        if ending_payroll > hard_cap:
            return False

        # 125% rule: if over cap, incoming salary can't exceed 125% of outgoing
        if ending_payroll > salary_cap and salary_out > 0 and salary_in > 0:
            if salary_in / salary_out > 1.259:
                return False

    return True


def find_trade_packages(my_players, my_picks, target, export, my_tid, server_id):
    """Find fair trade packages for a target player. Returns list of packages."""
    target_value = target['value']
    tolerance_low = target_value * 0.85
    tolerance_high = target_value * 1.15

    packages = []

    # Sort my assets by value descending for better matching
    my_players_sorted = sorted(my_players, key=lambda x: x['value'], reverse=True)
    my_picks_sorted = sorted(my_picks, key=lambda x: x['value'], reverse=True)

    # 1-for-1 player swaps
    for p in my_players_sorted:
        total = p['value']
        if tolerance_low <= total <= tolerance_high:
            outgoing = [p]
            incoming = [target]
            if validate_trade_salary(my_tid, target['tid'], outgoing, incoming, export, server_id):
                packages.append({
                    'outgoing': outgoing,
                    'incoming': [target],
                    'target_tid': target['tid'],
                    'value_out': total,
                    'value_in': target_value,
                    'fairness': abs(total - target_value)
                })
                if len(packages) >= 2:
                    break

    # Player + pick combos
    for p in my_players_sorted:
        if p['value'] >= target_value:
            continue
        for pick in my_picks_sorted:
            total = p['value'] + pick['value']
            if tolerance_low <= total <= tolerance_high:
                outgoing = [p, pick]
                incoming = [target]
                if validate_trade_salary(my_tid, target['tid'], outgoing, incoming, export, server_id):
                    packages.append({
                        'outgoing': outgoing,
                        'incoming': [target],
                        'target_tid': target['tid'],
                        'value_out': total,
                        'value_in': target_value,
                        'fairness': abs(total - target_value)
                    })
                    break
        if len(packages) >= 3:
            break

    # 2-for-1 player swaps
    if len(packages) < 3:
        for i, p1 in enumerate(my_players_sorted):
            if p1['value'] >= target_value:
                continue
            for p2 in my_players_sorted[i+1:]:
                total = p1['value'] + p2['value']
                if tolerance_low <= total <= tolerance_high:
                    outgoing = [p1, p2]
                    incoming = [target]
                    if validate_trade_salary(my_tid, target['tid'], outgoing, incoming, export, server_id):
                        packages.append({
                            'outgoing': outgoing,
                            'incoming': [target],
                            'target_tid': target['tid'],
                            'value_out': total,
                            'value_in': target_value,
                            'fairness': abs(total - target_value)
                        })
                        break
            if len(packages) >= 3:
                break

    return packages


def check_other_team_accepts(package, export):
    """Check if the other team would accept this trade (value_in >= value_out * 0.9)."""
    # From the other team's perspective: they send the target, they receive our assets
    their_value_out = package['value_in']  # what they lose
    their_value_in = package['value_out']   # what they gain
    return their_value_in >= their_value_out * 0.9


def generate_suggestions(export, my_tid, server_id, position=None, mode='default'):
    """Generate trade suggestions. Returns list of package dicts."""
    my_players = get_tradeable_players(export, my_tid)
    my_picks = get_tradeable_picks(export, my_tid)
    targets = find_target_players(export, my_tid, position)

    if not my_players and not my_picks:
        return []

    # Sort targets based on mode
    if mode == 'youth':
        targets.sort(key=lambda t: (t['pot'], -t['age']), reverse=True)
    elif mode == 'best':
        targets.sort(key=lambda t: t['ovr'], reverse=True)
    else:
        targets.sort(key=lambda t: t['value'], reverse=True)

    all_packages = []
    seen_targets = set()

    for target in targets:
        # Only one suggestion per target player
        if target['pid'] in seen_targets:
            continue

        packages = find_trade_packages(my_players, my_picks, target, export, my_tid, server_id)
        for pkg in packages:
            if check_other_team_accepts(pkg, export):
                all_packages.append(pkg)
                seen_targets.add(target['pid'])
                break  # one package per target

        if len(all_packages) >= 3:
            break

    # Sort by fairness (closest to even value)
    if mode == 'default':
        all_packages.sort(key=lambda p: p['fairness'])

    return all_packages[:2]


def format_asset(asset):
    """Format an asset for display."""
    if asset['type'] == 'player':
        return f"{asset['name']} ({asset['age']}yo {asset['ovr']}/{asset['pot']} {asset['pos']}, ${asset['salary']}M thru {asset['contract_exp']})"
    else:
        descrip = asset['descrip']
        descrip = descrip.replace('round 1', '1st round').replace('round 2', '2nd round').replace('round 3', '3rd round')
        return descrip


def build_suggestion_embeds(suggestions, my_team, position, mode, export, server_id):
    """Build separate embeds for each trade suggestion."""
    teams = export['teams']
    team_list = serversList.get(str(server_id), {}).get('teamlist', {})
    my_team_name = ''
    my_abbrev = ''
    for t in teams:
        if t['tid'] == my_team:
            my_team_name = t['region'] + ' ' + t['name']
            my_abbrev = t['abbrev']

    # Find my team's role for trade channel format
    my_role = basics.team_mention_by_tid(my_team, export, server_id) if hasattr(basics, 'team_mention_by_tid') else my_team_name

    embeds = []
    for i, pkg in enumerate(suggestions):
        other_team_name = ''
        other_abbrev = ''
        for t in teams:
            if t['tid'] == pkg['target_tid']:
                other_team_name = t['region'] + ' ' + t['name']
                other_abbrev = t['abbrev']

        # Find GM
        gm_mention = 'Unassigned'
        for uid, tid in team_list.items():
            if tid == pkg['target_tid']:
                gm_mention = f'<@!{uid}>'
                break

        # Build clean embed
        desc_parts = []
        if position:
            desc_parts.append(f"Position: **{position}**")
        if mode != 'default':
            desc_parts.append(f"Mode: **{mode.title()}**")
        desc = ' | '.join(desc_parts) if desc_parts else ''

        embed = discord.Embed(
            title=f"{my_team_name} ↔ {other_team_name}",
            description=f"GM: {gm_mention}\n{desc}" if desc else f"GM: {gm_mention}"
        )

        # Outgoing
        out_lines = []
        for a in pkg['outgoing']:
            out_lines.append(format_asset(a))
        embed.add_field(
            name=f"📤 {my_abbrev} sends",
            value='\n'.join(out_lines),
            inline=True
        )

        # Incoming
        in_lines = []
        for a in pkg['incoming']:
            in_lines.append(format_asset(a))
        embed.add_field(
            name=f"📥 {my_abbrev} gets",
            value='\n'.join(in_lines),
            inline=True
        )

        embed.set_footer(text=f"Trade Finder — suggestion {i+1} of {len(suggestions)}")
        embeds.append(embed)

    return embeds


async def suggesttrade_command(text, message):
    server_id = str(message.guild.id)
    settings = serversList[server_id]
    team_list = settings.get('teamlist', {})

    try:
        my_tid = team_list[str(message.author.id)]
    except KeyError:
        await message.channel.send("You need to be assigned as a GM to use this command.")
        return

    export = shared_info.serverExports[str(message.guild.id)]

    args = [a.lower() for a in text[1:]] if len(text) > 1 else []
    position = None
    mode = 'default'

    for arg in args:
        arg_upper = arg.upper()
        if arg_upper in VALID_POSITIONS or arg_upper in POSITION_ALIASES:
            position = arg_upper
        elif arg in ['youth', 'young']:
            mode = 'youth'
        elif arg in ['best', 'top']:
            mode = 'best'

    if not position:
        await message.channel.send("Usage: `-tradefinder PG`, `-tradefinder SF youth`, `-tradefinder C best`\n• **youth** — prioritize young, high-potential targets\n• **best** — prioritize highest current OVR")
        return

    suggestions = generate_suggestions(export, my_tid, server_id, position, mode)

    if not suggestions:
        await message.channel.send(f"No fair trades found for a {position}. Your assets may not match any available players, or salary rules prevent a deal.")
        return

    embeds = build_suggestion_embeds(suggestions, my_tid, position, mode, export, server_id)
    for embed in embeds:
        await message.channel.send(embed=embed)
