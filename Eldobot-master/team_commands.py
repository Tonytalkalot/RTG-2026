from shared_info import serverExports
from shared_info import serversList
import shared_info
import pull_info
import basics
import discord
import random
import plotly_express as px
import player_commands
import json
import asyncio
import itertools
import coach_commands


def _team_rating_rank(target_tid, export, season):
    """Return (rank, total) for a team's team_rating among active teams.

    Active = team has at least one player on roster this season (mirrors
    how the rest of the bot treats disabled / contracted teams).
    """
    try:
        teams = export['teams']
        players = export['players']
        current_season = export['gameAttributes']['season']
        ratings_by_tid = {}
        if season == current_season:
            for p in players:
                tid = p.get('tid', -1)
                if tid < 0:
                    continue
                ratings_by_tid.setdefault(tid, []).append(p['ratings'][-1]['ovr'])
        else:
            for p in players:
                for s in p.get('stats', []):
                    if s.get('season') == season and s.get('tid', -1) >= 0:
                        rl = p.get('ratings') or []
                        ovr = rl[-1]['ovr'] if rl else 0
                        for r in rl:
                            if r.get('season') == season:
                                ovr = r.get('ovr', ovr); break
                        ratings_by_tid.setdefault(s['tid'], []).append(ovr)
                        break
        scored = []
        for t in teams:
            if t.get('disabled'):
                continue
            tid = t['tid']
            if tid not in ratings_by_tid:
                continue
            tr = float(pull_info.team_rating(ratings_by_tid[tid], False))
            scored.append((tid, tr))
        scored.sort(key=lambda x: -x[1])
        for idx, (tid, _) in enumerate(scored, start=1):
            if tid == target_tid:
                return (idx, len(scored))
    except Exception:
        pass
    return (None, None)


def penalties(embed, t, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    teams = export['teams']
    pens = []
    for t in teams:
        tp = pull_info.trade_penalty(t['tid'], export)
        name = t['region']+" "+t['name']
        pens.append((name,tp))
    s = ""
    pens = sorted(pens, key = lambda x: x[1], reverse = True)
    count = 0
    for item in pens:
        count += 1
        s = s + "**"+item[0]+"**: "+str(round(item[1],3))+"\n"
        if count % 10 == 0:
            embed.add_field(name = "trade penalties", value = s)
            s = ""
    if len(s) > 0:
        embed.add_field(name = "trade penalties", value = s)
    return embed
def penalty(embed, t, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    tp = pull_info.trade_penalty(t['tid'], export)
    embed.add_field(name = str(tp), value = "This team's trade penalty is "+str(tp))
    return embed
def capspace(embed, t, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    l = []
    salaryCap = export['gameAttributes']['salaryCap']
    for tid in export['teams']:
        if not tid['disabled']:
            payroll = 0
            for p in players:
                if p['tid'] == tid['tid']:
                    payroll += p['contract']['amount']
            if 'releasedPlayers' in export:
                for rp in export['releasedPlayers']:
                    if rp['tid'] == tid['tid']:
                        payroll += rp['contract']['amount']
            name = tid['region']+" "+tid['name']
            l.append([name, (salaryCap-payroll)/1000])
    l = sorted(l, key = lambda a: a[1], reverse = True)
    text = ""
    for i in l[0:min(len(l),20)]:
        text = text + i[0] + ": " + str(i[1])+"\n"

    embed.add_field(name = "What am I supposed to write for the name of the embed", value = text)
    return embed
def rgoptions(embed, team, commandInfo):
    listofthings = "season, tid, yearsWithTeam, per, ewa, astp, blkp, drbp, orbp, stlp, trbp, usgp, drtg, ortg, dws, ows, obpm, dbpm, vorp, gp, gs, min, minAvailable, fg, fga, fgAtRim, fgaAtRim, fgLowPost, fgaLowPost, fgMidRange, fgaMidRange, tp, tpa, ft, fta, pm, orb, drb, ast, tov, stl, blk, ba, pf, pts, dd, td, qd, fxf, jerseyNumber, mpg, ppg, reb, rpg, apg, bpg, spg, tpg, fpg, fg%, ft%, tp%, ws, bpm, ast/tov, fg%AtRim, fg%LowPost, fg%MidRange"

    embed.add_field(name = "Stats options", value = listofthings)
    return embed

def rostergraph(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    message = commandInfo['message']
    m=commandInfo['message'].content.replace('rostergraph',"")[1:].strip()
        #print(m+"hi")
        
    try:
        yr = int(message.content.split(" ")[-1])
        m=m.replace(str(yr),"").strip()
    except ValueError:
        yr = export['gameAttributes']['season']
    if yr:
        t = m.split(" ")
        
        tid = team['tid'] # default, team is the user team
        
        firststatname = "ortg"
        secondstatname = "drtg"
        assigned = False
        secondisassigned = False
        poff = False
        listofthings = "season, tid, yearsWithTeam, per, ewa, astp, blkp, drbp, orbp, stlp, trbp, usgp, drtg, ortg, dws, ows, obpm, dbpm, vorp, gp, gs, min, minAvailable, fg, fga, fgAtRim, fgaAtRim, fgLowPost, fgaLowPost, fgMidRange, fgaMidRange, tp, tpa, ft, fta, pm, orb, drb, ast, tov, stl, blk, ba, pf, pts, dd, td, qd, fxf, jerseyNumber, mpg, ppg, reb, rpg, apg, bpg, spg, tpg, fpg, fg%, ft%, tp%, ws, bpm, ast/tov, fg%AtRim, fg%LowPost, fg%MidRange"


        for item in t:
            if item.__contains__("layoff"):
                poff = True
            elif len(item)>1:

                if not assigned:
                    if item in listofthings:
                        firststatname = item
                        assigned = True
                else:
                    if not secondisassigned:
                        if item in listofthings:
                            secondstatname = item
                            secondisassigned = True


        
        roster = []
        statentries = []
        for player in players:
            t = False
            if player['retiredYear'] is None:
                t = True
            else:
                if  player['retiredYear'] >= yr:
                    t = True
            if t:

                if yr == export['gameAttributes']['season'] and len(player.get("stats"))>0 and player.get("stats")[-1].get("tid")==tid:

                    
                    if not poff:
                        if player.get("stats")[-1].get("playoffs")==False:
                            roster.append(player)
                            statentries.append(player.get("stats")[-1])
                        else:
                            if player.get("stats")[-2].get("playoffs")==False and player.get("stats")[-2].get("tid")==tid and player.get("stats")[-2].get("season")==yr:
                                roster.append(player)
                                statentries.append(player.get("stats")[-2])
                    else:
                        if player.get("stats")[-1].get("playoffs")==True:
                            roster.append(player)
                            statentries.append(player.get("stats")[-1])
                if yr<export['gameAttributes']['season']:
                    for item in player.get("stats"):
                        if item.get("season")==yr and item.get("tid")==tid and item.get("playoffs")==poff:
                            roster.append(player)
                            statentries.append(item)

        names = []
        firststat = []
        secondstat = []
        sizes = []
        colors = ["#F63309","#09F621","#090FF6","#F68509","#F3F609","#09c3ba","#601A83","#83221A","#835B1A","#b1d5fb","#BB22B5","#FF13CD","#6891f8","#fcc5f4","#1d6b05","#878787","#787878","#A36B41","#87B5FF","#F5BFBD","#4E1B4B","#76190F","#41203E","#0A144A"]
        t = ""
        
        for item in listofthings.split(" "):
            if item.replace(",","").lower()==firststatname.lower():
                firststatname=item.replace(",","")
            if item.replace(",","").lower()==secondstatname.lower():
                secondstatname=item.replace(",","")
        #print("oh "+firststatname+" oh")
        for index in range (0,len(roster)):
            s = statentries[index]
            pid = roster[index].get("pid")
            if s['season'] == yr:
            
                #calculate secondary stats
                if s.get("min")>100 or (poff == True and s.get("min")>10):
                    
                    names.append(roster[index]['firstName'] + " " + roster[index]['lastName'])
                    #print(s)
                    s.update({"mpg":s.get("min")/s.get("gp")})
                    s.update({"ppg":s.get("pts")/s.get("gp")})
                    s.update({"reb":s.get("orb")+s.get("drb")})
                    s.update({"rpg":s.get("reb")/s.get("gp")})
                    s.update({"apg":s.get("ast")/s.get("gp")})
                    s.update({"bpg":s.get("blk")/s.get("gp")})
                    s.update({"spg":s.get("stl")/s.get("gp")})
                    s.update({"tpg":s.get("tov")/s.get("gp")})
                    s.update({"fpg":s.get("pf")/s.get("gp")})
                    s.update({"fg%":100*s.get("fg")/(s.get("fga")+0.000001)})
                    s.update({"jerseyNumber":int(s.get("jerseyNumber"))})
                    s.update({"ft%":100*s.get("ft")/(s.get("fta")+0.00001)})
                    s.update({"tp%":100*s.get("tp")/(s.get("tpa")+0.00001)})
                    s.update({"ws":s.get("ows")/s.get("dws")})
                    s.update({"bpm":s.get("obpm")/s.get("dbpm")})
                    
                    s.update({"ast/tov":s.get("ast")/(s.get("tov")+0.0000001)})
                    s.update({"fg%AtRim":100*s.get("fgAtRim")/(s.get("fgaAtRim")+0.0000001)})
                    s.update({"fg%LowPost":100*s.get("fgLowPost")/(s.get("fgaLowPost")+0.0000001)})
                    s.update({"fg%MidRange":100*s.get("fgMidRange")/(s.get("fgaMidRange")+0.0000001)})
                    #print(s.keys())

                    #print(firststatname)
                    if not (s.__contains__(firststatname) and s.__contains__(secondstatname)):
                        t += "Something about the two variables you specified is invalid.\n"
                        t += "To help you out: what we received from you was: "+firststatname+" and "+secondstatname+"\n"
                        embed.add_field(name = "Error", value = t)

                        return embed
                    firststat.append(s.get(firststatname))
                    secondstat.append(s.get(secondstatname))
                    sizes.append(s.get("min"))
                    r = lambda: random.randint(0,255)
                    colors.append('#%02X%02X%02X' % (r(),r(),r()))
                    #print(list(s.keys()))
        if len(sizes) == 0:
            t += "No player was found matching the criteria you have given. Note that team abbreviation may overlap with stats specified. If so, then append the full name of the team you want at the very end"
            embed.add_field(name = "Error", value = t)
            return embed
        a = max(sizes)
        team_name = team['name']
        for i in range (0,len(sizes)):
            sizes[i] = 0.1+(sizes[i]/a)
        tt = "Regular season roster graph, "+team_name+" "+str(yr)
        if poff:
            tt = "Playoffs roster graph, "+team_name+" "+str(yr)
        fig = px.scatter(x=firststat, y=secondstat,color=names,size=sizes, color_discrete_sequence = colors[0:len(firststat)])
        fig.update_layout(
        title=tt,
        xaxis=dict(
            title=firststatname,

        ),
        yaxis=dict(
            title=secondstatname,
        ))
        #fig.show()
        fig.write_image('second_figure.png',height=630)
        del fig
        prefix = serversList[str(message.guild.id)]['prefix']
        t += "Circle size corresponds to minutes played.\ncall "+prefix+"rgoptions to see options"
        embed.add_field(name = "Behold the least useful graph you will ever see!", value = t)
        return embed
def ovr(ratings):
    ovr = 0.159 * (ratings['hgt'] - 47.5) + 0.0777 * (ratings['stre'] - 50.2) +0.123 * (ratings['spd'] - 50.8) +0.051 * (ratings['jmp'] - 48.7) + 0.0632 * (ratings['endu'] - 39.9) + 0.0126 * (ratings['ins'] - 42.4) + 0.0286 * (ratings['dnk'] - 49.5) + 0.0202 * (ratings['ft']- 47.0) + 0.0726 * (ratings['tp'] - 47.1) + 0.133 * (ratings['oiq'] - 46.8) + 0.159 * (ratings['diq'] - 46.7) + 0.059 * (ratings['drb']- 54.8) + 0.062 * (ratings['pss'] - 51.3) +0.01 * (ratings['fg'] - 47.0) +0.01 * (ratings['reb'] - 51.4) + 48.5
    fudgeFactor = -10
    if ovr >= 68:
        fudgeFactor = 8
    elif ovr >= 50:
        fudgeFactor = 4 + (ovr - 50) * (4 / 18)
    elif ovr >= 42:
        fudgeFactor = -5 + (ovr - 42) * (9 / 8)
    elif ovr >= 31:
        fudgeFactor = -5 - (42 - ovr) * (5 / 11)

    ovr = round(ovr + fudgeFactor)
    if ovr > 100:

        ovr = 100
    if ovr < 0:
        ovr = 0
    return int(ovr)
def bound(value):
    if value > 100:
        return 100
    if value < 0:
        return 0
    return value
def simprogs(embed, t, commandInfo):
    #need drastically different versions depending on whether or not this is the current roster
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    print("huh")
    season = export['gameAttributes']['season']
    players = export['players']
    #we can deal with formatting later - for now, form the list of players depending on whether or not this is current
    #CURRENT - grab by TID and sort by rosterPosition
    #PAST - grab by final stats TID and sort by OVR
    playerRatings = [] #for TR calc
    playerRatingsfuture = []
    # first lets use the progs text file
    f = open("result.txt")
    print("reading")
    for line in f:
        thing = json.loads(line)
        break


    rosterList = []
    for p in players:
        if p['tid'] == t['tid']:

            age = season - p['born']['year']
            newage = age + 1
            defactoage = int(age)
            if (defactoage > 37):
                defactoage = 37
            if (defactoage < 18):
                defactoage = 18
            playerRatings.append(p['ratings'][-1]['ovr'])
            changedrating = p['ratings'][-1].copy()
            changedrating['season'] += 1
            shifts = random.sample(thing[str(defactoage)],1)[0]

            shindex = 0
            for attr in ['stre','spd','jmp','endu','ins','dnk','ft','fg','tp','oiq','diq','drb','pss','reb']:
                changedrating.update({attr:bound(changedrating[attr] + int(shifts[shindex]))})
                shindex += 1
            
            changedrating['ovr'] = ovr(changedrating)
            rosterList.append([p['pid'], p['rosterOrder'], pull_info.pinfo(p),newage,changedrating])
            playerRatingsfuture.append(changedrating['ovr'])

    rosterList.sort(key=lambda r: r[1])
    oldtr = float(pull_info.team_rating(playerRatings, False))
    newtr = float(pull_info.team_rating(playerRatingsfuture, False))
    text = ""
    overflow = ""
    embed.add_field(name=f"Old team Rating: {oldtr} New team rating: {newtr}", value = "",inline=True)

    added = 0
    for player in rosterList:
        pid = player[0]
        for p in players:
            if p['pid'] == pid:
                #print("got here")
                p = pull_info.pinfo(p)
                added += 1
                change = player[4]['ovr'] - p['ovr']
                if (change > 0):
                    change = '+'+str(change)
                playerLine = f"{p['position']} **{p['name']}** - {player[3] - 1} yo **{p['ovr']}** ➡️ {player[3]} yo **{player[4]['ovr']}** ovr ({change})" + '\n'
                if added <= 15:
                    text += playerLine
                else:
                    overflow += playerLine
    embed.add_field(name='Roster', value=text, inline=False)
    if overflow != "":
        embed.add_field(name='Continued', value=overflow, inline=False)
    
    return embed
    

def roster(embed, t, commandInfo):
    #need drastically different versions depending on whether or not this is the current roster
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    print("huh")
    season = export['gameAttributes']['season']
    players = export['players']
    #we can deal with formatting later - for now, form the list of players depending on whether or not this is current
    #CURRENT - grab by TID and sort by rosterPosition
    #PAST - grab by final stats TID and sort by OVR
    playerRatings = [] #for TR calc
    if commandInfo['season'] == season:
        #CURRENT
        rosterList = []
        for p in players:
            if p['tid'] == t['tid']:

                rosterList.append([p['pid'], p['rosterOrder'], pull_info.pinfo(p)])
                playerRatings.append(p['ratings'][-1]['ovr'])

        rosterList.sort(key=lambda r: r[1])
    else:
        #PAST
        rosterList = []
        for p in players:
            if 'stats' in p:
                stats = p['stats']
                endTeam = -1
                for s in stats:
                    if s['season'] == commandInfo['season']:
                        endTeam = s['tid']
                if endTeam == t['tid']:
                    ratings = p['ratings']
                    ovr = ratings[-1]['ovr']
                    for r in ratings:
                        if r['season'] == commandInfo['season']:
                            ovr = r['ovr']
                    rosterList.append([p['pid'], ovr])
                    playerRatings.append(ovr)
        rosterList.sort(key=lambda r: r[1], reverse = True)

    #rosterList now contains our sorted roster. all that's left is to put it in the embed. but first, we need to do the top parts
    #note that there will be the stats roster if this is -sroster or if it is a past season, the regular roster otherwise
    # Find GM(s) for this team
    teamlist = serversList.get(str(commandInfo['serverId']), {}).get('teamlist', {})
    gm_mentions = []
    for user_id, tid in teamlist.items():
        if tid == t['tid']:
            gm_mentions.append(f"<@!{user_id}>")

    # Find the team's coach (optional feature) and their record with this team
    coach_line = None
    coachData = serversList.get(str(commandInfo['serverId']), {}).get('coaches', {})
    rawTeam = coach_commands._find_team(export, t['tid'])
    for pid, c in coachData.items():
        if c.get('tid', -1) == t['tid'] and rawTeam is not None:
            rec = coach_commands._coach_team_record(c, export, t['tid'])
            ringStr = f", {rec['rings']}\U0001F48D" if rec['rings'] else ''
            coach_line = f"Coach: {c['name']} ({rec['won']}-{rec['lost']}{ringStr})"
            break

    team_rating_value = f"Playoffs: {pull_info.team_rating(playerRatings, True)}/100"
    if gm_mentions:
        team_rating_value += f"\nGM: {', '.join(gm_mentions)}"
    if coach_line:
        team_rating_value += f"\n{coach_line}"
    tr_rank, tr_total = _team_rating_rank(t['tid'], export, commandInfo['season'])
    tr_header = f"Team Rating: {pull_info.team_rating(playerRatings, False)}/100"
    if tr_rank and tr_total:
        tr_header += f" (#{tr_rank} of {tr_total})"
    embed.add_field(name=tr_header, value=team_rating_value, inline=True)

    text = ""
    overflow = ""
    print(commandInfo)
    if commandInfo['command'] == 'roster' and commandInfo['season'] == season:
        #add the payroll
        payroll = 0
        for p in players:
            if p['tid'] == t['tid']:
                payroll += p['contract']['amount']
        if 'releasedPlayers' in export:
            for rp in export['releasedPlayers']:
                if rp['tid'] == t['tid']:
                    payroll += rp['contract']['amount']
        salaryCap = export['gameAttributes']['salaryCap']
        hardCap = serversList[str(commandInfo['serverId'])]['hardcap']

        embed.add_field(name=f"Payroll: ${payroll/1000}M/${salaryCap/1000}M", value=f"Hard Cap: ${hardCap}M", inline=True)
        embed.add_field(name=f"Roster Spots: {export['gameAttributes']['maxRosterSize']-len(rosterList)}", value=f"PTI: {t['pti'][0]} regular season, {t['pti'][1]} playoffs", inline=True)
        roEnabled = serversList.get(str(commandInfo['serverId']), {}).get('rookieoptions') == 'on'
        #now make the standard roster
        added = 0
        for player in rosterList:
            pid = player[0]
            for p in players:
                if p['pid'] == pid:
                    #print("got here")
                    raw_p = p
                    p = pull_info.pinfo(p)
                    added += 1

                    expText = str(p['contractExp'])
                    if roEnabled and raw_p.get('contract', {}).get('rookie') and raw_p.get('draft', {}).get('round') == 1:
                        expText += '+RO'
                    badgeText = f" *{p['skills']}*" if p['skills'] else ''
                    playerLine = f"{p['position']} **{p['name']}** - {commandInfo['season'] - p['born']} yo {p['ovr']}/{p['pot']} | ${p['contractAmount']}M/{expText}{badgeText}" + '\n'
                    if added <= 15 and len(text) + len(playerLine) <= 1000:
                        text += playerLine
                    else:
                        overflow += playerLine
    else:
        if commandInfo['command'] == 'psroster' or commandInfo['command'] == 'sroster' or commandInfo['command'] == 'roster':
            if commandInfo['command'] == 'psroster':
                playoffs = True
            else:
                playoffs = False
            #stats roster
            added = 0
            for player in rosterList:
                pid = player[0]
                for p in players:
                    if p['pid'] == pid:
                        added += 1
                        stats = pull_info.pstats(p, commandInfo['season'], playoffs)
                        p = pull_info.pinfo(p, commandInfo['season'])
                        if stats == None:
                            statLine = '``No stats available.``'
                        else:
                            statLine = f"``{stats['pts']} pts, {stats['orb'] + stats['drb']} reb, {stats['ast']} ast, {stats['per']} PER``"

                        playerLine = f"{p['position']} **{p['name']}** - {commandInfo['season'] - p['born']} yo {p['ovr']}/{p['pot']} | {statLine}" +'\n'
                        if added <= 13 and len(text) < 930:
                            text += playerLine
                        else:
                            overflow += playerLine
        if commandInfo['command'] == 'progster' or commandInfo['command'] == 'proster':
            added = 0
            for player in rosterList:
                pid = player[0]
                for p in players:
                    if p['pid'] == pid:
                        added += 1
                        p2 = pull_info.pinfo(p)
                        pastrating = p2['ovr']
                        pastpot = p2['pot']
                        pastage = commandInfo['season'] - p2['born'] - 1
                        for item in p['ratings']:

                            if item['season'] == season - 1:
                                pastrating = item['ovr']
                                pastpot = item['pot']
                                pastage = item['season'] - p2['born']
                        prog = p2['ovr'] - pastrating
                        if prog > 0:
                            prog = "+"+str(prog)
                        elif prog == 0:
                            prog = "0"
                        elif prog < 0:
                            prog = str(prog)
                        playerLine = f"{p2['position']} **{p2['name']}** - {commandInfo['season'] - p2['born']} yo {p2['ovr']}/{p2['pot']} "+" **("+prog+ ')** (was '+str(pastage)+" yo "+str(pastrating)+"/"+str(pastpot)+')\n'
                        if added <= 13:
                            text += playerLine
                        else:
                            overflow += playerLine
                            
                                    
            
        
    embed.add_field(name='Roster', value=text, inline=False)
    if overflow != "":
        embed.add_field(name='Continued', value=overflow, inline=False)
    
    return embed

def lineup(embed, t, commandInfo):
    #simply grab current lineup
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    players = export['players']
    if commandInfo['season'] != season:
        embed.add_field(name='No Support for Past Seasons', value="Basketball GM doesn't store lineup data for past seasons, so this command is only good for current lineups. You can access past teams with the roster command.")
        return embed
    else:
        lineup = []
        for p in players:
            if p['tid'] == t['tid']:
                lineup.append([p['pid'], p['rosterOrder']])
        lineup.sort(key=lambda l: l[1])

        # Position-mix banner: scan top-5 positions, flag duplicates
        # (e.g. 3 PGs starting) since BBGM doesn't enforce a balanced lineup.
        starter_pids = [l[0] for l in lineup[:5]]
        starter_positions = []
        starter_ovrs = []
        bench_ovrs = []
        for pid in starter_pids:
            for p in players:
                if p['pid'] == pid:
                    rl = p.get('ratings') or []
                    if rl:
                        starter_positions.append(rl[-1].get('pos', '?'))
                        starter_ovrs.append(rl[-1].get('ovr', 0))
                    break
        for l in lineup[5:]:
            for p in players:
                if p['pid'] == l[0]:
                    rl = p.get('ratings') or []
                    if rl:
                        bench_ovrs.append(rl[-1].get('ovr', 0))
                    break
        if starter_positions:
            # Display biggest-first (C-PF-SF-SG-PG) so a missing center
            # shows up as the wrong position in the leftmost slot.
            pos_order = {'C': 0, 'PF': 1, 'SF': 2, 'SG': 3, 'PG': 4}
            sorted_positions = sorted(starter_positions, key=lambda p: pos_order.get(p, 99))
            flags = []
            if 'C' not in sorted_positions:
                flags.append('no C')
            if 'PG' not in sorted_positions:
                flags.append('no PG')
            balanced = sorted_positions == ['C', 'PF', 'SF', 'SG', 'PG']
            if balanced:
                suffix = ' ✓'
            elif flags:
                suffix = f" ⚠ {', '.join(flags)}"
            else:
                suffix = ''  # has both C and PG, just duplicated wings/bigs — no warn
            embed.add_field(name='Starters', value='-'.join(sorted_positions) + suffix, inline=False)

        text = ""
        overflow = ""
        added = 0
        for l in lineup:
            added += 1
            for p in players:
                if p['pid'] == l[0]:
                    p = pull_info.pinfo(p)

                    ptText = None
                    #get the PT info
                    if p['ptModifier'] == 1:
                        ptText = ""
                    if p['ptModifier'] == 1.25:
                        ptText = "(**+** minutes)"
                    if p['ptModifier'] == 0.75:
                        ptText = "(**-** minutes)"
                    if p['ptModifier'] == 1.5:
                        ptText = "(**++** minutes)"
                    if p['ptModifier'] == 0:
                        ptText = "(**0** minutes)"
                    if ptText == None:
                        ptText = f"(custom playing time: **{round(p['ptModifier']*p['ovr'], 2)}** OVR)"
                    
                    line = f"{added}. {p['position']} **{p['name']}** - {p['ovr']}/{p['pot']} {ptText}" + '\n'
                    if added == 5:
                        line += '---' + '\n'
                    if added <= 15:
                        text += line
                    else:
                        overflow += line
        embed.add_field(name='Team Lineup', value=text)
        if overflow != '':
            embed.add_field(name='Continued', value=overflow, inline=False)
        if starter_ovrs and bench_ovrs:
            s_avg = sum(starter_ovrs) / len(starter_ovrs)
            b_avg = sum(bench_ovrs) / len(bench_ovrs)
            drop = s_avg - b_avg
            embed.add_field(
                name='Depth',
                value=f"Starters avg: **{s_avg:.1f}** · Bench avg: **{b_avg:.1f}** · Drop-off: **{drop:+.1f}**",
                inline=False,
            )
        if len(lineup) > 5:
            starters = [a[0] for a in lineup[:5]]
            slist = []
            for p in players:
                if p['pid'] in starters:
                    slist.append(p)
            embed = player_commands.realsynergy(embed, commandInfo,slist, False, addnote = False)
        return embed

def picks(embed, t, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    text = ""
    overflow = ""
    if export['gameAttributes']['phase'] != -1:
        picks.sort(key=lambda p: p['season'])
    added = 0
    for p in picks:
        if p['tid'] == t['tid']:
            
            line = f"{p['season']} round {p['round']} pick"
            if p['pick'] != 0:
                line += f"(#{p['pick']})"
            if p['originalTid'] != p['tid']:
                for team in teams:
                    if team['tid'] == p['originalTid']:
                        abbrev = team['abbrev']
                line += f" ({abbrev})"
            if p['round'] == 1:
                line = '**' + line + '**'
            line += '\n'
            if added < 20:
                text += line
            else:
                overflow += line
            added+=1
    embed.add_field(name=f"{t['abbrev']} Draft Picks", value=text)
    if overflow != "":
        embed.add_field(name='Continued', value=overflow)
    return embed

def ownspicks(embed, t, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    text = ""
    overflow = ""
    picks.sort(key=lambda p: p['season'])
    added = 0
    for p in picks:
        if p['originalTid'] == t['tid']:
            
            line = f"{p['season']} round {p['round']} pick - owned by"
            for team in teams:
                if team['tid'] == p['tid']:
                    abbrev = team['abbrev']
            line += f" {abbrev}"
            if p['round'] == 1:
                line = '**' + line + '**'
            line += '\n'
            if added < 20:
                text += line
            else:
                overflow += line
            added+=1
    embed.add_field(name=f"{t['abbrev']} Draft Pick Owners", value=text)
    if overflow != "":
        embed.add_field(name='Continued', value=overflow, inline=False)
    return embed
def teamcompare(embed, team, commandInfo):
    message = commandInfo['message']
    export = shared_info.serverExports[str(message.guild.id)]
    season = export['gameAttributes']['season']
    players = export['players']
    teams = export['teams']
    if not "," in commandInfo['message'].content:
        return embed
    a = commandInfo['message'].content.split(",")[0]
    b = commandInfo['message'].content.split(",")[1]
    # first team
    commandSeasona = season
    text = a.split(" ")
    for m in text:
        try:
            m = int(m)
            commandSeasona = m
            text.remove(str(commandSeasona))
        except:
            pass
    try: commandTida = serversList[str(message.guild.id)]['teamlist'][str(message.author.id)]
    except KeyError: commandTida = -1
    if commandSeasona != season:
        for t in teams:
            seasons = t['seasons']
            for s in seasons:
                if s['season'] == commandSeasona:
                    teamNames = [s['abbrev'], s['region'], s['name'], s['region'] + ' ' + s['name']]
                    for name in teamNames:
                        if str.lower(name.strip()) in [str(m).lower() for m in text]:
                            commandTida = t['tid']
        if commandTida == -1:
            for t in teams:
                teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
                for name in teamNames:
                    if str.lower(name.strip()) in [str(m).lower() for m in text]:
                        commandTida = t['tid']
    else:
        for t in teams:
            teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
            for name in teamNames:

                if str.lower(name.strip()) in [str(m).lower() for m in text]:
                    commandTida= t['tid']
    # second team
    commandSeasonb = season
    text = b.split(" ")
    for m in text:
        try:
            m = int(m)
            commandSeasonb = m
            text.remove(str(commandSeasonb))
        except:
            pass
    try: commandTidb = serversList[str(message.guild.id)]['teamlist'][str(message.author.id)]
    except KeyError: commandTidb = -1
    if commandSeasonb != season:
        for t in teams:
            seasons = t['seasons']
            for s in seasons:
                if s['season'] == commandSeasonb:
                    teamNames = [s['abbrev'], s['region'], s['name'], s['region'] + ' ' + s['name']]
                    for name in teamNames:
                        if str.lower(name.strip()) in [str(m).lower() for m in text]:
                            commandTidb = t['tid']
        if commandTidb == -1:
            for t in teams:
                teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
                for name in teamNames:
                    if str.lower(name.strip()) in [str(m).lower() for m in text]:
                        commandTidb = t['tid']
    else:
        for t in teams:
            teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
            for name in teamNames:
                if str.lower(name.strip()) in [str(m).lower() for m in text]:
                    commandTidb= t['tid']
    print(commandTida)
    print(commandSeasona)
    print(commandTidb)
    print(commandSeasonb)
    for t in teams:

        if t['tid'] == commandTida:

            ainfo = pull_info.tinfo(t,commandSeasona)
            for s in t['seasons']:
                if s['season'] == commandSeasona:
                    aplayoffResult = pull_info.playoff_result(s['playoffRoundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], s['season'], False)
            for s in t['stats']:
                if s['season'] == commandSeasona:
                    print(s)
                    if not ('playoffs' in s and s['playoffs']):
                        astats = s
            
        if t['tid'] == commandTidb:
            binfo = pull_info.tinfo(t,commandSeasonb)
            for s in t['seasons']:
                if s['season'] == commandSeasonb:
                    bplayoffResult = pull_info.playoff_result(s['playoffRoundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], s['season'], False)
            for s in t['stats']:
                if s['season'] == commandSeasonb:
                    if not ('playoffs' in s and s['playoffs']):
                        bstats = s
    print(astats)
    astatssum = {'Points':astats['pts']/astats['gp'],"FG%":astats['fg']*100/astats['fga'],"TP%":astats['tp']*100/astats['tpa'],'Rebounds':(astats['orb']+astats['drb'])/astats['gp'],
                 'Assists':astats['ast']/astats['gp'],'Steals':astats['stl']/astats['gp'],'Blocks':astats['blk']/astats['gp'],'Turnovers':astats['tov']/astats['gp'],'Opp. Points':astats['oppPts']/astats['gp'],
                 "Opp. FG%":astats['oppFg']*100/astats['oppFga'],"Opp. TP%":astats['oppTp']*100/astats['oppTpa'],'Opp. Rebounds':(astats['oppOrb']+astats['oppDrb'])/astats['gp'],
                 'Opp. Assists':astats['oppAst']/astats['gp'],'Opp. Steals':astats['oppStl']/astats['gp'],'Opp. Blocks':astats['oppBlk']/astats['gp'],'Opp. Turnovers':astats['oppTov']/astats['gp']}
    bstatssum = {'Points':bstats['pts']/bstats['gp'],"FG%":bstats['fg']*100/bstats['fga'],"TP%":bstats['tp']*100/bstats['tpa'],'Rebounds':(bstats['orb']+bstats['drb'])/bstats['gp'],
                 'Assists':bstats['ast']/bstats['gp'],'Steals':bstats['stl']/bstats['gp'],'Blocks':bstats['blk']/bstats['gp'],'Turnovers':bstats['tov']/bstats['gp'],'Opp. Points':bstats['oppPts']/bstats['gp'],
                 "Opp. FG%":bstats['oppFg']*100/bstats['oppFga'],"Opp. TP%":bstats['oppTp']*100/bstats['oppTpa'],'Opp. Rebounds':(bstats['oppOrb']+bstats['oppDrb'])/bstats['gp'],
                 'Opp. Assists':bstats['oppAst']/bstats['gp'],'Opp. Steals':bstats['oppStl']/bstats['gp'],'Opp. Blocks':bstats['oppBlk']/bstats['gp'],'Opp. Turnovers':bstats['oppTov']/bstats['gp']}
    li = ['Points','FG%','TP%','Rebounds','Assists','Steals','Blocks', 'Turnovers']
    astring = ""
    bstring = ""
    for item in li:
        isturnovers = (item == 'Turnovers')
        if (isturnovers and astatssum[item] < bstatssum[item]) or (not isturnovers and astatssum[item] > bstatssum[item]):
            astring = astring + item + ": **"+str(round(astatssum[item],2))+"**\n"
            bstring = bstring + item + ": "+str(round(bstatssum[item],2))+"\n"
        elif (isturnovers and astatssum[item] > bstatssum[item]) or (not isturnovers and astatssum[item] < bstatssum[item]):
            astring = astring + item + ": "+str(round(astatssum[item],2))+"\n"
            bstring = bstring + item + ": **"+str(round(bstatssum[item],2))+"**\n"
        else:
            astring = astring + item + ": "+str(round(astatssum[item],2))+"\n"
            bstring = bstring + item + ": "+str(round(bstatssum[item],2))+"\n"
    aoppstring = ""
    boppstring = ""
    for item in li:
        item = "Opp. "+item
        isturnovers = (item == 'Opp. Turnovers')
        if (isturnovers and astatssum[item] > bstatssum[item]) or (not isturnovers and astatssum[item] < bstatssum[item]):
            aoppstring = aoppstring + item + ": **"+str(round(astatssum[item],2))+"**\n"
            boppstring = boppstring + item + ": "+str(round(bstatssum[item],2))+"\n"
        elif (isturnovers and astatssum[item] < bstatssum[item]) or (not isturnovers and astatssum[item] > bstatssum[item]):
            aoppstring = aoppstring + item + ": "+str(round(astatssum[item],2))+"\n"
            boppstring = boppstring + item + ": **"+str(round(bstatssum[item],2))+"**\n"
        else:
            aoppstring = aoppstring + item + ": "+str(round(astatssum[item],2))+"\n"
            boppstring = boppstring + item + ": "+str(round(bstatssum[item],2))+"\n"
    print(aoppstring)
    embed.add_field(name = ainfo['name']+" "+str(commandSeasona), value = "Record: "+ainfo['record']+"\nPlayoffs: "+aplayoffResult, inline = True)
    embed.add_field(name = binfo['name']+" "+str(commandSeasonb), value = "Record: "+binfo['record']+"\nPlayoffs: "+bplayoffResult, inline = True)
    embed.add_field(name = "filler",value = "Yeh", inline = True)
    embed.add_field(name = ainfo['name']+" "+str(commandSeasona)+" stats", value = astring, inline = True)
    embed.add_field(name = binfo['name']+" "+str(commandSeasonb)+" stats", value = bstring, inline = True)
    embed.add_field(name = "filler",value = "Yeh", inline = True)
    embed.add_field(name = ainfo['name']+" "+str(commandSeasona)+" opponent stats", value = aoppstring, inline = True)
    embed.add_field(name = binfo['name']+" "+str(commandSeasonb)+" opponent stats", value = boppstring, inline = True)
    embed.add_field(name = "filler",value = "Yeh", inline = True)
    aroster = dict()
    arosterdesc = dict()
    
    broster = dict()
    brosterdesc = dict()
    for p in players:
        for s in p['stats']:
            if not s['playoffs']:
                if s['season'] == commandSeasona:
                    if s['tid'] == commandTida:
                        stats = pull_info.pstats(p, s['season'], playoffs=False, qualifiers=False, tids = commandTida)
                        if stats['gp'] > 0:
                            # is on team a
                            if not p['pid'] in aroster:
                                aroster.update({p['pid']:s['min']})
                            else:
                                aroster.update({p['pid']:aroster[p['pid']]+s['min']})
                            for r in p['ratings']:
                                if r['season'] == commandSeasona:
                                    pot = r['pot']
                                    ovr = r['ovr']
                                    pos = r['pos']
                            age = commandSeasona-p['born']['year']
                            
                            
                            arosterdesc.update({p['pid']:"**"+p['firstName']+" "+p['lastName']+"**:\n"+str(ovr)+"/"+str(pot)+", "+str(pos)+", Age "+str(age)+"\n"+
                                                str(round(stats['gp'],0))+" GP, "+str(round(stats['gs'],0))+" GS, \n"+str(round(stats['pts'],1))+" pts, "+str(round(stats['orb']+stats['drb'],1))+" reb, "+str(round(stats['ast'],1))+" ast"})
                if s['season'] == commandSeasonb:
                    if s['tid'] == commandTidb:
                         stats = pull_info.pstats(p, s['season'], playoffs=False, qualifiers=False, tids = commandTidb)
                         if stats['gp'] > 0:
                            # is on team b
                            if not p['pid'] in broster:
                                broster.update({p['pid']:s['min']})
                            else:
                                broster.update({p['pid']:aroster[p['pid']]+s['min']})
                            for r in p['ratings']:
                                if r['season'] == commandSeasonb:
                                    pot = r['pot']
                                    ovr = r['ovr']
                                    pos = r['pos']
                            age = commandSeasonb-p['born']['year']
                           
                            brosterdesc.update({p['pid']:"**"+p['firstName']+" "+p['lastName']+"**:\n"+str(ovr)+"/"+str(pot)+", "+str(pos)+", Age "+str(age)+"\n"+
                                                str(round(stats['gp'],0))+" GP, "+str(round(stats['gs'],0))+" GS, \n"+str(round(stats['pts'],1))+" pts, "+str(round(stats['orb']+stats['drb'],1))+" reb, "+str(round(stats['ast'],1))+" ast"})
  
    print(aroster)
    k = sorted(aroster.keys(), key= lambda x: -aroster[x])
    l = sorted(broster.keys(), key = lambda x: -broster[x])
    stra = ""
    for obj in k[0:min(len(k),10)]:
        stra = stra + arosterdesc[obj]+"\n"
    strb = ""
    for obj in l[0:min(len(l),10)]:
        strb = strb + brosterdesc[obj]+"\n"
    print(k)
    embed.add_field(name = ainfo['name']+" "+str(commandSeasona)+" top players", value = stra, inline = True)
    embed.add_field(name = binfo['name']+" "+str(commandSeasonb)+" top players", value = strb, inline = True)
    return embed
def history(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']
    #GENERIC INFO
    overallRecord = [0, 0]
    totalSeasons = 0
    playoffs = 0
    titles = 0
    finals = 0
    bestRecord = [-1, 5]
    worstRecord = [2,0]

    #PREVIOUS 10 SEASONS
    lines = []
    for t in teams:
        if t['tid'] == team['tid']:
            seasons = t['seasons']
            for s in seasons:
                totalSeasons += 1
                overallRecord[0] += s['won']
                overallRecord[1] += s['lost']
                if s['playoffRoundsWon'] > -1:
                    playoffs += 1
                playoffResult = pull_info.playoff_result(s['playoffRoundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], s['season'], True)
                if playoffResult == '**won championship**':
                    titles += 1
                    finals += 1
                if playoffResult == 'made finals':
                    finals += 1
                try: winP = s['won'] / (s['won'] + s['lost'])
                except ZeroDivisionError: winP = 0
                try:
                    if winP > bestRecord[0] / (bestRecord[0]+bestRecord[1]):
                        bestRecord = [s['won'], s['lost'], s['season']]
                    if winP < worstRecord[0] / (worstRecord[0]+worstRecord[1]):
                        worstRecord = [s['won'], s['lost'], s['season']]
                except ZeroDivisionError: pass
                line = f"{s['season']} - {s['abbrev']} - {s['won']}-{s['lost']}"
                if playoffResult != '':
                    line+= f', {playoffResult}'
                lines.append(line)
                #RETIRED JERSEYS
                retiredJerseys = ""
                if len(t['retiredJerseyNumbers']) == 0:
                    retiredJerseys = "*No retired jerseys.*"
                else:
                    for r in t['retiredJerseyNumbers']:
                        if not 'pid' in r:
                            retiredName = "Unknown"
                        else:
                            for p in players:
                                if p['pid'] == r['pid']:
                                    retiredName = p['firstName'] + ' ' + p['lastName']
                        retiredJerseys += '**#' + str(r['number']) + '** - ' + retiredName + '\n'
    #CALCULATE TOP PLAYERS
    topPlayers = []
    for p in players:
        if 'stats' in p:
            stats = p['stats']
            pts = 0
            reb = 0
            ast = 0
            ewa = 0
            for s in stats:
                if s['tid'] == team['tid'] and s['playoffs'] == False:
                    pts += s['pts']
                    if 'drb' in s:
                        reb += s['drb'] + s['orb']
                    ast += s['ast']
                    if 'ewa' in s:
                        ewa += s['ewa']
            topPlayers.append([f"{p['firstName']} {p['lastName']}", pts, reb, ast, ewa])
    topPlayers.sort(key=lambda t: t[4], reverse=True)
    ewaText = ""
    number = 0
    for t in topPlayers[:5]:
        ewaText += f"{number}. **{t[0]}** - {round(t[4], 1)} EWA" + '\n'
        number+=1
    topPlayers.sort(key=lambda t: t[1], reverse=True)
    ptsText = ""
    number = 0
    for t in topPlayers[:3]:
        ptsText += f"{number}. **{t[0]}** - {t[1]} pts" + '\n'
        number+=1
    topPlayers.sort(key=lambda t: t[2], reverse=True)
    rebText = ""
    number = 0
    for t in topPlayers[:3]:
        rebText += f"{number}. **{t[0]}** - {t[2]} reb" + '\n'
        number+=1
    topPlayers.sort(key=lambda t: t[3], reverse=True)
    astText = ""
    number = 0
    for t in topPlayers[:3]:
        astText += f"{number}. **{t[0]}** - {t[3]} ast" + '\n'
        number+=1

    #compile past seasons
    lines.reverse()
    lines = lines[:15]
    pastSeasonText = '\n'.join(lines)
    
    #embed time
    try: overallWinP = str(round(overallRecord[0]/(overallRecord[0]+overallRecord[1]), 4))[1:]
    except ZeroDivisionError: overallWinP = '0'
    try: playoffsP = str(round(100*(playoffs/totalSeasons), 2))
    except ZeroDivisionError: playoffsP = 0
    embed.add_field(name='Generic', value=f"**Overall record:** {overallRecord[0]}-{overallRecord[1]} ({overallWinP})" + '\n'
                    + f"{totalSeasons} seasons, {playoffs} playoffs ({playoffsP}%)" + '\n'
                    + f"Finals Appearances: {finals}" + '\n' + f"**Championships:** {titles}" + '\n'
                    + f"Best Record: {bestRecord[0]}-{bestRecord[1]} ({bestRecord[2]})" + '\n' + f"Worst Record: {worstRecord[0]}-{worstRecord[1]} ({worstRecord[2]})")
    embed.add_field(name='Retired Jerseys', value=retiredJerseys)
    embed.add_field(name='Top Players', value=ewaText)
    embed.add_field(name='Top Statistics', value=f"**__Points__**" + '\n' + ptsText + '\n' + '**__Rebounds__**' + '\n' + rebText + '\n' + '**__Assists__**' + '\n' + astText)
    embed.add_field(name='Past 15 Seasons', value=pastSeasonText)

    #COACHES (optional feature) - top 3 by total wins with this team
    coachData = serversList.get(str(commandInfo['serverId']), {}).get('coaches', {})
    topCoaches = coach_commands.top_team_coaches(coachData, export, team['tid'], 3)
    if topCoaches:
        coachText = ""
        for i, (name, w, l, rings) in enumerate(topCoaches, 1):
            ringStr = f" {rings}\U0001F48D" if rings else ''
            coachText += f"{i}. **{name}** - {w}-{l}{ringStr}" + '\n'
    else:
        coachText = "*No coach.*"
    embed.add_field(name='Top Coaches', value=coachText)

    return embed

def finances(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    teams = export['teams']
    players = export['players']

    if commandInfo['season'] < season:
        embed.add_field(name='Error', value='Finances cannot be shown for past seasons, only current and future ones.')
    else:
        roster = []
        playerCount = 0
        payroll = 0
        for p in players:
            if p['tid'] == team['tid']:
                if p['contract']['exp'] >= commandInfo['season']:
                    roster.append([p['pid'], p['contract']['amount'], False])
                    payroll+= p['contract']['amount']
                    playerCount += 1
        if 'releasedPlayers' in export:
            releasedPlayers = export['releasedPlayers']
            for rp in releasedPlayers:
                if rp['tid'] == team['tid']:
                    if rp['contract']['exp'] >= commandInfo['season']:
                        roster.append([rp['pid'], rp['contract']['amount'], True, rp['contract']['exp']])
                        payroll+= rp['contract']['amount']
        roster.sort(key=lambda r: r[1], reverse=True)
        text = ""
        overflow = ""
        contractNumber = 1
        number = 0
        if export['gameAttributes']['phase'] >= 7:
            contractNumber = 0
        for r in roster:
            for p in players:
                if p['pid'] == r[0]:
                    if len(p['firstName']) > 0:
                        line = f"{p['ratings'][-1]['pos']} **{p['firstName'][0]}. {p['lastName']}** - $"
                    else:
                        line = f"{p['ratings'][-1]['pos']} **{p['lastName']}** - $"
                    if r[2]:
                        line += f"{r[1]/1000}M/{r[3]-season+contractNumber }Y"
                        line = '*' + line + '*'
                    else:
                        line += f"{p['contract']['amount']/1000}M/{p['contract']['exp']-season+contractNumber }Y"
                    line += '\n'
                    if number < 16:
                        text += line
                    else:
                        overflow += line
                    number += 1
        embed.add_field(name=f"{team['abbrev']} Finances ({commandInfo['season']})", value=text)
        if overflow != "":
            embed.add_field(name='Continued', value=overflow)
        #add basic info
        salaryCap = export['gameAttributes']['salaryCap']/1000
        rosterLimit = export['gameAttributes']['maxRosterSize']
        hype = 0
        for t in teams:
            if t['tid'] == team['tid'] and t.get('seasons'):
                hype = t['seasons'][-1].get('hype', 0)
        embed.add_field(name=f"Payroll: ${payroll/1000}M/${salaryCap}M", value=f"Cap space: ${round((salaryCap-(payroll/1000)), 2)}M" + '\n' + f'Roster spots: {rosterLimit-playerCount}' + '\n' + f'**Hype:** {hype}', inline=False)
    return embed

def seasons(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']
    #season is irrelevant. collect seasons of a team
    lines = []
    for t in teams:
        if t['tid'] == team['tid']:
            seasons = t['seasons']
            for s in seasons:
                info = pull_info.tinfo(t, s['season'])
                line = f"{s['season']} - {info['abbrev']} - {info['record']}"
                playoffResult = pull_info.playoff_result(info['roundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], s['season'], True)
                if playoffResult != "":
                    line += f", {playoffResult}"
                lines.append(line)
    lines.reverse()
    numDivs, rem = divmod(len(lines), 15)
    numDivs += 1
    for i in range(numDivs):
        newLines = lines[(i*15):((i*15)+15)]
        text = '\n'.join(newLines)
        embed.add_field(name='Seasons', value=text, inline = False)
    return embed

def tstats(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']

    if commandInfo['command'] == 'tstats':
        playoffs = False
    else:
        playoffs = True

    #quick check
    gamesPlayed = False
    for t in teams:
        if t['tid'] == team['tid']:
            stats = t['stats']
            for s in stats:
                if s['season'] == commandInfo['season'] and s['playoffs'] == playoffs and s['gp'] > 0:
                    gamesPlayed = True
    if gamesPlayed == False:
        embed.add_field(name='Error', value='No stats found for the specified season or playoff.')
    else:
    
        def rank(season, statName, stat, type, worseBetter=False):
            rank = 1
            for t in teams:
                stats = t['stats']
                for s in stats:
                    if s['season'] == season and s['playoffs'] == playoffs:
                        s['reb'] = s['drb'] + s['orb']
                        s['oppReb'] = s['oppDrb'] + s['oppOrb']
                        if worseBetter:
                            if type == 'total':
                                if s[statName] < stat:
                                    rank += 1
                            if type == 'average':
                                if s[statName]/s['gp'] < stat:
                                    rank += 1
                            if type == 'percent':
                                try: teamAmount = s[statName[0]]/s[statName[1]]
                                except ZeroDivisionError: teamAmount = 10000000000
                                try: origAmount = stat[0] / (stat[1])
                                except ZeroDivisionError: origAMount = 0
                                if teamAmount < origAmount:
                                    rank += 1
                        else:
                            if type == 'total':
                                if s[statName] > stat:
                                    rank += 1
                            if type == 'average':
                                if s[statName]/s['gp'] > stat:
                                    rank += 1
                            if type == 'percent':
                                try: teamAmount = s[statName[0]]/s[statName[1]]
                                except ZeroDivisionError: teamAmount = 10000000000
                                try: origAmount = stat[0] / (stat[1])
                                except ZeroDivisionError: origAmount = 0
                                if teamAmount > origAmount:
                                    rank += 1
            return rank
        
        teamStats = [
            ['**Points**', 'pts', 'average', False], ['Rebounds', 'reb', 'average', False], ['Assists', 'ast', 'average', False], ['Blocks', 'blk', 'average', False], ['Steals', 'stl', 'average', False], ['Turnovers', 'tov', 'average', True], ['FG%', ['fg', 'fga'], 'percent', False], ['3P%', ['tp', 'tpa'], 'percent', False], ['FT%', ['ft', 'fta'], 'percent', False] 
        ]
        opponentStats = [
            ['**Opponent points**', 'oppPts', 'average', True], ['Opp. rebounds', 'oppReb', 'average', True], ['Opp. assists', 'oppAst', 'average', True], ['Opp. blocks', 'oppBlk', 'average', True], ['Opp. steals', 'oppStl', 'average', True], ['Opp. TOV', 'oppTov', 'average', False], ['Opp. FG%', ['oppFg', 'oppFga'], 'percent', True], ['Opp. 3P%', ['oppTp', 'oppTpa'], 'percent', True], ['Opp. FT%', ['oppFt', 'oppFta'], 'percent', True]
        ]

        text = ''
        for ts in teamStats:
            for t in teams:
                if t['tid'] == team['tid']:
                    stats = t['stats']
                    for s in stats:
                        if s['season'] == commandInfo['season'] and s['playoffs'] == playoffs:
                            s['reb'] = s['drb'] + s['orb']
                            s['oppReb'] = s['oppDrb'] + s['oppOrb']
                            if ts[2] == 'percent':
                                statAmount = [s[ts[1][0]], s[ts[1][1]]]
                            else:
                                statAmount = s[ts[1]]
                                if ts[2] == 'average':
                                    statAmount = statAmount/s['gp']
                            statRank = rank(s['season'], ts[1], statAmount, ts[2], ts[3])
            if isinstance(statAmount, list):
                statAmount = (statAmount[0] / statAmount[1]) * 100
            text += f"{ts[0]}: {round(statAmount, 1)} (Rank: #{statRank})" + '\n'
        embed.add_field(name='Team Stats', value=text)

        oppText = ''
        for ts in opponentStats:
            for t in teams:
                if t['tid'] == team['tid']:
                    stats = t['stats']
                    for s in stats:
                        if s['season'] == commandInfo['season'] and s['playoffs'] == playoffs:
                            s['reb'] = s['drb'] + s['orb']
                            s['oppReb'] = s['oppDrb'] + s['oppOrb']
                            if ts[2] == 'percent':
                                statAmount = [s[ts[1][0]], s[ts[1][1]]]
                            else:
                                statAmount = s[ts[1]]
                                if ts[2] == 'average':
                                    statAmount = statAmount / s['gp']
                            statRank = rank(s['season'], ts[1], statAmount, ts[2], ts[3])
            if isinstance(statAmount, list):
                statAmount = (statAmount[0] / +statAmount[1])*100
            oppText += f"{ts[0]}: {round(statAmount, 1)} (Rank: #{statRank})" + '\n'
        embed.add_field(name='Opponent Stats', value=oppText)

    return embed

def sos(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']
    schedule = export['schedule']

    oppWins = 0
    oppLoses = 0
    home = 0
    road = 0
    for s in schedule:
        oppTid = None
        if s['homeTid'] == team['tid']:
            oppTid = s['awayTid']
            home += 1
        if s['awayTid'] == team['tid']:
            oppTid = s['homeTid']
            road += 1
        if oppTid != None:
            for t in teams:
                if t['tid'] == oppTid:
                    oppWins += t['seasons'][-1]['won']
                    oppLoses += t['seasons'][-1]['lost']
    
    sos = oppWins / (oppWins+oppLoses)
    embed.add_field(name='Strength of Schedule', value=f"Remainder of season: {str(round(sos, 3))[1:]}" + '\n' + f"Home games: {home} | Road games: {road}")
    return embed

def schedule(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']
    schedule = export['schedule']

    lines = []
    for s in schedule:
        if s['homeTid'] == team['tid']:
            for t in teams:
                if t['tid'] == s['awayTid']:
                    line = f"**vs** {t['name']} ({t['seasons'][-1]['won']}-{t['seasons'][-1]['lost']})"
                    lines.append(line)
        if s['awayTid'] == team['tid']:
            for t in teams:
                if t['tid'] == s['homeTid']:
                    line = f"**@** {t['name']} ({t['seasons'][-1]['won']}-{t['seasons'][-1]['lost']})"
                    lines.append(line)
    
    numDivs, rem = divmod(len(lines), 15)
    numDivs += 1
    for i in range(numDivs):
        newLines = lines[(i*15):((i*15)+15)]
        text = '\n'.join(newLines)
        embed.add_field(name='Schedule', value=text)
    
    return embed
    
def gamelog(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']
    try: games = export['games']
    except: 
        embed.add_field(name='Error', value='No box scores in file.')
        return embed
    
    lines = []
    number = 1
    for g in games:

        if (g['won']['tid'] == team['tid'] or g['lost']['tid'] == team['tid']) and g['season'] == season:
            #record the game
            homeTeam = g['teams'][0]['tid']
            roadTeam = g['teams'][1]['tid']
            line = f"``{number}.`` "
            for t in teams:
                if t['tid'] == roadTeam:
                    line += f"{t['abbrev']} {g['teams'][1]['pts']}"
                    if g['won']['tid'] == t['tid']:
                        line = '**' + line + '**'
                    line += ' - '
            for t in teams:
                if t['tid'] == homeTeam:
                    teamLine = f"{t['abbrev']} {g['teams'][0]['pts']}"
                    if g['won']['tid'] == t['tid']:
                        teamLine = '**' + teamLine + '**'
                    line+= teamLine
            for gt in g['teams']:
                if gt['tid'] == team['tid']:
                    line += f" ({gt['won']}-{gt['lost']})"
            lines.append(line)
            number += 1
    print(len(lines))
    numDivs, rem = divmod(len(lines), 20)
    numDivs += 1
    for i in range(numDivs):
        newLines = lines[(i*20):((i*20)+20)]
        text = '\n'.join(newLines)
        embed.add_field(name='Game Log', value=text)
    
    return embed

def game(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    try: games = export['games']
    except: 
        embed.add_field(name='Error', value='No box scores in file.')
        return embed
    #just use commandseason as the number
    gameNum = commandInfo['season']
    number = 1
    found = False
    for g in games:
        if g['won']['tid'] == team['tid'] or g['lost']['tid'] == team['tid']:
            if number == gameNum:
                found = True
                number += 1
                gameData = pull_info.game_info(g, export, commandInfo['message'])
                text = f"{gameData['fullScore']}" + '\n' + f"{gameData['quarters']}" + '\n' + '\n' + f"**Top Performers:**" + '\n' + '\n'.join(gameData['topPerformances']) + '\n'
                if g['clutchPlays'] != []:
                    for c in g['clutchPlays']:
                        text += '\n' + '***' + c.split('>')[1].replace('</a', '') + '** ' + c.split('>')[2] + '*'
                embed.add_field(name='Game Summary', value=text)
            else:
                number += 1
    if found == False:
        embed.add_field(name='Error', value='No game found.')
    return embed

def boxscore(embed, team, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    picks = export['draftPicks']
    teams = export['teams']
    players = export['players']
    try: games = export['games']
    except: 
        embed.add_field(name='Error', value='No box scores in file.')
        return embed
    #just use commandseason as the number
    gameNum = commandInfo['season']
    number = 1
    found = False
    for g in games:
        if g['won']['tid'] == team['tid'] or g['lost']['tid'] == team['tid']:
            
            if number == gameNum:
                found = True
                number += 1
                gameData = pull_info.game_info(g, export, commandInfo['message'])
                #boxscore time
                embed.add_field(name='Game Info', value=f"{gameData['fullScore']}" + '\n' + f"{gameData['quarters']}" + '\n' + '\n', inline=False)
                numDivs, rem = divmod(len(gameData['boxScore'][1]), 8)
                numDivs += 1
                for i in range(numDivs):
                    newLines = gameData['boxScore'][1][(i*8):((i*8)+8)]
                    text ='\n'.join(newLines)
                    embed.add_field(name=f"{gameData['away']} Box Score", value=text, inline=False)
                numDivs, rem = divmod(len(gameData['boxScore'][0]), 8)
                numDivs += 1
                for i in range(numDivs):
                    newLines = gameData['boxScore'][0][(i*8):((i*8)+8)]
                    text ='\n'.join(newLines)
                    embed.add_field(name=f"{gameData['home']} Box Score", value=text, inline=False)
                
                

            else:
                number += 1
    if found == False:
        embed.add_field(name='Error', value='No game found.')
    return embed

async def roast(embed, t, commandInfo):
    from ai_media import safe_gemini_call
    from gemini_integration import model

    if not model:
        embed.add_field(name='Roast', value='AI service not available.', inline=False)
        return embed

    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = commandInfo['season']

    # Get team record
    team_obj = None
    for tm in teams:
        if tm['tid'] == t['tid']:
            team_obj = tm
            break

    record = t['record']
    team_name = t['name']

    # Get roster with stats, sorted by minutes
    roster_data = []
    for p in players:
        if p['tid'] == t['tid']:
            s = pull_info.pstats(p, season)
            name = f"{p['firstName']} {p['lastName']}"
            age = season - p['born']['year']
            roster_data.append((name, age, s))
    roster_data.sort(key=lambda x: x[2].get('min', 0), reverse=True)

    roster_lines = []
    for name, age, s in roster_data[:8]:
        roster_lines.append(f"{name} (age {age}): {s['pts']:.1f} PPG, {(s.get('orb',0)+s.get('drb',0)):.1f} RPG, {s['ast']:.1f} APG, {s['fg']:.1f}% FG, {s['tp']:.1f}% 3PT")

    roster_text = '\n'.join(roster_lines)

    prompt = f"""Roast this basketball team in 2-3 sentences. Be funny, savage, and specific to their record, stats, and players. No mercy.

Team: {team_name}
Record: {record}
Top players:
{roster_text}

Keep it short and brutal. No intro, just the roast. Never mention ratings or OVR."""

    result = await safe_gemini_call(prompt)
    if not result:
        embed.add_field(name='Roast', value='AI roast timed out. Even the AI doesn\'t want to watch this team.', inline=False)
        return embed

    if len(result) > 1024:
        result = result[:1021] + "..."
    embed.add_field(name='Roast', value=result, inline=False)
    return embed


def synergylineups(embed, t, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = commandInfo['season']
    players = export['players']

    # Parse sort type from message
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

    # Gather roster players and sort by OVR descending, take top 8
    roster = []
    for p in players:
        if p['tid'] == t['tid']:
            current_ovr = p['ratings'][-1]['ovr']
            roster.append((current_ovr, p))
    roster.sort(key=lambda x: x[0], reverse=True)
    top8 = [p for _, p in roster[:8]]

    if len(top8) < 5:
        embed.add_field(name='Error', value='Need at least 5 players on the roster.')
        return embed

    # Evaluate all C(n,5) combinations
    results = []
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
        results.append((score, d, list(combo)))

    if not results:
        embed.add_field(name='Error', value='Could not calculate synergy for any lineup combination.')
        return embed

    results.sort(key=lambda x: x[0], reverse=True)
    top5 = results[:3]

    for rank, (score, d, combo) in enumerate(top5, 1):
        # Build vertical player list
        s = ""
        for i, p in enumerate(combo, 1):
            pi = pull_info.pinfo(p, season)
            s += f"`{i}.` {pi['position']} **{pi['name']}** — {pi['ovr']}/{pi['pot']}\n"

        s += f"\n**Offense: {round(d['O'], 3)}/1.25** | **Defense: {round(d['D'], 3)}/0.833** | **Rebound: {round(d['Rs'], 3)}/0.5**\n"
        s += f"3pt: {round(d['3'], 1)} | Ath: {round(d['A'], 1)} | BH: {round(d['B'], 1)} | Post: {round(d['Po'], 1)} | Pass: {round(d['Ps'], 1)} | Per: {round(d['P'], 1)}\n"
        s += f"dAth: {round(d['dA'], 1)} | IntD: {round(d['Di'], 1)} | PerD: {round(d['Dp'], 1)} | Reb: {round(d['R'], 1)}"

        header = f"#{rank} — {round(score, 3)} {sort_label} Synergy"
        embed.add_field(name=header, value=s, inline=False)

    # Synergy explanation
    explain = ("Synergy measures how well 5 players complement each other. "
               "**O** = Offense (3pt, Athleticism, Ball Handling, Post, Passing, Perimeter). "
               "**D** = Defense (Athleticism, Interior, Perimeter). "
               "**R** = Rebounding. "
               "Total = O + D + R (max ~2.583). "
               "Top 8 players by OVR are used.")
    embed.add_field(name='What is Synergy?', value=explain, inline=False)

    return embed


def _league_team_ranks(export, season, playoffs=False):
    """Return {tid: {stat_key: (value, rank, total)}} across all active teams.

    Used by -tscout to inject "PPG: 115 (4th of 24)" into the AI prompt so
    scouting reports cite concrete league standing instead of generic
    "good offense" / "bad defense" prose.

    Stats ranked: ppg, opp_ppg, fg_pct, tp_pct, rpg, apg, tov_pg, spg, bpg.
    All are "higher = better" EXCEPT opp_ppg and tov_pg which are inverted.
    """
    inverted = {'opp_ppg', 'tov_pg'}
    keys = ('ppg', 'opp_ppg', 'fg_pct', 'tp_pct', 'rpg', 'apg', 'tov_pg', 'spg', 'bpg')
    by_tid = {}
    for tm in export.get('teams', []):
        if tm.get('disabled'):
            continue
        ts = _team_per_game_stats(tm, season, playoffs=playoffs)
        if ts is None:
            continue
        by_tid[tm['tid']] = ts
    result = {tid: {} for tid in by_tid}
    total = len(by_tid)
    for k in keys:
        ordered = sorted(by_tid.items(), key=lambda kv: kv[1].get(k, 0),
                         reverse=(k not in inverted))
        for rank, (tid, ts) in enumerate(ordered, start=1):
            result[tid][k] = (ts.get(k, 0), rank, total)
    return result


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


def _project_team_finish(export, season, target_tid):
    """Project end-of-season wins + seed + playoff/title likelihood for one
    team. Uses current winp to project remaining games, sorts league by
    projected wins for seed and playoff/title labels. Cheap (no Monte
    Carlo) but credible — anchors the AI prompt with concrete numbers.
    Returns dict or None if data missing."""
    ga = export['gameAttributes']
    games_attr = ga.get('numGames', 82)
    if isinstance(games_attr, list):
        games_per_season = games_attr[-1].get('value', 82) if games_attr else 82
    else:
        games_per_season = games_attr

    projections = []  # (tid, proj_wins, current_wins, current_losses)
    for t in export.get('teams', []):
        if t.get('disabled'):
            continue
        for s in t.get('seasons', []):
            if s.get('season') != season:
                continue
            won = s.get('won', 0); lost = s.get('lost', 0)
            tied = s.get('tied', 0); otl = s.get('otl', 0)
            gp = won + lost + tied + otl
            if gp <= 0:
                # No games yet — fall back to neutral 0.500 projection
                proj_wins = games_per_season * 0.5
            else:
                winp = (won + 0.5 * tied) / gp
                remaining = max(0, games_per_season - gp)
                proj_wins = won + remaining * winp
            projections.append((t['tid'], proj_wins, won, lost))
            break

    if not projections:
        return None
    projections.sort(key=lambda x: -x[1])
    n_teams = len(projections)

    target = next((p for p in projections if p[0] == target_tid), None)
    if target is None:
        return None
    seed = next(i + 1 for i, p in enumerate(projections) if p[0] == target_tid)
    proj_wins = round(target[1])
    proj_losses = games_per_season - proj_wins
    won = target[2]; lost = target[3]

    # Playoff field size — default 16 for standard NBA-style brackets
    series_lens = ga.get('numGamesPlayoffSeries')
    if isinstance(series_lens, list):
        playoff_rounds = len(series_lens)
    else:
        playoff_rounds = 4
    n_playoff = min(n_teams, 2 ** playoff_rounds)

    if seed <= max(4, n_playoff // 4):
        playoff_label = 'Lock'
    elif seed <= n_playoff:
        playoff_label = 'Likely'
    elif seed <= n_playoff + max(2, n_teams // 8):
        playoff_label = 'Bubble'
    else:
        playoff_label = 'Out'

    if seed <= 2:
        title_label = 'Contender'
    elif seed <= 5:
        title_label = 'Dark horse'
    elif seed <= n_playoff:
        title_label = 'Long shot'
    else:
        title_label = '—'

    return {
        'proj_wins': proj_wins,
        'proj_losses': proj_losses,
        'current_wins': won,
        'current_losses': lost,
        'seed': seed,
        'n_teams': n_teams,
        'playoff_label': playoff_label,
        'title_label': title_label,
    }


def _best_lineup_synergy(target_team, players, season, current_season):
    """Top-5 by rosterOrder (or season OVR for past seasons) + synergy
    triple. Returns (lineup_str, synergy_dict) or (None, None)."""
    import player_commands
    is_past = (current_season is not None) and (season != current_season)
    tid = target_team['tid']
    on_team = []
    if is_past:
        for p in players:
            stats = p.get('stats') or []
            if not any(s.get('season') == season and s.get('tid') == tid for s in stats):
                continue
            r = p['ratings'][-1]
            for cand in p.get('ratings', []):
                if cand.get('season') == season:
                    r = cand; break
            on_team.append((r.get('ovr', 0), p, r))
        on_team.sort(key=lambda x: -x[0])
    else:
        for p in players:
            if p.get('tid') != tid:
                continue
            r = p['ratings'][-1]
            ro = p.get('rosterOrder', 9999)
            on_team.append((ro, p, r))
        on_team.sort(key=lambda x: x[0])  # rosterOrder ascending = starters first

    if len(on_team) < 5:
        return None, None
    top5 = on_team[:5]
    positions = [r.get('pos', '?') for _, _, r in top5]
    lineup_str = '-'.join(positions)
    try:
        synergy = player_commands.lineupsynergycalc([p for _, p, _ in top5], season)
    except Exception:
        synergy = None
    return lineup_str, synergy


def _team_per_game_stats(raw_team, season, playoffs=False):
    """Return per-game offensive and opponent stats for a given team-season.

    Returns a dict or None if no games played for that season/phase.
    """
    for s in raw_team.get('stats', []):
        if s.get('season') == season and bool(s.get('playoffs')) == playoffs and s.get('gp', 0) > 0:
            gp = s['gp']
            reb = s.get('drb', 0) + s.get('orb', 0)
            def pct(num, den):
                return (num / den * 100) if den else 0.0
            # Possession estimate (Dean Oliver), averaged over both teams' attempts, so we
            # can pace-adjust scoring into ortg/drtg (points per 100 poss) for NBA matching.
            poss = 0.5 * (
                (s.get('fga', 0) + 0.44 * s.get('fta', 0) - s.get('orb', 0) + s.get('tov', 0)) +
                (s.get('oppFga', 0) + 0.44 * s.get('oppFta', 0) - s.get('oppOrb', 0) + s.get('oppTov', 0))
            )
            pace = poss / gp if gp else 0.0
            return {
                'gp': gp,
                'pace': pace,
                'ortg': (s.get('pts', 0) / poss * 100) if poss else 0.0,
                'drtg': (s.get('oppPts', 0) / poss * 100) if poss else 0.0,
                'ppg': s.get('pts', 0) / gp,
                'opp_ppg': s.get('oppPts', 0) / gp,
                'rpg': reb / gp,
                'apg': s.get('ast', 0) / gp,
                'tov_pg': s.get('tov', 0) / gp,
                'spg': s.get('stl', 0) / gp,
                'bpg': s.get('blk', 0) / gp,
                'fg_pct': pct(s.get('fg', 0), s.get('fga', 0)),
                'tp_pct': pct(s.get('tp', 0), s.get('tpa', 0)),
                'ft_pct': pct(s.get('ft', 0), s.get('fta', 0)),
                'opp_fg_pct': pct(s.get('oppFg', 0), s.get('oppFga', 0)),
                'opp_tp_pct': pct(s.get('oppTp', 0), s.get('oppTpa', 0)),
                'tp_attempts_pg': s.get('tpa', 0) / gp,
            }
    return None


def _top_roster_lines(players, tid, season, n=8, current_season=None, export=None):
    """Top n players (by OVR-at-season) with rich per-player scouting context.

    For the current season, scans players currently on the team (p['tid'] == tid).
    For past seasons, scans players whose stats show they were on the team that
    year, mirroring how -roster handles historical lookups.
    """
    is_past = current_season is not None and season != current_season

    roster = []
    if is_past:
        for p in players:
            stats = p.get('stats') or []
            on_team = any(s.get('season') == season and s.get('tid') == tid for s in stats)
            if not on_team:
                continue
            # Find their OVR for that specific season
            ovr_for_year = p['ratings'][-1]['ovr'] if p.get('ratings') else 0
            for r in p.get('ratings', []):
                if r.get('season') == season:
                    ovr_for_year = r.get('ovr', ovr_for_year)
                    break
            roster.append((ovr_for_year, p))
    else:
        for p in players:
            if p['tid'] == tid:
                cur = p['ratings'][-1]['ovr'] if p.get('ratings') else 0
                roster.append((cur, p))

    roster.sort(key=lambda x: x[0], reverse=True)

    lines = []
    for _, p in roster[:n]:
        pi = pull_info.pinfo(p, season)
        try:
            age = season - p['born']['year']
        except (KeyError, TypeError):
            age = '?'
        skills = pi.get('skills', '') or '—'
        # Use season-specific ratings if available
        r = p['ratings'][-1]
        for cand in p.get('ratings', []):
            if cand.get('season') == season:
                r = cand; break
        trait_checks = [
            (r.get('tp', 0), '3pt'), (r.get('ins', 0), 'post'), (r.get('dnk', 0), 'finishing'),
            (r.get('pss', 0), 'passing'), (r.get('drb', 0), 'handles'), (r.get('diq', 0), 'def-iq'),
            (r.get('spd', 0), 'speed'), (r.get('stre', 0), 'strength'), (r.get('jmp', 0), 'athleticism'),
            (r.get('reb', 0), 'rebounding'), (r.get('oiq', 0), 'off-iq'),
        ]
        trait_checks.sort(key=lambda x: x[0], reverse=True)
        top_traits = ', '.join(name for _, name in trait_checks[:3])
        stats = pull_info.pstats(p, season)
        stat_str = ''
        if stats and stats.get('gp', 0) > 0:
            rpg = (stats.get('orb', 0) + stats.get('drb', 0))
            bits = [
                f"{stats.get('min', 0):.1f} mpg",
                f"{stats['pts']:.1f} pts",
                f"{rpg:.1f} reb",
                f"{stats['ast']:.1f} ast",
                f"{stats.get('stl', 0):.1f} stl",
                f"{stats.get('blk', 0):.1f} blk",
                f"{stats.get('tov', 0):.1f} tov",
            ]
            shoot = []
            if stats.get('fg'): shoot.append(f"{stats['fg']:.0f}% FG")
            if stats.get('tp'): shoot.append(f"{stats['tp']:.0f}% 3PT")
            if stats.get('ft'): shoot.append(f"{stats['ft']:.0f}% FT")
            if stats.get('TS%'): shoot.append(f"{stats['TS%']:.0f}% TS")
            if stats.get('usgp'): shoot.append(f"{stats['usgp']:.0f}% USG")
            if shoot:
                bits.append(', '.join(shoot))
            stat_str = ' || per-game stats: ' + ', '.join(bits)
        lines.append(
            f"{pi['position']} {pi['name']} ({age}yo {pi['ovr']}/{pi['pot']}) "
            f"— strengths: {top_traits} — badges: {skills}{stat_str}"
        )
    return lines, len(roster)


async def tscout(embed, t, commandInfo):
    from ai_media import safe_gemini_call
    from gemini_integration import model

    if not model:
        embed.add_field(name='Scouting Report', value='AI service not available.', inline=False)
        return embed

    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = commandInfo['season']
    current_season = export['gameAttributes']['season']
    players = export['players']

    raw_team = None
    for tm in export['teams']:
        if tm['tid'] == t['tid']:
            raw_team = tm
            break
    if raw_team is None:
        embed.add_field(name='Error', value='Could not resolve team data.', inline=False)
        return embed

    roster_lines, roster_size = _top_roster_lines(players, t['tid'], season, n=8, current_season=current_season, export=export)
    if roster_size == 0:
        embed.add_field(name='Error', value='No roster found for this team-season.', inline=False)
        return embed

    # Star power — top OVR plus a half-bonus for a strong sidekick (so a
    # 75+75 duo reads higher than a 78+62 solo). Range: 1-5 stars.
    top_ovrs = []
    is_past = season != current_season
    for p in players:
        if not p.get('ratings'):
            continue
        if is_past:
            stats = p.get('stats') or []
            if not any(s.get('season') == season and s.get('tid') == t['tid'] for s in stats):
                continue
            ovr_for_year = p['ratings'][-1]['ovr']
            for r in p['ratings']:
                if r.get('season') == season:
                    ovr_for_year = r.get('ovr', ovr_for_year); break
            top_ovrs.append(ovr_for_year)
        else:
            if p['tid'] == t['tid']:
                top_ovrs.append(p['ratings'][-1]['ovr'])
    top_ovrs.sort(reverse=True)
    star_ovr = top_ovrs[0] if top_ovrs else 0
    second_ovr = top_ovrs[1] if len(top_ovrs) > 1 else 0
    # Base stars from top OVR
    if star_ovr >= 80: base_stars = 5
    elif star_ovr >= 75: base_stars = 4
    elif star_ovr >= 70: base_stars = 3
    elif star_ovr >= 65: base_stars = 2
    else: base_stars = 1
    # Sidekick bump: strong #2 nudges the rating up
    sidekick_bump = 0
    if second_ovr >= 75 and base_stars < 5: sidekick_bump = 1
    elif second_ovr >= 70 and base_stars < 5: sidekick_bump = 0  # no bump, just acknowledged
    star_total = min(5, base_stars + sidekick_bump)
    star_emoji = '🌟' * star_total

    ts = _team_per_game_stats(raw_team, season, playoffs=False)
    ranks = _league_team_ranks(export, season, playoffs=False)
    team_ranks = ranks.get(t['tid'], {})

    def _fmt_stat(key, value, fmt='.1f', unit=''):
        r = team_ranks.get(key)
        # opp_ppg/tov_pg rank low-to-high; say "fewest" so neither the AI nor
        # a reader flips the direction ("1st of 24" in TOV reads as most)
        word = ' fewest' if key in ('opp_ppg', 'tov_pg') else ''
        rank_suffix = f" ({_ordinal(r[1])}{word} of {r[2]})" if r else ''
        return f"{format(value, fmt)}{unit}{rank_suffix}"

    stats_block = ''
    if ts:
        stats_block = (
            f"\nTeam stats ({season}) — value with league rank in parens. 1st is always BEST: OPP PPG and TOV rank by fewest, so \"1st fewest\" TOV = best ball security, NOT most turnovers:\n"
            f"  PPG: {_fmt_stat('ppg', ts['ppg'])}\n"
            f"  OPP PPG: {_fmt_stat('opp_ppg', ts['opp_ppg'])}\n"
            f"  FG%: {_fmt_stat('fg_pct', ts['fg_pct'], '.1f', '%')}\n"
            f"  3PT%: {_fmt_stat('tp_pct', ts['tp_pct'], '.1f', '%')} on {ts['tp_attempts_pg']:.1f} att/g\n"
            f"  RPG: {_fmt_stat('rpg', ts['rpg'])}\n"
            f"  APG: {_fmt_stat('apg', ts['apg'])}\n"
            f"  TOV: {_fmt_stat('tov_pg', ts['tov_pg'])}\n"
            f"  STL/BLK: {_fmt_stat('spg', ts['spg'])} / {_fmt_stat('bpg', ts['bpg'])}"
        )

    # Last-season trajectory — feed prior W-L so the AI can describe direction
    trajectory_block = ''
    prior_season = None
    for s in raw_team.get('seasons', []):
        if s.get('season') == season - 1:
            prior_season = s; break
    if prior_season:
        pw = prior_season.get('won', 0); pl = prior_season.get('lost', 0)
        prior_prw = prior_season.get('playoffRoundsWon', -1)
        po_settings = export['gameAttributes']['numGamesPlayoffSeries']
        res = pull_info.playoff_result(prior_prw, po_settings, season - 1)
        prior_tag = res.replace('**', '') if res else 'missed playoffs'
        trajectory_block = f"\nLast season ({season-1}): {pw}-{pl}, {prior_tag}."

    roster_block = '\n'.join(f"- {l}" for l in roster_lines)

    prompt = f"""You are a sharp professional basketball scout. Write a grounded, specific scouting report on the team below — explain HOW this team wins and loses games, who drives it, and what an opponent would game-plan around. No fluff, no hype.

=== TEAM DATA (the only facts you may use) ===
Team: {t['name']} ({t['record']})
Roster size: {roster_size}{trajectory_block}{stats_block}

PLAYERS — each line is one player. The numbers after "per-game stats:" belong to THAT player only:
{roster_block}
=== END DATA ===

STAT FIDELITY — this is the most important rule, breaking it ruins the report:
- Every number you write must be copied EXACTLY, character-for-character, from the data above (a team stat, a league rank, or one player's per-game line).
- NEVER do arithmetic. Do not average, add, combine, convert totals to per-game, or recompute a percentage. Just quote the numbers as written.
- A player's per-game stats belong to him alone — never attribute one player's numbers to another.
- If you don't have a number to support a point, make the point in plain words with NO number. A wrong number is far worse than no number.

Format EXACTLY like this:

**Offensive Identity:** [2-3 sentences — how they create offense (pace, spacing, shot diet, who initiates), tied to named players and the ranks above. Be specific about what truly drives their scoring.]
**Defensive Identity:** [2-3 sentences — scheme tendency, rim protection vs perimeter, where they are stout and where they leak, tied to named players and ranks.]
**Roster Construction:** [2 sentences — star structure, depth, age/trajectory, and how the pieces fit (or do not).]
**Strengths:**
- [a concrete edge grounded in a named player or league rank]
- [a second concrete edge]
**Weaknesses:**
- [a concrete hole an opponent attacks — name a player or cite a rank]
- [a second concrete hole]
**Verdict:** [2 sentences — what this team is this season (contender, bubble, or rebuild) given its trajectory and ranks, and the one thing the season hinges on.]

CRITICAL:
- ONLY reference players named in the data above; never invent a player.
- Never mention OVR/POT or any 0-100 rating — those are not basketball stats. Use the per-game stats, league ranks, and plain basketball description instead.
- Describe players by what their stats and ranks show, in plain terms. Do NOT lean on archetype labels, role nicknames, or catchy titles.
- When a number strengthens a point, quote it exactly (e.g. "21.9 points a night", "38% from three", "3rd in opponent PPG"). Re-read the STAT FIDELITY rules before writing any number.
- If a claim contradicts a league rank shown, drop it. Finish every section."""

    result = await safe_gemini_call(prompt)
    if not result:
        embed.add_field(name='Scouting Report', value='AI scouting timed out. Try again.', inline=False)
        return embed

    # Parse AI response — sections may have prose OR bullet lines after the
    # `**Header:**` marker. We keep bullets verbatim so Discord renders them.
    import re
    sections = {}
    section_order = []
    current_header = None
    current_lines = []
    def _flush():
        if current_header:
            text = '\n'.join(current_lines).strip()
            if text:
                sections[current_header] = text
                section_order.append(current_header)
    for raw_line in result.split('\n'):
        line = raw_line.rstrip()
        if not line.strip():
            if current_header and current_lines and current_lines[-1] != '':
                current_lines.append('')
            continue
        m = re.match(r'\*\*(.+?):\*\*\s*(.*)$', line.strip())
        if m:
            _flush()
            current_header = m.group(1).strip()
            tail = m.group(2).strip()
            current_lines = [tail] if tail else []
        else:
            current_lines.append(line.strip())
    _flush()

    # Star Power leads — always shown, derived from raw OVR (not the AI)
    embed.add_field(name='Star Power', value=star_emoji or '—', inline=True)

    if not section_order:
        # AI didn't format with bold headers — surface the raw text
        body = result[:1021] + '...' if len(result) > 1024 else result
        embed.add_field(name='Scouting Report', value=body, inline=False)
        return embed

    for header in section_order:
        body = sections[header]
        if len(body) > 1024:
            body = body[:1021] + '...'
        embed.add_field(name=header, value=body, inline=False)

    return embed


async def tnbacomp(embed, t, commandInfo):
    from ai_media import safe_gemini_call
    from gemini_integration import model
    import nba_team_data

    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = commandInfo['season']
    current_season = export['gameAttributes']['season']

    raw_team = None
    for tm in export['teams']:
        if tm['tid'] == t['tid']:
            raw_team = tm
            break
    if raw_team is None:
        embed.add_field(name='Error', value='Could not resolve team data.', inline=False)
        return embed

    ts = _team_per_game_stats(raw_team, season, playoffs=False)
    if not ts:
        embed.add_field(name='Error', value='No regular-season stats for this team-season.', inline=False)
        return embed

    if nba_team_data._df is None:
        embed.add_field(name='Error', value='NBA team dataset not loaded.', inline=False)
        return embed

    bbgm_stats = {
        'ortg': ts['ortg'],
        'drtg': ts['drtg'],
        'pace': ts['pace'],
        'tp_attempts_pg': ts['tp_attempts_pg'],
        'fg_pct': ts['fg_pct'],
        'tp_pct': ts['tp_pct'],
        'apg': ts['apg'],
        'tov_pg': ts['tov_pg'],
        'rpg': ts['rpg'],
    }
    similar = nba_team_data.find_similar_teams(bbgm_stats, top_n=2)
    if not similar:
        embed.add_field(name='Error', value='No NBA matches found.', inline=False)
        return embed
    # match_pct now comes back calibrated from find_similar_teams (percentile of closeness).

    # One factual "led by" tag grounds the team — the comp itself is team-vs-team, not player-vs-player.
    roster_lines, _ = _top_roster_lines(export['players'], t['tid'], season, n=1, current_season=current_season)

    # "Led by" — pull just position + name from the first roster line, drop the ovr/pot if zeros
    leader = 'unknown'
    if roster_lines:
        # roster_line format: "POS Name (age yo ovr/pot) — strengths: ... — badges: ... | stats"
        import re
        m = re.match(r'(\S+\s+[^(]+?)\s*\((\d+)yo\s+(\d+)/(\d+)\)', roster_lines[0])
        if m:
            pos_name = m.group(1).strip()
            ovr = int(m.group(3))
            pot = int(m.group(4))
            if ovr > 0 or pot > 0:
                leader = f"{pos_name} ({m.group(2)}yo, {ovr}/{pot})"
            else:
                leader = pos_name

    net = ts['ortg'] - ts['drtg']

    # AI writes a one-line identity for the sim team plus a team-vs-team playstyle blurb
    # for each NBA match. No player analogies — the whole comp is about how the team plays.
    ai_identity = None
    ai_lines = {}
    if model:
        comp_lines = []
        for idx, s in enumerate(similar):
            rec = f"{s['wins']}-{s['losses']}" if s['wins'] is not None else '?'
            s_net = s['ortg'] - s['drtg']
            comp_lines.append(
                f"{idx+1}. {s['season']} {s['team']} ({rec}): {s['ortg']:.1f} ORtg / {s['drtg']:.1f} DRtg "
                f"({s_net:+.1f} net), {s['pace']:.1f} pace, {s['tp_pct']:.1f}% 3PT on {s['tp_attempts_pg']:.1f} att, "
                f"{s['fg_pct']:.1f}% FG"
            )
        comp_list = '\n'.join(comp_lines)
        prompt = f"""You're a basketball analyst comparing a simulated team to the real NBA team-seasons it most resembles. Talk only about TEAM PLAYSTYLE and IDENTITY — tempo (fast or slow), how they score (3-point heavy, paint-bound, balanced), offense vs defense, and overall quality. This is team-to-team: never name or compare individual players.

The matches were chosen by similar pace-adjusted offense and defense (ORtg/DRtg = points scored/allowed per 100 possessions), tempo (pace), and shooting profile.

THE SIM TEAM — {t['name']} ({t['record']}):
{ts['ortg']:.1f} ORtg / {ts['drtg']:.1f} DRtg ({net:+.1f} net), {ts['pace']:.1f} pace, {ts['tp_pct']:.1f}% 3PT on {ts['tp_attempts_pg']:.1f} attempts, {ts['fg_pct']:.1f}% FG

NBA MATCHES:
{comp_list}

Reply using ONLY this format, nothing else:

Identity: [one vivid line on how the SIM team plays — tempo + how they score + how they defend]
1. {similar[0]['season']} {similar[0]['team']} — [one line: how this NBA team plays like the sim team; cite pace, efficiency or shooting]
   Verdict: [short and fun — the vibe or ceiling]
2. {similar[1]['season']} {similar[1]['team']} — [one line]
   Verdict: [short and fun]

Keep every line under 20 words. Punchy, fun, and grounded in the numbers. No player names, no intro, no extra commentary."""
        result = await safe_gemini_call(prompt)
        if result:
            # Parse: an "Identity:" line, then numbered playstyle blurbs each with a "Verdict:" beneath.
            current_idx = None
            buf = {}
            for raw in result.strip().split('\n'):
                line = raw.strip()
                if not line:
                    continue
                low = line.lower().lstrip('-*# ').strip()
                if low.startswith('identity:'):
                    ai_identity = line.split(':', 1)[1].strip()
                    current_idx = None
                elif line[:2] in ('1.', '2.', '3.'):
                    for idx, s in enumerate(similar):
                        if str(s['season']) in line and (s['team'] in line or (s.get('abbrev') and s['abbrev'] in line)):
                            current_idx = idx
                            blurb = line.split('—', 1)[1].strip() if '—' in line else line[2:].strip()
                            buf[current_idx] = {'blurb': blurb, 'verdict': None}
                            break
                elif low.startswith('verdict:') and current_idx is not None:
                    buf[current_idx]['verdict'] = line.split(':', 1)[1].strip()
            ai_lines = buf

    # Sim team's own snapshot: AI identity line (if any) + the dimensions we matched on.
    snapshot = f"*{ai_identity}*\n" if ai_identity else ''
    snapshot += (
        f"{ts['ortg']:.1f} ORtg / {ts['drtg']:.1f} DRtg ({net:+.1f} net) · {ts['pace']:.1f} pace · "
        f"{ts['tp_pct']:.1f}% 3PT ({ts['tp_attempts_pg']:.1f} att) · {ts['fg_pct']:.1f}% FG"
    )
    if leader != 'unknown':
        snapshot += f"\nLed by {leader}"
    if len(snapshot) > 1024:
        snapshot = snapshot[:1021] + '...'
    embed.add_field(name='Your Team', value=snapshot, inline=False)

    # One field per NBA match — the matched dimensions up top, then the playstyle blurb + verdict.
    for idx, s in enumerate(similar):
        rec = f"{s['wins']}-{s['losses']}" if s['wins'] is not None else '?'
        header = f"#{idx+1} · {s['season']} {s['team']} ({rec}) — {s['match_pct']}% match"
        s_net = s['ortg'] - s['drtg']
        srs_tag = f" · {s['srs']:+.1f} SRS" if s.get('srs') is not None else ''
        body = (
            f"{s['ortg']:.1f} ORtg / {s['drtg']:.1f} DRtg ({s_net:+.1f} net) · {s['pace']:.1f} pace · "
            f"{s['tp_pct']:.1f}% 3PT{srs_tag}"
        )
        if s.get('stars'):
            body += f"\nKey men: {s['stars']}"
        if idx in ai_lines:
            b = ai_lines[idx]
            if b.get('blurb'):
                body += f"\n> *{b['blurb']}*"
            if b.get('verdict'):
                body += f"\n> **Verdict:** {b['verdict']}"
        if len(header) > 256:
            header = header[:253] + '...'
        if len(body) > 1024:
            body = body[:1021] + '...'
        embed.add_field(name=header, value=body, inline=False)

    # Methodology — keep it one plain line so the comp is transparent and trustworthy.
    embed.add_field(
        name='How this works',
        value=("Matched on **pace-adjusted offense & defense** (points per 100 possessions), "
               "**tempo**, and **shooting profile** — not raw point totals, so different eras "
               "compare fairly. Match % is overall profile similarity."),
        inline=False,
    )
    return embed





        



    

    
            



                
 
