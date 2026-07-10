import shared_info
from shared_info import serversList
import basics
import discord
from datetime import date

# ── helpers ──

def get_position_breakdown(export, tid):
    positions = {}
    for p in export['players']:
        if p['tid'] == tid and p.get('ratings'):
            pos = p['ratings'][-1].get('pos', '?')
            positions[pos] = positions.get(pos, 0) + 1
    return positions

def get_team_payroll(export, tid):
    total = 0
    for p in export['players']:
        if p['tid'] == tid:
            total += p['contract']['amount']
    return total

def get_roster_count(export, tid):
    return sum(1 for p in export['players'] if p['tid'] == tid)

def get_autopilot_config(serverId, tid):
    autopilot = serversList[str(serverId)].get('autopilot', {})
    return autopilot.get(str(tid), None)


# ── FA offer generation ──

def generate_autopilot_offers(export, serverId):
    """Generate 1yr FA offers for all autopilot teams. Returns list of offer dicts."""
    autopilot = serversList[str(serverId)].get('autopilot', {})
    if not autopilot:
        return []

    settings = serversList[str(serverId)]
    players = export['players']
    maxContract = export['gameAttributes']['maxContract'] / 1000
    hardCap = float(settings.get('hardcap', 200))
    maxRoster = int(settings.get('maxroster', 15))
    holdoutPct = float(settings.get('holdout', 100)) / 100

    # Get all free agents
    freeAgents = []
    for p in players:
        if p['tid'] == -1 and p.get('ratings'):
            r = p['ratings'][-1]
            freeAgents.append({
                'pid': p['pid'],
                'pot': r.get('pot', 0),
                'ovr': r.get('ovr', 0),
                'pos': r.get('pos', '?'),
                'askingPrice': p['contract']['amount'] / 1000,
                'name': p['firstName'] + ' ' + p['lastName']
            })

    # Rank by pot for "top 15" determination
    freeAgents.sort(key=lambda x: x['pot'], reverse=True)
    top15Pots = set(fa['pid'] for fa in freeAgents[:15])

    offers = []

    for tidStr, config in autopilot.items():
        if not config.get('enabled', False):
            continue
        tid = int(tidStr)
        payroll = get_team_payroll(export, tid) / 1000
        rosterCount = get_roster_count(export, tid)
        posBreakdown = get_position_breakdown(export, tid)
        needPositions = [pos for pos in ['PG', 'SG', 'SF', 'PF', 'C'] if posBreakdown.get(pos, 0) < 2]

        # Count how many offers we're generating for priority
        teamOfferCount = sum(1 for o in settings.get('offers', []) if o['team'] == tid)

        for fa in freeAgents:
            if rosterCount >= maxRoster:
                break

            # Determine offer amount based on pot tier
            pot = fa['pot']
            if fa['pid'] in top15Pots or pot >= 68:
                amount = maxContract
            elif 63 <= pot <= 67:
                amount = maxContract * 0.5
            elif 60 <= pot <= 62:
                amount = maxContract * 0.33
            elif 57 <= pot <= 59:
                holdoutAmount = fa['askingPrice'] * holdoutPct
                if holdoutAmount > maxContract * 0.33:
                    continue  # too expensive for this tier
                amount = holdoutAmount
            else:
                continue  # skip below 57

            # Clamp to valid range
            minContract = export['gameAttributes']['minContract'] / 1000
            amount = max(amount, minContract)
            amount = min(amount, maxContract)
            amount = round(amount, 1)

            # Respect holdout floor
            holdoutFloor = fa['askingPrice'] * holdoutPct
            if amount < holdoutFloor:
                amount = round(holdoutFloor, 1)
            if amount > maxContract:
                continue

            # Cap check
            if (payroll + amount) > hardCap:
                continue

            # Prefer needed positions
            # (still offer for non-needed positions but prioritize needs)
            priority = teamOfferCount + 1
            if fa['pos'] in needPositions:
                priority = max(1, priority - 10)  # boost priority for needs

            offer = {
                "player": fa['pid'],
                "amount": amount,
                "years": 1,
                "team": tid,
                "option": None,
                "priority": priority,
                "qo": False
            }
            offers.append(offer)
            teamOfferCount += 1
            rosterCount += 1  # assume we might sign them
            payroll += amount

    return offers


# ── Trade evaluation ──

def calculate_player_pick_value(player, export):
    """Calculate a player's value in terms of mid-1st-round picks."""
    r = player['ratings'][-1]
    pot = r.get('pot', 0)
    season = export['gameAttributes']['season']
    age = season - player['born']['year']
    salary = player['contract']['amount'] / 1000
    maxContract = export['gameAttributes']['maxContract'] / 1000

    # Base value by pot
    if pot >= 63:
        value = 1.0
    elif pot >= 60:
        value = 0.7
    elif pot >= 57:
        value = 0.4
    else:
        value = 0.2

    # Age bonus for young players on deals
    if age < 25:
        value += (25 - age) * 0.1

    # Bad contract penalty: if salary exceeds their FA-tier value
    if pot >= 68:
        fairSalary = maxContract
    elif pot >= 63:
        fairSalary = maxContract * 0.5
    elif pot >= 60:
        fairSalary = maxContract * 0.33
    else:
        fairSalary = maxContract * 0.15

    if salary > fairSalary * 1.2:
        value -= 1.0  # costs a 1st to dump a bad contract

    return value


def calculate_pick_value(pick, export):
    """Calculate a draft pick's value in terms of mid-1st-round picks."""
    season = export['gameAttributes']['season']

    if pick['round'] == 1:
        value = 1.0
    else:
        value = 0.3

    # Future pick bonus
    if pick['season'] > season:
        value *= 1.1

    # Team quality adjustment based on current record
    teams = export['teams']
    for t in teams:
        if t['tid'] == pick['originalTid']:
            try:
                stats = t['seasons'][-1]
                winPct = stats['won'] / max(1, stats['won'] + stats['lost'])
                if winPct > 0.6:
                    value *= 0.7  # good team = late pick
                elif winPct < 0.4:
                    value *= 1.3  # bad team = early pick
            except (KeyError, IndexError):
                pass
            break

    return value


def evaluate_trade_for_autopilot(tradeData, autopilotTid, export, serverId):
    """
    Evaluate a trade for an autopilot team.
    Returns (accept: bool, reason: str)
    """
    players = export['players']
    settings = serversList[str(serverId)]
    hardCap = float(settings.get('hardcap', 200))
    season = export['gameAttributes']['season']

    # Figure out which assets are incoming vs outgoing for the autopilot team
    # Handle both int and string keys (orjson serialization may convert)
    outgoing_assets = tradeData.get(autopilotTid, tradeData.get(str(autopilotTid), []))
    incoming_assets = []
    otherTid = None
    for tid, assets in tradeData.items():
        if int(tid) != autopilotTid:
            incoming_assets = assets
            otherTid = int(tid)

    if otherTid is None:
        return False, "Could not identify trade partner."

    # Check daily trade limit
    config = get_autopilot_config(serverId, autopilotTid)
    if config:
        history = config.get('tradeHistory', {})
        today = str(date.today())
        if str(otherTid) in history and history[str(otherTid)] == today:
            return False, "You can only propose one trade per day to an autopilot team."

    # Hard reject: any player with pot > 65
    for a in outgoing_assets + incoming_assets:
        if a['type'] == 'player':
            for p in players:
                if p['pid'] == a['id']:
                    pot = p['ratings'][-1].get('pot', 0)
                    if pot > 65:
                        return False, f"Trades involving players with 65+ potential require manual GM approval."

    # Calculate salary in/out
    salaryIn = 0
    salaryOut = 0
    for a in incoming_assets:
        if a['type'] == 'player':
            for p in players:
                if p['pid'] == a['id']:
                    salaryIn += p['contract']['amount'] / 1000
    for a in outgoing_assets:
        if a['type'] == 'player':
            for p in players:
                if p['pid'] == a['id']:
                    salaryOut += p['contract']['amount'] / 1000

    # Hard reject: taking on salary
    if salaryIn > salaryOut and salaryIn > 0:
        return False, "Autopilot will not accept trades that increase team salary."

    # Hard reject: would exceed hard cap
    currentPayroll = get_team_payroll(export, autopilotTid) / 1000
    newPayroll = currentPayroll + salaryIn - salaryOut
    if newPayroll > hardCap:
        return False, "Trade would exceed the hard cap."

    # Calculate total value in/out
    valueIn = 0
    valueOut = 0

    for a in incoming_assets:
        if a['type'] == 'player':
            for p in players:
                if p['pid'] == a['id']:
                    valueIn += calculate_player_pick_value(p, export)
        elif a['type'] == 'draftPick':
            for pick in export['draftPicks']:
                if pick['dpid'] == a['id']:
                    valueIn += calculate_pick_value(pick, export)

    for a in outgoing_assets:
        if a['type'] == 'player':
            for p in players:
                if p['pid'] == a['id']:
                    valueOut += calculate_player_pick_value(p, export)
        elif a['type'] == 'draftPick':
            for pick in export['draftPicks']:
                if pick['dpid'] == a['id']:
                    valueOut += calculate_pick_value(pick, export)

    # Accept if incoming value >= 90% of outgoing value
    if valueIn >= valueOut * 0.9:
        return True, f"Trade value acceptable (in: {round(valueIn, 2)} picks, out: {round(valueOut, 2)} picks)."
    else:
        return False, f"Trade value insufficient (in: {round(valueIn, 2)} picks, out: {round(valueOut, 2)} picks)."


def record_trade_attempt(serverId, autopilotTid, otherTid):
    """Record that a team attempted a trade with an autopilot team today."""
    config = serversList[str(serverId)]['autopilot'].get(str(autopilotTid))
    if config:
        if 'tradeHistory' not in config:
            config['tradeHistory'] = {}
        config['tradeHistory'][str(otherTid)] = str(date.today())


# ── Autopilot command ──

async def autopilot_command(text, message):
    serverId = str(message.guild.id)
    settings = serversList[serverId]
    teamList = settings.get('teamlist', {})

    try:
        userTid = teamList[str(message.author.id)]
    except KeyError:
        await message.channel.send("You need to be assigned as a GM to use autopilot.")
        return

    if 'autopilot' not in settings:
        settings['autopilot'] = {}

    tidStr = str(userTid)
    args = [t.lower() for t in text[1:]] if len(text) > 1 else []

    if not args:
        # Show status
        config = settings['autopilot'].get(tidStr)
        if config and config.get('enabled'):
            tradesStatus = "on" if config.get('trades', False) else "off"
            await message.channel.send(f"🤖 Autopilot is **on** for your team. Trades: **{tradesStatus}**.")
        else:
            await message.channel.send("🤖 Autopilot is **off** for your team.")
        return

    if args[0] == 'on':
        settings['autopilot'][tidStr] = {
            "enabled": True,
            "trades": False,
            "tradeHistory": {}
        }
        # Set default draft formula if none exists
        draftPrefs = settings.get('draftPreferences', {})
        if not draftPrefs.get(tidStr, ''):
            draftPrefs[tidStr] = 'pot'
            settings['draftPreferences'] = draftPrefs

        await basics.save_db(serversList)
        await message.channel.send(
            "🤖 **Autopilot enabled.** I'll handle:\n"
            "• **Free agency** — 1yr offers based on potential\n"
            "• **Draft** — highest potential (or your custom formula)\n"
            "• **Lineups** — synergy-optimized auto-sort\n\n"
            "Trade responses are **off** by default. Use `-autopilot trades on` to enable (experimental)."
        )
        return

    if args[0] == 'off':
        settings['autopilot'].pop(tidStr, None)
        await basics.save_db(serversList)
        await message.channel.send("🤖 **Autopilot disabled.** You're back in control.")
        return

    if args[0] == 'trades':
        config = settings['autopilot'].get(tidStr)
        if not config or not config.get('enabled'):
            await message.channel.send("Turn on autopilot first with `-autopilot on`.")
            return
        if len(args) < 2:
            tradesStatus = "on" if config.get('trades', False) else "off"
            await message.channel.send(f"🤖 Trade autopilot is **{tradesStatus}**.")
            return
        if args[1] == 'on':
            config['trades'] = True
            await basics.save_db(serversList)
            await message.channel.send(
                "🤖 **Trade autopilot enabled (experimental).** I'll auto-accept/reject trades involving your team.\n"
                "⚠️ Trades involving players with 65+ potential will always be rejected — those need manual approval.\n"
                "Each team can only propose one trade per day to your team."
            )
            return
        if args[1] == 'off':
            config['trades'] = False
            await basics.save_db(serversList)
            await message.channel.send("🤖 **Trade autopilot disabled.**")
            return

    await message.channel.send("Usage: `-autopilot on`, `-autopilot off`, `-autopilot trades on/off`")
