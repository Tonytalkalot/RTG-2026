import shared_info
from shared_info import serverExports
from shared_info import serversList
import pull_info
import basics
import discord
import free_agency_runner
import asyncio
import os
import copy
from data_dir import data_path
import itertools
import player_commands

#-lineup will fall under team commands.

async def lmove(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    #findPlayer
    player = ' '.join(text[1:-1])
    player = basics.find_match(player, export, False, True,settings =  shared_info.serversList[str(commandInfo['serverId'])])
    #moveTo
    try:
        moveTo = int(text[-1])
    except:
        embed.add_field(name='Error', value='Please provide a valid integer as the last word of your command, to move the player to.')
    
    #see if player is valid
    valid = False
    for p in players:
        if p['pid'] == player:
            if p['tid'] != commandInfo['userTid']:
                embed.add_field(name='Error', value=f"{p['firstName']} {p['lastName']} is not on your team.")
            else:
                if moveTo < 1:
                    embed.add_field(name='Error', value='Please provide a positive number.')
                else:
                    #move the player
                    valid = True
    #create team lineup as a list
    teamLineup = []
    for p in players:
        if p['tid'] == commandInfo['userTid']:
            teamLineup.append([p['pid'], p['rosterOrder']])
    teamLineup.sort(key=lambda l: l[1])
    spot = 1
    newLineup = []
    for t in teamLineup:
        if t[0] == player:
            teamLineup.remove(t)
    for pl in teamLineup:
        if spot == moveTo:
            newLineup.append(player)
        newLineup.append(pl[0])
        spot+=1
    #check the validity of this new lineup with tank rules
    starters = newLineup[:5]
    lowStarterOvr = 101

    for s in starters:
        for p in players:
            if p['pid'] == s:
                if p['ratings'][-1]['ovr'] < lowStarterOvr:
                    lowStarterOvr = p['ratings'][-1]['ovr']
    bench = newLineup[5:]
    highBenchOvr = -1
    for b in bench:
        for p in players:
            if p['pid'] == b:
                if p['ratings'][-1]['ovr'] > highBenchOvr:
                    highBenchOvr = p['ratings'][-1]['ovr']
    limit = serversList[str(commandInfo['serverId'])]['lineupovrlimit']
    if highBenchOvr - lowStarterOvr > int(limit):
        embed.add_field(name='Error', value=f"Your lineup fails anti-tank rules. A bench player can not be more than {limit} OVR higher than a starter.")
    else:
        #set the lineup
        spot = 0
        for n in newLineup:
            for p in players:
                if p['pid'] == n:
                    p['rosterOrder'] = spot
                    spot += 1
        
        embed.add_field(name='Success', value='Lineup adjusted.')
        starters = newLineup[:5]

        path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
        await basics.save_db(export, path_to_file)
    return embed

async def pt(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    #findPlayer
    player = ' '.join(text[1:-1])
    player = basics.find_match(player, export, False, True, settings =  shared_info.serversList[str(commandInfo['serverId'])])
    #the ptMod
    ptMods = ['+', '++', '-', '0', 'none', 'default']
    commandPt = text[-1]
    if commandPt in ptMods:
        if commandPt == '+':
            commandPt = 1.25
        if commandPt == '++':
            commandPt = 1.75
        if commandPt == '-':
            commandPt = 0.75
        if commandPt == '0':
            commandPt = 0
        if commandPt == 'none':
            commandPt = 1
        if commandPt == 'default':
            commandPt = 1
    else:
        try: commandPt = float(commandPt)
        except: embed.add_field(name='Error', value='Please provide 0, -, +, ++, or a positive number as the playing time modifier.')
    #check if player is on team
    valid = False
    for p in players:
        if p['pid'] == player:
            if p['tid'] == commandInfo['userTid']:
                valid = True
    if valid:
        if isinstance(commandPt, (int, float)):
            #if it's not a well known value, apply it as a PT OVR
            if commandPt not in [0, 0.75, 1, 1.25, 1.75]:
                for p in players:
                    if p['pid'] == player:
                        ovr = p['ratings'][-1]['ovr']
                        commandPt = commandPt/ovr
            #check limits
            serverSettings = serversList[str(commandInfo['serverId'])]
            if commandPt > float(serverSettings['maxptlimit']) or commandPt < float(serverSettings['minptlimit']):
                valid = False
                #one exception
                for p in players:
                    if p['pid'] == player:
                        if p['ratings'][-1]['ovr'] <= float(serverSettings['allowzero']):
                            if commandPt == 0:
                                valid = True

                if valid == False:            
                    embed.add_field(name='Violation', value=f'You tried applying a modifier of {round(commandPt, 2)}, which falls outside the server minimum/maximum limits.')
            if valid:
                #apply
                for p in players:
                    if p['pid'] == player:
                        p['ptModifier'] = commandPt
                        name = p['firstName'] + ' ' + p['lastName']
                        embed.add_field(name='Success', value=f"Adjusted {name}'s playing time modifier to {round(commandPt, 2)}.")
                        path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
                        await basics.save_db(export, path_to_file)
    else:
        embed.add_field(name='Error', value='That player is not on your team.')

    return embed

async def autosort(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    #just auto the roster
    lineup = []
    for p in players:
        if p['tid'] == commandInfo['userTid']:
            lineup.append([p['pid'], p['valueNoPot']])
    lineup.sort(key=lambda l: l[1], reverse=True)
    position = 0
    for l in lineup:
        for p in players:
            if p['pid'] == l[0]:
                p['rosterOrder'] = position
                position += 1
    embed.add_field(name='Success', value='Lineup autosorted.')
    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
    await basics.save_db(export, path_to_file)
    return embed

async def autosortsynergy(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    season = export['gameAttributes']['season']

    # Parse sort type
    msg = commandInfo['message'].content.lower()
    sort_type = 'total'
    sort_label = 'Total'
    if 'off' in msg:
        sort_type = 'O'
        sort_label = 'Offensive'
    elif 'def' in msg:
        sort_type = 'D'
        sort_label = 'Defensive'
    elif 'reb' in msg:
        sort_type = 'R'
        sort_label = 'Rebounding'

    # Gather roster players, sort by OVR, take top 8 for synergy combos
    roster = []
    for p in players:
        if p['tid'] == commandInfo['userTid']:
            roster.append(p)

    if len(roster) < 5:
        embed.add_field(name='Error', value='Need at least 5 players on your roster.')
        return embed

    roster.sort(key=lambda p: p['ratings'][-1]['ovr'], reverse=True)
    top8 = roster[:8]
    bench = roster[8:]

    # Evaluate all C(n,5) combinations from top 8
    best_score = -999
    best_combo = None
    for combo in itertools.combinations(top8, 5):
        d = player_commands.lineupsynergycalc(list(combo), season)
        if d is None:
            continue
        if sort_type == 'O':
            score = d['O']
        elif sort_type == 'D':
            score = d['D']
        elif sort_type == 'R':
            score = d['Rs']
        else:
            score = d['O'] + d['D'] + d['Rs']
        if score > best_score:
            best_score = score
            best_combo = list(combo)

    if best_combo is None:
        embed.add_field(name='Error', value='Could not calculate synergy for any lineup combination.')
        return embed

    # Anti-tank check
    starter_pids = set(p['pid'] for p in best_combo)
    remaining = [p for p in top8 if p['pid'] not in starter_pids] + bench
    low_starter_ovr = min(p['ratings'][-1]['ovr'] for p in best_combo)
    if remaining:
        high_bench_ovr = max(p['ratings'][-1]['ovr'] for p in remaining)
    else:
        high_bench_ovr = 0
    limit = serversList[str(commandInfo['serverId'])]['lineupovrlimit']
    if high_bench_ovr - low_starter_ovr > int(limit):
        embed.add_field(name='Error', value=f"Best synergy lineup fails anti-tank rules. A bench player ({high_bench_ovr} OVR) would be more than {limit} OVR higher than a starter ({low_starter_ovr} OVR).")
        return embed

    # Apply: starters get rosterOrder 0-4, rest sorted by valueNoPot
    best_combo.sort(key=lambda p: p['ratings'][-1]['ovr'], reverse=True)
    remaining.sort(key=lambda p: p['valueNoPot'], reverse=True)
    position = 0
    for p in best_combo:
        p['rosterOrder'] = position
        position += 1
    for p in remaining:
        p['rosterOrder'] = position
        position += 1

    # Display result
    starter_text = ""
    for i, p in enumerate(best_combo, 1):
        pi = pull_info.pinfo(p)
        starter_text += f"`{i}.` {pi['position']} **{pi['name']}** — {pi['ovr']}/{pi['pot']}\n"
    embed.add_field(name=f'Lineup sorted by {sort_label} synergy ({round(best_score, 3)})', value=starter_text, inline=False)

    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
    await basics.save_db(export, path_to_file)
    return embed

async def findsynergy(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    season = export['gameAttributes']['season']

    # Parse optional max OVR and sort type from text
    maxovr = 100
    msg = commandInfo['message'].content.lower()
    sort_type = 'total'
    sort_label = 'Total'
    if 'off' in msg:
        sort_type = 'O'
        sort_label = 'Offensive'
    elif 'def' in msg:
        sort_type = 'D'
        sort_label = 'Defensive'
    elif 'reb' in msg:
        sort_type = 'R'
        sort_label = 'Rebounding'

    # Optional position filter, e.g. "-findsynergy def C 60". Broad letters
    # match hybrids too: G matches PG/SG/G/GF, F matches GF/SF/F/PF/FC, C matches FC/C.
    positions = ['PG', 'G', 'SG', 'GF', 'SF', 'F', 'PF', 'FC', 'C']
    pos_filter = None
    for word in commandInfo['message'].content.split()[1:]:
        if word.upper() in positions:
            pos_filter = word.upper()
        try:
            b = int(word)
            if 25 < b < 100:
                maxovr = b
        except ValueError:
            pass

    # Get user's lineup (by rosterOrder), take first 4 starters
    # Fall back to sorting by OVR if rosterOrder isn't set
    roster = []
    for p in players:
        if p['tid'] == commandInfo['userTid']:
            roster.append((p.get('rosterOrder', 9999), p))
    roster.sort(key=lambda x: x[0])
    # If nobody has rosterOrder set, sort by OVR instead
    if all(order == 9999 for order, _ in roster):
        roster = sorted(roster, key=lambda x: x[1]['ratings'][-1]['ovr'] if x[1].get('ratings') else 0, reverse=True)
    top4 = [p for _, p in roster[:4]]

    if len(top4) < 4:
        embed.add_field(name='Error', value='Need at least 4 players on your roster.')
        return embed

    # Build team abbrev lookup
    team_abbrevs = {}
    for tm in export['teams']:
        team_abbrevs[tm['tid']] = tm['abbrev']

    # Title with the 4 players
    names = [f"{p['firstName']} {p['lastName']}" for p in top4]
    title = ", ".join(names) + " - Find 5th"
    if pos_filter:
        title += f" ({pos_filter}"
        title += f", under {maxovr} OVR)" if maxovr != 100 else ")"
    elif maxovr != 100:
        title += f" (under {maxovr} OVR)"
    ovr_note = f" Only showing players under **{maxovr} OVR**." if maxovr != 100 else ""
    pos_note = f" Only showing **{pos_filter}** players." if pos_filter else ""
    description = (f"Searching the league for the best 5th player to complement your top 4 starters by **{sort_label}** synergy.{ovr_note}{pos_note}\n"
                   f"Add `off`, `def`, or `reb` to sort by that category. Add a number to filter by max OVR. Add a position (e.g. `C`, `PG`) to filter by position.")
    embed = discord.Embed(title=title, description=description)

    # Search all league players (not free agents)
    top4_pids = set(p['pid'] for p in top4)
    candidates = []
    for lastp in players:
        if lastp['pid'] in top4_pids:
            continue
        if lastp['tid'] == -1:
            continue
        for v in lastp['ratings']:
            if v['season'] == season and v['ovr'] < maxovr and (pos_filter is None or pos_filter in v.get('pos', '')):
                d = player_commands.lineupsynergycalc(top4 + [lastp], season)
                if d is None:
                    continue
                if len(candidates) > 0 and candidates[-1][0] == lastp['pid']:
                    candidates = candidates[:-1]
                if sort_type == 'O':
                    score = d['O']
                elif sort_type == 'D':
                    score = d['D']
                elif sort_type == 'R':
                    score = d['Rs']
                else:
                    score = d['O'] + d['D'] + d['Rs']
                team_abbrev = team_abbrevs.get(lastp['tid'], '??')
                candidates.append((lastp['pid'], lastp['firstName'] + " " + lastp['lastName'], d['O'], d['D'], d['Rs'], score, v['ovr'], v['pot'], v['pos'], team_abbrev))

    candidates.sort(key=lambda x: x[5], reverse=True)
    top5 = candidates[:5]

    s = ''
    for i, c in enumerate(top5, 1):
        _, name, o, d, rs, score, ovr, pot, pos, team = c
        s += f"{i}. {pos} **{name}** {ovr}/{pot} ({team}): {round(o,3)} O, {round(d,3)} D, {round(rs,3)} R, {round(o+d+rs,3)} total\n"
    if s:
        embed.add_field(name=f"Best {sort_label} Synergy Fits", value=s, inline=False)

    return embed

async def resetpt(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    for p in players:
        if p['tid'] == commandInfo['userTid']:
            p['ptModifier'] = 1
    embed.add_field(name='Success', value='Reset your playing time settings.')
    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
    await basics.save_db(export, path_to_file)
    return embed

async def changepos(embed, text, commandInfo):
    if shared_info.serversList[str(commandInfo['serverId'])].get('poschanges', 'on') == 'off':
        embed.add_field(name='Disabled', value='Position changes are turned off in this league. A mod can re-enable them with `-edit poschanges on`.')
        return embed
    export = shared_info.serverExports[str(commandInfo['serverId'])]

    players = export['players']
    teams = export['teams']
    #findPlayer
    player = ' '.join(text[1:-1])
    player = basics.find_match(player, export, False, True,settings =  shared_info.serversList[str(commandInfo['serverId'])])
    #position
    positions = ['PG', 'G', 'SG', 'GF', 'SF', 'F', 'PF', 'FC', 'C']
    if str.upper(text[-1]) in positions:
        for p in players:
            if p['pid'] == player:
                if p['tid'] != commandInfo['userTid']:
                    embed.add_field(name='Violation', value='That player is not on your team.')
                else:
                    p['ratings'][-1]['pos'] = str.upper(text[-1])
                    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
                    await basics.save_db(export, path_to_file)
                    embed.add_field(name='Success', value=f"{p['firstName']} {p['lastName']}'s position has been changed to {str.upper(text[-1])}.")
    else:
        embed.add_field(name='Error', value='Please move to a valid position.')
    
    return embed

async def acceptto(embed, text, commandInfo):
    message = commandInfo['message']
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    serverSettings = shared_info.serversList[str(commandInfo['serverId'])]
    #findPlayer
    player = ' '.join(text[1:])
    player = basics.find_match(player, export, False, True,settings =  shared_info.serversList[str(commandInfo['serverId'])])
    for p in players:
        if p['pid'] == player:
            name = f"{p['firstName']} {p['lastName']}"
            rating = f"{p['ratings'][-1]['ovr']}/{p['ratings'][-1]['pot']}"
            # CHECKS
            valid = True
            # -1. the options is on
            if serverSettings['options'] == 'off':
                valid = False
            # 0. the TO exists, for this season
            amount = 0
            if 'TO' in serverSettings:
 
                if not (player in serverSettings['TO'] or str(player) in serverSettings['TO']):
                    print("hence")
                    valid = False
                else:
                    print("kinda nice")
                    
                    if player in serverSettings['TO']:
                        print("either here")
                        if not int(serverSettings['TO'][player][1]) == export['gameAttributes']['season']:
                            valid = False
                        else:
                            print("aha2")
                            amount =1000* float(serverSettings['TO'][player][0])
                    if str(player) in serverSettings['TO']:
                        print("or  here")
 
                        if not int(serverSettings['TO'][str(player)][1]) == export['gameAttributes']['season']:
                            valid = False
                        else:
                            print("aha")
                            amount =1000* float(serverSettings['TO'][str(player)][0])

            # 1. there is such a negotiation
            print("intermediate")
            print(valid)
            if valid:
                tid = commandInfo['userTid']
                if not 'negotiations' in export:
                    valid = False
                else:
                    valid = False
                    for n in export['negotiations']:
                        if n['tid'] == tid and n['pid'] == player:
                            print("found negotiation")
                            valid = True
            #2. hard cap
            if valid:
                teamPayroll = 0
                for p2 in players:
                    if p2['tid'] == commandInfo['userTid']:
                        teamPayroll += p2['contract']['amount']
                try:
                    for r in export['releasedPlayers']:
                        if r['tid'] == commandInfo['userTid']:
                            teamPayroll += r['contract']['amount']
                except: pass
                if teamPayroll + amount > float(serverSettings['hardcap'])*1000:
                    print("violated hardcap")
                    print(teamPayroll)
                    print(amount)
                    print(serverSettings['hardcap'])
                    valid = False
            #3. player currently has no team on him
            if p['tid'] >= 0:
                valid = False
            if not valid:
                embed.add_field(name = "This player is NOT available to sign to a 1 year TO.", value = "At least one of 5 things is true: \n1. options settings is off. \n2. Player is currently on a team. \n3. hard cap is violated if you sign this guy to the requested TO. \n4. the player is not negotiating with that team actively. \n5. There is no contract with a team option for this player.")
            if valid:
                #confirmation
                text = f'Are you sure you sign the player {name} ({rating}) to a 1 year team option at ${amount/1000} million? This action can not be reversed. Click the ✅ to confirm.'
                
                confirmMessage = await commandInfo['message'].channel.send(text)
                await confirmMessage.add_reaction('✅')
                def check(payload):
                    return payload.message_id == confirmMessage.id and payload.user_id == commandInfo['message'].author.id and str(payload.emoji) == '✅'
                try:
                    payload = await shared_info.bot.wait_for('raw_reaction_add', timeout=10, check=check)
                except asyncio.TimeoutError:
                    await confirmMessage.edit(content='❌Timed out.')
                else:
                    await confirmMessage.edit(content='Signing player...')
                    # LOGISTICAL STUFF
                    t = None
                    team = export['teams'][tid]
                    for n in export['negotiations']:
                        if n['pid'] == player:
                            t = n
                    export['negotiations'].remove(t)
                    if True:
                        x = serverSettings['TO']
                        if str(player) in x:
                            del serverSettings['TO'][str(player)]
                        else:
                            del serverSettings['TO'][player]
                    
                    p['tid'] = team['tid']
                    abbrev = team['abbrev']
                    tname = team['region']+" "+team['name']
                    p['contract'] = {
                        "amount": amount,
                        "exp": export['gameAttributes']['season']+1
                    }
                    p['gamesUntilTradable'] = serversList[str(commandInfo['serverId'])]['traderesign']
                    for i in range(0,1):
                        salaryInfo = dict()
                        salaryInfo['season'] = export['gameAttributes']['season'] + i + 1
                        salaryInfo['amount'] = amount
                        p['salaries'].append(salaryInfo)
                    events = export['events']
                    newEvent = dict()
                    newEvent['text'] = 'The <a href="/l/10/roster/' + team['abbrev'] + '/' + str( export['gameAttributes']['season']) + '">' + team['name'] + '</a> re-signed <a href="/l/10/player/' + str(p['pid']) + '">' + p['firstName'] + ' ' + p['lastName'] + '</a> for $' + str(amount/1000) + 'M/year through ' + str(1 + export['gameAttributes']['season']) + '.'
                    newEvent['pids'] = [p['pid']]
                    newEvent['tids'] = [team['tid']]
                    newEvent['season'] = export['gameAttributes']['season']
                    newEvent['type'] = 'reSigned'
                    newEvent['eid'] = events[-1]['eid'] + 1
                    events.append(newEvent)
                    message2 = p['firstName']+" "+p['lastName']+ " gets resigned on a 1 year team option by "+basics.team_mention(message, tname, abbrev)+"."
                    try:
                            transChannel = shared_info.bot.get_channel(int(serversList[str(commandInfo['serverId'])]['fachannel'].replace('<#', '').replace('>', '')))
                            await transChannel.send(message2)
                    except Exception:
                            await message.channel.send(message2)
                    await basics.save_db(serversList)
                    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
                    await basics.save_db(export, path_to_file)
                    await confirmMessage.edit(content='**Complete.**')
                    embed = None
    return embed

async def acceptrookieoption(embed, text, commandInfo):
    message = commandInfo['message']
    tid = commandInfo['userTid']
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    serverSettings = shared_info.serversList[str(commandInfo['serverId'])]
    #findPlayer
    player = ' '.join(text[1:])
    player = basics.find_match(player, export, False, True,settings =  shared_info.serversList[str(commandInfo['serverId'])])
    for p in players:
        if p['pid'] == player:
            name = f"{p['firstName']} {p['lastName']}"
            rating = f"{p['ratings'][-1]['ovr']}/{p['ratings'][-1]['pot']}"
            # CHECKS
            valid = True
            # -1. the options is on
            if serverSettings['rookieoptions'] == 'off':
                valid = False
            if not export['gameAttributes']['phase'] == 7:
                valid = False
            # 0. the player is someone off their rookie contract and is drafted in round 1
            amount = 0
            tempvalid = False
            if p['draft']['round'] == 1 and p['draft']['year'] == export['gameAttributes']['season'] - export['gameAttributes']['rookieContractLengths'][0]:
                x = True
                for t in p.get('transactions', []):
                    if t['type'] == 'release':
                        x = False
                if len(p['stats']) == 0:
                    #print(p['firstName']+" "+p['lastName'])
                    x = False
                if x:
                    if p['tid'] < 0:
                        if p['stats'][-1]['tid'] == commandInfo['userTid']:
                            tempvalid = True
                            amount = p['salaries'][0]['amount']*1.2
            if (not tempvalid):
                valid= False
            
            #1. hard cap
            if valid:
                teamPayroll = 0
                for p2 in players:
                    if p2['tid'] == commandInfo['userTid']:
                        teamPayroll += p2['contract']['amount']
                try:
                    for r in export['releasedPlayers']:
                        if r['tid'] == commandInfo['userTid']:
                            teamPayroll += r['contract']['amount']
                except: pass
                if teamPayroll + amount > float(serverSettings['hardcap'])*1000:
                    print("violated hardcap")
                    print(teamPayroll)
                    print(amount)
                    print(serverSettings['hardcap'])
                    valid = False
            #2. player currently has no team on him
            if p['tid'] >= 0:
                valid = False
            
            if not valid:
                embed.add_field(name = "This player is NOT available to sign to a 1 year rookie option.", value = "At least one of 5 things is true: \n1. rookie options settings is off. \n2. Player is currently on a team. \n3. hard cap is violated if you sign this guy to the requested rookie option. \n4. the player is not negotiating with that team actively. \n5. There is no contract with a team option for this player.")
            if valid:
                #confirmation
                text = f'Are you sure you sign the player {name} ({rating}) to his rookie option at ${amount/1000} million? This action can not be reversed. Click the ✅ to confirm.'
                
                confirmMessage = await commandInfo['message'].channel.send(text)
                await confirmMessage.add_reaction('✅')
                def check(payload):
                    return payload.message_id == confirmMessage.id and payload.user_id == commandInfo['message'].author.id and str(payload.emoji) == '✅'
                try:
                    payload = await shared_info.bot.wait_for('raw_reaction_add', timeout=10, check=check)
                except asyncio.TimeoutError:
                    await confirmMessage.edit(content='❌Timed out.')
                else:
                    await confirmMessage.edit(content='Signing player...')
                    # LOGISTICAL STUFF
                    t = None
                    team = export['teams'][tid]
                    for n in export['negotiations']:
                        if n['pid'] == player:
                            t = n
                    if t is not None:
                        export['negotiations'].remove(t)

                    p['tid'] = team['tid']
                    abbrev = team['abbrev']
                    tname = team['region']+" "+team['name']
                    p['contract'] = {
                        "amount": amount,
                        "exp": export['gameAttributes']['season']+1
                    }
                    p['gamesUntilTradable'] = serversList[str(commandInfo['serverId'])]['traderesign']
                    for i in range(0,1):
                        salaryInfo = dict()
                        salaryInfo['season'] = export['gameAttributes']['season'] + i + 1
                        salaryInfo['amount'] = amount
                        p['salaries'].append(salaryInfo)
                    events = export['events']
                    newEvent = dict()
                    text = 'The <a href="/l/10/roster/' + team['abbrev'] + '/' + str( export['gameAttributes']['season']) + '">'
                    text = text   + team['name'] + '</a> re-signed <a href="/l/10/player/' + str(p['pid']) + '">' + p['firstName'] + ' ' + p['lastName']
                    text = text  + '</a> for $' + str(amount/1000) + 'M/year through ' + str(1 + export['gameAttributes']['season']) + '(rookie option).'
                    newEvent['text'] = text
                    newEvent['pids'] = [p['pid']]
                    newEvent['tids'] = [team['tid']]
                    newEvent['season'] = export['gameAttributes']['season']
                    newEvent['type'] = 'reSigned'
                    newEvent['eid'] = events[-1]['eid'] + 1
                    events.append(newEvent)
                    message2 = p['firstName']+" "+p['lastName']+ " gets his rookie option picked up by "+basics.team_mention(message, tname, abbrev)+"."
                    try:
                            transChannel = shared_info.bot.get_channel(int(serversList[str(commandInfo['serverId'])]['fachannel'].replace('<#', '').replace('>', '')))
                            await transChannel.send(message2)
                    except Exception:
                            await message.channel.send(message2)
                    await basics.save_db(serversList)
                    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
                    await basics.save_db(export, path_to_file)
                    await confirmMessage.edit(content='**Complete.**')
                    embed = None
    return embed
                
            

async def release(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    serverSettings = shared_info.serversList[str(commandInfo['serverId'])]
    #findPlayer
    player = ' '.join(text[1:])
    player = basics.find_match(player, export, False, True,settings =  shared_info.serversList[str(commandInfo['serverId'])])
    for p in players:
        if p['pid'] == player:
            name = f"{p['firstName']} {p['lastName']}"
            rating = f"{p['ratings'][-1]['ovr']}/{p['ratings'][-1]['pot']}"
            #validity checks!
            valid = True
            #OVR
            maxOvrRelease = int(serverSettings['maxovrrelease'])
            if p['ratings'][-1]['ovr'] > maxOvrRelease:
                embed.add_field(name='Illegal', value=f'{name} is too highly rated to be released.')
                valid = False
            #team
            if p['tid'] != commandInfo['userTid']:
                embed.add_field(name='Illegal', value=f"{name} is not on your team.")
                valid = False
            if valid:
                #confirmation
                text = f'Are you sure you want to release {name} ({rating})? This action can not be reversed. Click the ✅ to confirm.'
                confirmMessage = await commandInfo['message'].channel.send(text)
                await confirmMessage.add_reaction('✅')
                def check(payload):
                    return payload.message_id == confirmMessage.id and payload.user_id == commandInfo['message'].author.id and str(payload.emoji) == '✅'
                try:
                    payload = await shared_info.bot.wait_for('raw_reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    await confirmMessage.edit(content='❌ Release timed out.')
                else:
                    await confirmMessage.edit(content='Releasing player...')
                    await basics.release_player(p['pid'], commandInfo['message'], commandInfo)
                    await confirmMessage.edit(content='**Complete.**')
                    embed = None
    return embed


async def autocut(embed, text, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = export['gameAttributes']['season']

    maxRoster = export['gameAttributes']['maxRosterSize']

    for t in teams:
        roster = []
        for p in players:
            if p['tid'] == t['tid']:
                autocutFormula = (p['ratings'][-1]['ovr'] + p['ratings'][-1]['pot'])
                if p['contract']['exp'] == season:
                    autocutFormula+=0.3
                if p['draft']['year'] == season or (p['draft']['year'] == season-1 and export['gameAttributes']['phase'] == 0):
                    autocutFormula += 0.5
                roster.append([p['pid'], autocutFormula])
        roster.sort(key=lambda r: r[1], reverse=True)
        toCut = len(roster) - maxRoster
        if toCut > 0:
            releasePlayers = roster[-toCut:]
            for r in releasePlayers:
                print(r[0])
                export = await basics.release_player(r[0], commandInfo['message'], commandInfo, updateexport=False, export=export)
    path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
    await basics.save_db(export, path_to_file)
    embed.add_field(name='Complete', value='Autocuts done.')
    return embed





