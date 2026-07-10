from shared_info import serverExports
import pull_info
import basics
import plotly_express as px
import pandas
import random
import math
import plotly.graph_objects as go
from shared_info import trivias
import discord
import shared_info
import json
import hashlib

thing = None

##PLAYER COMMANDS
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
def contracthistory(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    t = ''
    tot = 0
    for p in players:
        if p['pid'] == player['pid']:
            for s in p['salaries']:
                t = t + str(s['season'])+": "+str(s['amount']/1000)+"M\n"
                tot += s['amount']/1000
    t = t + "**Total: "+str(tot)+"M**"
    embed.add_field(name = 'Player Contracts', value = t,inline = False)
    embed.add_field(name = 'Acknowledgements',value = 'credit Happyman (id happy0643_44051) for the suggestion to add this command',inline = False)
    return embed
def addrating(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    for p in players:
        if p['pid'] == player['pid']:
            rating = None
            amount = 0
            for item in commandInfo['message'].content.split(" "):
                if item in ['hgt','stre','endu','jmp','dnk','spd','ins','fg','ft','tp','oiq','diq','reb','pss','drb']:
                    rating = item
                try:
                    amount = int(item)
                except ValueError:
                    pass
            if rating is not None:
                
                p['ratings'][-1][rating] = p['ratings'][-1][rating] + amount
                if p['ratings'][-1][rating] > 100:
                    p['ratings'][-1][rating] = 100
                if p['ratings'][-1][rating] < 0:
                    p['ratings'][-1][rating] = 0
                potdiff = p['ratings'][-1]['pot'] - p['ratings'][-1]['ovr']
                p['ratings'][-1]['ovr'] = ovr(p['ratings'][-1])
                p['ratings'][-1]['pot'] = potdiff + p['ratings'][-1]['ovr']
                if (p['ratings'][-1]['pot'] > 100):
                    p['ratings'][-1]['pot'] = 100
                #skills
                compdict = calccomp(commandInfo['fullplayer'], commandInfo['season'], extra = True)
                if compdict is None:
                    embed.add_field(name='player doesnt have a rating', value='can only addrating for latest season, but cannot find player rating for latest season')
                    return embed
                skillstring = []
                if compdict['3'] > 59:
                    skillstring.append('3')

                if compdict['A'] > 63:
                    skillstring.append('A')
                if compdict['B'] > 68:
                    skillstring.append('B')
                if compdict['Di'] > 57:
                    skillstring.append('Di')
                if compdict['Dp'] > 61:
                    skillstring.append('Dp')
                if compdict['Po'] > 61:
                    skillstring.append('Po')
                if compdict['Ps'] > 63:
                    skillstring.append('Ps')
                if compdict['R'] > 61:
                    skillstring.append('R')
                if compdict['Usage'] > 61:
                    skillstring.append('V')
                print(p['ratings'][-1]['skills'])
                p['ratings'][-1]['skills'] = skillstring
            else:
                embed.add_field(name = 'supply one of the following rating names', value = str(['hgt','stre','endu','jmp','dnk','spd','ins','fg','ft','tp','oiq','diq','reb','pss','drb']))
    embed.add_field(name='Added rating', value='This added rating '+str(amount)+ ' to rating '+str(rating)+' of player '+str(player['name']))
    return embed
def default(embed, player, commandInfo):
    embed.add_field(name='A New Player Command', value=f'This is the template for player commands that have no assigned funtion to fill the embed. Player name: {player["name"]}')
    return (embed)
def formatchange(old, new):
    if new > old:
        return "+"+str(new-old)
    if new == old:
        return 0
    if old > new:
        return "-"+str(old-new)
def pratings(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    season = commandInfo['season']
    s = dict()
    r = dict()
    
    for p in players:
        if p['pid'] == player['pid']:
            if player['retiredYear'] is not None and season > player['retiredYear']:
                season = player['retiredYear']
            
            for rating in p['ratings']:
                if rating['season'] == season - 1:
                    for element in rating:
                        s.update({element:rating[element]})
                if rating['season'] == season:
                    for element in rating:
                        r.update({element:rating[element]})
            break
    if len(s.keys()) > 2:
        
        overallBlock = (f"**Overall:** {r['ovr']} ({formatchange(s['ovr'],r['ovr'])}) \n"
             + f" **Potential:** {r['pot']} ({formatchange(s['pot'],r['pot'])})" )
        physicalBlock = (f"**Height:** {r['hgt']} ({formatchange(s['hgt'],r['hgt'])})" + '\n'
             + f"**Strength:** {r['stre']} ({formatchange(s['stre'],r['stre'])})" + '\n'
             + f"**Speed:** {r['spd']} ({formatchange(s['spd'],r['spd'])})" + '\n'
             + f"**Jumping:** {r['jmp']} ({formatchange(s['jmp'],r['jmp'])})" + '\n'
             + f"**Endurance:** {r['endu']} ({formatchange(s['endu'],r['endu'])})")
        shootingBlock = (f"**Inside:** {r['ins']} ({formatchange(s['ins'],r['ins'])})" + '\n'
                         + f"**Dunks/Layups:** {r['dnk']} ({formatchange(s['dnk'],r['dnk'])})" + '\n'
                         + f"**Free Throws:** {r['ft']} ({formatchange(s['ft'],r['ft'])})" + '\n'
                         + f"**Two Pointers:** {r['fg']} ({formatchange(s['fg'],r['fg'])})" + '\n'
                         + f"**Three Pointers:** {r['tp']} ({formatchange(s['tp'],r['tp'])})")
        skillBlock = (f"**Offensive IQ:** {r['oiq']} ({formatchange(s['oiq'],r['oiq'])})" + '\n'
                      + f"**Defensive IQ:** {r['diq']} ({formatchange(s['diq'],r['diq'])})" + '\n'
                      + f"**Dribbling:** {r['drb']} ({formatchange(s['drb'],r['drb'])})" + '\n'
                      + f"**Passing:** {r['pss']} ({formatchange(s['pss'],r['pss'])})" + '\n'
                      + f"**Rebounding:** {r['reb']} ({formatchange(s['reb'],r['reb'])})")
        embed.add_field(name = 'Overall', value = overallBlock, inline = False)
        embed.add_field(name='Physical', value=physicalBlock)
        embed.add_field(name='Shooting', value=shootingBlock)
        embed.add_field(name='Skill', value=skillBlock)
        return embed
    else:
        if len(r.keys()) == 0:
            poem = "I've traveled to lands reached by few\n"
            poem += "I've braved the waves of the ocean blue\n"
            poem += "I've searched all the lines that I ran through\n"
            poem+= "But I've got no ratings for you.\n\n"
            poem += "I've tracked down hints, and followed clues\n"
            poem += "I've looked at every year, and season too\n"
            poem += "But if you've watched, you already knew\n"
            poem += "That I've got no ratings for you."
            embed.add_field(name="Enjoy a little song, will ya?", value=poem)
            return embed
                        
        else:
            embed.add_field(name="This guy hasn't progged yet", value="And I'm too lazy to supply his ratings")
            return embed
                
def whoidolizes(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    il = []
    for p in export['players']:
        if p['pid'] == player['pid']:
            player = p
            break
    newplayers = []
    for p2 in export['players']:
        isgoated = False
        allstars = 0
        for a in p2['awards']:
            if a['type'] == "All-Star":
                allstars += 1
        peakovrrating = []
        peakovr = 0
        for r in p2['ratings']:
            if r['ovr'] > 70:
                isgoated = True
            if r['ovr'] > peakovr:
                peakovr = r['ovr']
                peakovrrating = r
        
        if allstars > 4:
            isgoated = True
        if isgoated:
            newplayers.append(p2)
    for p in export['players']:
        #random.seed(player['pid'])
        dy = 0
        dr = []
        randomscore = 0
        for p2 in export['players']:
            if p2['pid'] == p['pid']:
                dy = p2['draft']['year']
                dr = p2['ratings'][0]
                dpos = p2['ratings'][0]['pos']
                for i in p2['firstName']+p2['lastName']:
                    randomscore += ord(i)
        idol = "None"
        maxscore = -1000000000
        listofpotential = []

        for p2 in newplayers:
            if p2['draft']['year'] - dy < -10 and p2['draft']['year'] - dy > -30:
                isgoated = False
                allstars = 0
                for a in p2['awards']:
                    if a['type'] == "All-Star":
                        allstars += 1
                peakovrrating = []
                peakovr = 0
                for r in p2['ratings']:
                    if r['ovr'] > 70:
                        isgoated = True
                    if r['ovr'] > peakovr:
                        peakovr = r['ovr']
                        peakovrrating = r
                
                if allstars > 4:
                    isgoated = True

                if isgoated:
                    diffs = []

                    for ratingitem in ['hgt','stre','endu','jmp','spd','fg','ft','tp','ins','dnk','oiq','diq','drb','pss','reb']:
                        diffs.append(peakovrrating[ratingitem]-dr[ratingitem])
                    mean = sum(diffs)/len(diffs)
                    var = 0
                    for item in diffs:
                        var += abs(item-mean)
                    score = -var+500
                    #print(var)
                    if dpos == peakovrrating['pos']:
                        score += 100
                    for l in dpos:
                        if l in peakovrrating['pos']:
                            score += 40
                    for a in p2['awards']:
                        if a['type'] == "Finals MVP":
                            score += 10
                        if a['type'] == "Most Valuable Player":
                            score += 10
                        if a['type'] == "Won Championship":
                            score += 5
                    if peakovrrating['ovr'] < dr['pot']-3:
        
                        score = score - 75
                    if peakovrrating['ovr'] > 70:
                        score += (peakovrrating['ovr']-70)
                    

                    if p['born']['loc'].split(" ")[-1] == p2['born']['loc'].split(" ")[-1]:
                        if not ('USA' in p2['born']['loc'].split(" ")[-1] or 'United States' in p2['born']['loc'].split(" ")[-1]):

                            score += 150
                    listofpotential.append([p2['firstName']+' '+p2['lastName'],score])

        #print(listofpotential)
        if len(listofpotential) == 0:
            idol = "None"
        else:
        
            scorelist = [i[1] for i in listofpotential]
            minimum = min(scorelist)
            for i in listofpotential:
                i[1]= math.exp(i[1]/50)/1000
            scorelist = [i[1] for i in listofpotential]
            listofpotential = sorted(listofpotential, key = lambda x: x[1], reverse = True)
            #print(listofpotential)
            total = sum(scorelist)
            random.seed(p['pid']+1856)
            threshold = random.random()*total
            #print(threshold)
            curtotal = 0
            for i in listofpotential:
                curtotal += i[1]
                if curtotal > threshold:
                    idol =i[0]
                    break
        #print(player)
        if idol == player['firstName']+" "+player['lastName']:
            maxovr = 0
            for r in p['ratings']:
                if r['ovr'] > maxovr:
                    maxovr = r['ovr']
                pos = r['pos']
            il.append((pos+" "+p['firstName']+" "+p['lastName'],maxovr))
            
    il = sorted(il, key = lambda x:-x[1])
    s = ""
    if len(il) == 0:
        embed.add_field(name = "Players who idolize "+player['firstName']+" "+player['lastName'], value = "NO ONE!!!!!!")
        return embed
    for i in il:
        s += i[0]+",  peak ovr "+str(i[1])+"\n"
        if len(s) > 990:
            break
    embed.add_field(name = "Players who idolize "+player['firstName']+" "+player['lastName'], value = s)
    return embed
        
        
def shots(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    playoffs = False
    if commandInfo['commandName'] == 'pshots':
        playoffs = True
    for p in players:
        if p['pid'] == player['pid']:
            d = dict()
            catalog = ['fgAtRim','fgaAtRim','fgMidRange','fgaMidRange','fgLowPost','fgaLowPost','tp','tpa','ft','fta','fg','fga','gp']
            for stat in catalog:
                d.update({stat:0})
            for s in p['stats']:
                if s['season'] == commandInfo['season'] and s['playoffs'] == playoffs:
                    for stat in catalog:
                        d.update({stat:d[stat]+s[stat]})

            if d['fga'] == 0:
                embed.add_field(name = "Error", value = "player did not attempt a shot here")
                return embed
            for item in ['fgaAtRim','fgaMidRange','fgaLowPost','tpa','fta','fga']:
                if d[item] == 0:
                    d.update({item:0.00000001})
            for item in ['gp']:
                if d[item] == 0:
                    d.update({item:0.00001})
            t = "Made per game: "+str(round(d['fgAtRim']/d['gp'],1)) + "\nAttempts per game: "+str(round(d['fgaAtRim']/d['gp'],1))+"\nPercentage: "+str(round(d['fgAtRim']*100/d['fgaAtRim'],1))+"%"
            
            embed.add_field(name = "At rim", value = t, inline = True)
            t = "Made per game: "+str(round(d['fgLowPost']/d['gp'],1)) + "\nAttempts per game: "+str(round(d['fgaLowPost']/d['gp'],1))+"\nPercentage: "+str(round(d['fgLowPost']*100/d['fgaLowPost'],1))+"%"
            
            embed.add_field(name = "Low Post", value = t, inline = True)
            t = "Made per game: "+str(round(d['fgMidRange']/d['gp'],1)) + "\nAttempts per game: "+str(round(d['fgaMidRange']/d['gp'],1))+"\nPercentage: "+str(round(d['fgMidRange']*100/d['fgaMidRange'],1))+"%"
            
            embed.add_field(name = "Mid Range", value = t, inline = True)
            t = "Made per game: "+str(round(d['tp']/d['gp'],1)) + "\nAttempts per game: "+str(round(d['tpa']/d['gp'],1))+"\nPercentage: "+str(round(d['tp']*100/d['tpa'],1))+"%"
            
            embed.add_field(name = "Threes", value = t, inline = True)
            t = "Made per game: "+str(round(d['ft']/d['gp'],1)) + "\nAttempts per game: "+str(round(d['fta']/d['gp'],1))+"\nPercentage: "+str(round(d['ft']*100/d['fta'],1))+"%"
            
            embed.add_field(name = "Free Throws", value = t, inline = True)
            for item in ['fgaAtRim','fgaMidRange','fgaLowPost','tpa','fta']:
                if d[item] < 0.5:
                    d.update({item:0})
            t = "At Rim: "+str(round(d['fgaAtRim']/d['fga']*100,1)) +"%\n"
            t += "Low Post: "+str(round(d['fgaLowPost']/d['fga']*100,1)) +"%\n"
            t += "Mid Range: "+str(round(d['fgaMidRange']/d['fga']*100,1)) +"%\n"
            t += "Three Point: "+str(round(d['tpa']/d['fga']*100,1)) +"%\n"
            t += "Ft/Fg: "+str(round(d['fta']/d['fga'],2)) 
            
            embed.add_field(name = "Shot Distribution", value = t, inline = True)
    return embed
                    
    
    

def stats(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    raw = None
    for p in players:
        if p['pid'] == player['pid']:
            raw = p
    playoffs = commandInfo['commandName'] == 'pstats'
    if commandInfo['commandName'] == 'cstats':
        seasonArg = 'career'
        title = 'Player Career Stats '
    elif playoffs:
        seasonArg = commandInfo['season']
        title = 'Player Playoff Stats '
    else:
        seasonArg = commandInfo['season']
        title = f"{commandInfo['season']} Season Stats "
    s = pull_info.pstats(raw, seasonArg, playoffs=playoffs)

    def team_abbrev(tid):
        name = '?'
        for t in teams:
            if t['tid'] == tid:
                name = t['abbrev']
                for ts in t['seasons']:
                    if ts['season'] == commandInfo['season']:
                        name = ts['abbrev']
        return name

    # Chronological team order for traded players (pstats returns a set)
    if seasonArg == 'career':
        orderedTids = s['teams']
    else:
        orderedTids = []
        for row in raw['stats']:
            if row['season'] == seasonArg and row['playoffs'] == playoffs and row.get('gp', 0) > 0 and row['tid'] not in orderedTids:
                orderedTids.append(row['tid'])
    statsTeams = '('
    for tid in orderedTids:
        statsTeams += team_abbrev(tid) + '/'
    if statsTeams == '(':
        statsTeams = ''
    else:
        statsTeams = statsTeams[:-1] + ')'

    def stat_line(d):
        return f"{d['pts']} pts, {d['orb'] + d['drb']} reb, {d['ast']} ast, {d['blk']} blk, {d['stl']} stl, {d['tov']} tov"

    def eff_line(d):
        return f"{str(d['gp']).replace('.0', '')} GP, {d['min']} MPG, {d['per']} PER, {d['fg']}% FG, {d['tp']} 3PT%, {d['ft']} FT%, {d['eFG%']} eFG%, {d['TS%']} TS%"

    if s['gp'] == 0:
        statsLine = f'*No stats available.*'
        effLine = f'*No stats available.*'
        advLine = None
    elif seasonArg != 'career' and len(orderedTids) > 1:
        # Traded mid-season: one line per team, then the combined total
        statsLine = ''
        effLine = ''
        for tid in orderedTids:
            ts = pull_info.pstats(raw, seasonArg, playoffs=playoffs, tids=tid)
            ab = team_abbrev(tid)
            statsLine += f"**{ab}:** {stat_line(ts)}\n"
            effLine += f"**{ab}:** {eff_line(ts)}\n"
        statsLine += f"**Total:** {stat_line(s)}"
        effLine += f"**Total:** {eff_line(s)}"
    else:
        statsLine = stat_line(s)
        effLine = eff_line(s)
    if s['gp'] != 0:
        ws = float(s.get('ows', 0)) + float(s.get('dws', 0))
        obpm = s.get('obpm', 0)
        dbpm = s.get('dbpm', 0)
        bpm = float(obpm) + float(dbpm)
        advLine = (
            f"**Rate:** {s.get('ortg', 0)} ORtg / {s.get('drtg', 0)} DRtg | {s.get('usgp', 0)} USG%\n"
            f"**BPM:** {obpm:+}/{dbpm:+} OBPM/DBPM ({bpm:+.1f} BPM)\n"
            f"**Value:** {ws:.1f} WS ({s.get('ows', 0)} O / {s.get('dws', 0)} D) | {s.get('vorp', 0)} VORP"
        )
    embed.add_field(name=title+statsTeams, value=statsLine, inline=False)
    embed.add_field(name='Shooting & Efficiency', value=effLine, inline=False)
    if advLine:
        embed.add_field(name='Advanced', value=advLine, inline=False)

    return(embed)

def estimate_wingspan(raw_player, rating_row=None):
    # BBGM generates the hgt rating from true height + a +/-1" wingspan bonus,
    # mapped so 66" (5'6") = 0 and 93" (7'9") = 100. Inverting that and comparing
    # against the listed height recovers the wingspan bonus; adding the ~4.5"
    # NBA-average wingspan-over-height gives an estimated wingspan.
    try:
        rating = (rating_row if rating_row is not None else raw_player['ratings'][-1])['hgt']
        listed = raw_player['hgt']
    except (KeyError, IndexError, TypeError):
        return None
    if 0 < rating < 100:
        impliedHeight = 66 + 27 * rating / 100
        # Rounding snaps off the height-rounding noise, recovering the true
        # short/average/long state; clamping absorbs edited/custom players
        # whose rating doesn't match their listed height.
        arms = max(-1, min(1, round(impliedHeight - listed)))
    else:
        arms = 0  # rating clamped at the extremes, can't invert; assume average
    # Average NBA wingspan is ~1.06x height (taller players have proportionally
    # longer arms); the game's +/-1" arm signal scales 3x to a realistic spread.
    feet, inches = divmod(round(listed * 1.06 + 3 * arms), 12)
    return f"{feet}'{inches}\""

def _combine_noise(pid, event, scale):
    # Deterministic per-player, per-event jitter in [-scale, +scale]. md5 (not
    # Python's hash()) so results are stable across restarts.
    digest = hashlib.md5(f"combine:{pid}:{event}".encode()).digest()
    frac = int.from_bytes(digest[:4], 'big') / 0xFFFFFFFF
    return (frac * 2 - 1) * scale

def _feet_inches(inches):
    inches = round(inches * 4) / 4  # combine measures to the quarter inch
    feet, rem = divmod(inches, 12)
    return f"{int(feet)}'{rem:g}\""

def combine_numbers(raw_player, rating_row=None):
    # Fake-but-deterministic draft combine numbers, calibrated so a 100-rated
    # athlete approaches the real combine records (10.45s lane agility, 2.98s
    # sprint, 48" max vert, 20 bench reps) and positional averages match real
    # combine data (the weight/height terms below — BBGM ratings alone
    # under-separate guards from centers on bench, body fat, and the timed
    # drills).
    try:
        r = rating_row if rating_row is not None else raw_player['ratings'][-1]
        pid = raw_player['pid']
        listed = raw_player['hgt']
        weight = raw_player['weight']
    except (KeyError, IndexError, TypeError):
        return None
    n = lambda event, scale: _combine_noise(pid, event, scale)
    spd = r.get('spd', 50); jmp = r.get('jmp', 50)
    stre = r.get('stre', 50); endu = r.get('endu', 50); drb = r.get('drb', 50)

    barefoot = listed - 1.25 + n('shoes', 0.25)
    if 0 < r.get('hgt', 50) < 100:
        arms = max(-1, min(1, round(66 + 27 * r['hgt'] / 100 - listed)))
    else:
        arms = 0
    wingspan = listed * 1.06 + 3 * arms  # matches the bio/ratings wingspan
    reach = 0.6 * (barefoot + wingspan) + 8 + n('reach', 0.5)
    bodyfat = max(3.5, 4.8 + (weight / listed - 2.55) * 6 - (endu - 50) * 0.025 + n('fat', 0.8))

    lane = 12.2 - (0.6 * spd + 0.4 * drb) * 0.018 + (listed - 78) * 0.03 + n('lane', 0.12)
    sprint = 3.60 - spd * 0.0060 + (listed - 78) * 0.012 + n('sprint', 0.04)
    vertMax = 24.5 + jmp * 0.195 + n('vert', 1.5)
    bench = max(0, round((stre - 15) * 0.22 + (weight - 195) * 0.075 + n('bench', 1.5)))
    # Wonderlic: 0-50 scale, population average ~21. Driven by basketball IQ.
    oiq = r.get('oiq', 50); diq = r.get('diq', 50)
    wonderlic = max(1, min(50, round(8 + (oiq + diq) * 0.14 + n('wonderlic', 3))))

    return {
        'height': barefoot, 'wingspan': wingspan, 'reach': reach,
        'weight': weight + n('weight', 4), 'fat': bodyfat,
        'lane': lane, 'sprint': sprint, 'vert': vertMax, 'bench': bench,
        'wonderlic': wonderlic,
    }

def combine_results(raw_player, rating_row=None):
    c = combine_numbers(raw_player, rating_row)
    if not c:
        return None
    return (
        f"**Height (no shoes):** {_feet_inches(c['height'])} | **Wingspan:** {_feet_inches(c['wingspan'])} | **Reach:** {_feet_inches(c['reach'])}\n"
        f"**Weight:** {c['weight']:.1f} lbs | **Body fat:** {c['fat']:.1f}% | **Wonderlic:** {c['wonderlic']}\n"
        f"**Lane agility:** {c['lane']:.2f}s | **3/4 sprint:** {c['sprint']:.2f}s | **Max vertical:** {round(c['vert'] * 2) / 2:g}\" | **Bench (185 lbs):** {c['bench']} reps"
    )

_INTERVIEW_LINES = {
    'W': ["Asked every team how many rings they're planning on. Rooms loved it.",
          "Tried to win the interview itself. Scouts are still talking about it."],
    '$': ["Asked about the rookie scale in three separate interviews.",
          "Knows the CBA better than some agents. Teams noticed."],
    'F': ["Asked one team about their media market. They wrote it down.",
          "Great quote in every room. Maybe too great."],
    'L': ["Wants to retire wherever he gets drafted. Front offices melted.",
          "Zero drama, zero entourage. Grandma came to the interview."],
}

def prospect_notebook(export, raw_player, r):
    # Interview, scrimmage, and draft-buzz lines for a draft prospect. Fully
    # deterministic: template picks and stat lines hash off pid like the
    # combine numbers do.
    pid = raw_player['pid']
    n = lambda event, scale: _combine_noise(pid, event, scale)
    lines = []

    # Team interviews, flavored by BBGM mood traits
    traits = raw_player.get('moodTraits', [])
    if traits:
        pick = 0 if n('interview', 1) < 0 else 1
        for t in traits[:2]:
            if t in _INTERVIEW_LINES:
                lines.append(f"**Interviews:** {_INTERVIEW_LINES[t][pick]}")
                break
    if not any(l.startswith('**Interviews') for l in lines):
        lines.append("**Interviews:** Polite, rehearsed, forgettable.")

    # Class context: everyone drafted (or to be drafted) the same year
    draft_year = raw_player['draft']['year']
    classmates = [p for p in export['players'] if p['draft']['year'] == draft_year and p.get('ratings')]
    def draft_value(p):
        # Drafts are won on upside: potential dominates, current ability tiebreaks
        r0 = p['ratings'][0]
        return r0['pot'] * 0.8 + r0['ovr'] * 0.2
    classmates.sort(key=draft_value, reverse=True)
    rank = next((i + 1 for i, p in enumerate(classmates) if p['pid'] == pid), len(classmates))

    # Draft buzz: mock position from class rank, arrow from athletic testing
    if rank <= 3: proj = f"top-3 pick (mock #{rank})"
    elif rank <= 14: proj = f"lottery (mock #{rank})"
    elif rank <= 30: proj = f"first round (mock #{rank})"
    elif rank <= 45: proj = f"second round (mock #{rank})"
    else: proj = "fringe draftable — likely undrafted"
    athletic = (r.get('jmp', 50) + r.get('spd', 50)) / 2
    classAthletic = sum((p['ratings'][0].get('jmp', 50) + p['ratings'][0].get('spd', 50)) / 2 for p in classmates) / max(1, len(classmates))
    buzz = f"**Draft Buzz:** Projected {proj}."
    if athletic - classAthletic > 12:
        buzz += " 📈 Testing turned heads."
    elif athletic - classAthletic < -12:
        buzz += " 📉 Ran heavier than the tape."
    lines.append(buzz)

    return '\n'.join(lines)

def bio(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    raw_player = None
    for p in players:
        if p['pid'] == player['pid']:
            stats = pull_info.pstats(p, 'career')
            raw_player = p
    build = None
    if raw_player is not None and raw_player.get('ratings'):
        # Use season-specific ratings if a past season is queried; otherwise latest
        season_ratings = raw_player['ratings'][-1]
        q_season = commandInfo.get('season')
        if q_season is not None:
            for rr in raw_player['ratings']:
                if rr.get('season') == q_season:
                    season_ratings = rr; break
        build, _ = _classify_build(player, season_ratings, commandInfo)
    wingspanText = estimate_wingspan(raw_player) if raw_player is not None else None
    buildValue = player['height']
    if wingspanText:
        buildValue += f", {wingspanText} wingspan"
    if build:
        buildValue += '\n' + build
    embed.add_field(name='Build', value=buildValue, inline=False)
    teamsPlayedFor = ""
    for t in stats['teams']:
        for team in teams:
            if team['tid'] == t:
                teamsPlayedFor += team['abbrev'] + ', '
    teamsPlayedFor = teamsPlayedFor[:-2]
    p = player

    try: statLine = f"{str(stats['gp'])[:-2]} G, {stats['pts']} pts, {stats['orb'] + stats['drb']} reb, {stats['ast']} ast, {stats['per']} PER"
    except: statLine = '*Could not access stats.*'
    leagueBlock = (f"**Experience:** {len(player['seasonsPlayed'])} seasons ({basics.group_numbers(player['seasonsPlayed'])})" + '\n'
    + f"**Career Stats:** {statLine}" + '\n'
    + f'**Teams:** {teamsPlayedFor}')
    embed.add_field(name='League', value=leagueBlock, inline=False)

    if p['deathInfo']['died']:
        ageText = f"Died in {p['deathInfo']['yearDied']} (age {p['deathInfo']['ageDied']})"
    else:
        ageText = str(export['gameAttributes']['season'] - p['born']) + ' yo'
    physicalBlock = (f"**Weight:** {p['weight']} lbs" + '\n'
                     + f"**Age:** {ageText}")
    embed.add_field(name='Physical', value=physicalBlock)

    personalBlock = (f"**Country:** {p['country']}" + '\n'
                     + f"**College:** {p['college']}" + '\n'
                     + f"**Mood Traits:** {p['moodTraits']}")
    embed.add_field(name='Personal', value=personalBlock)

    for bbgmPlayer in players:
        if bbgmPlayer['pid'] == p['pid']:
            draftTid = bbgmPlayer['draft']['tid']
            draftRating = f"{bbgmPlayer['draft']['ovr']}/{bbgmPlayer['draft']['pot']}"
    draftTeam = 'Undrafted'
    for t in teams:
        if t['tid'] == draftTid:
            draftTeam = t['region'] + ' ' + t['name']
    draftBlock = (f"{p['draft']}" + '\n'
                  + f"{draftTeam}" + '\n'
                  + f"{draftRating} at draft")
    embed.add_field(name='Draft', value=draftBlock)

    teamdict = dict()
    for p2 in players:
        if p2['pid'] == player['pid']:
            peakovr = 0
            peakszn = 0
            peakpot = 0
            for r in p2['ratings']:
                if r['ovr'] > peakovr:
                    peakovr = r['ovr']
                    peakszn = r['season']
                    peakpot = r['pot']
                
            for s in p2['stats']:

                if s['playoffs'] == False:
                    if s['tid'] not in teamdict:
                        teamdict.update({s['tid']:[s['season']]})
                    else:
                        l = teamdict[s['tid']]
                        l.append(s['season'])
                        teamdict.update({s['tid']:l})
            k = sorted(teamdict.keys(), key = lambda x:min(teamdict[x]), reverse = False)
            s = ""
            for tid in k:
                abbrev= "WHAAAAA"
                for t in teams:
                    if t['tid'] == tid:
                        abbrev=t['abbrev']
                x = sorted(teamdict[tid])
                years = ""
                index = 0

                while index < len(x):
                    y = x[index]
                    if not y+1 in x:
                        years += str(y)+", "
                        index += 1
                    else:
                        index += 1
                        j = 1
                        while y+j in x:
                            j += 1
                            index += 1
                        years += str(y)+"-"+str(y+j-1)+", "
                if len(years) > 2:
                    years = years[0:-2]
                    
                s += abbrev + ": "+str(years)+"\n"
                
            embed.add_field(name = "Teams", value = s)
            embed.add_field(name = "Peaks", value = str(peakovr)+"/"+str(peakpot)+" at "+str(peakszn))
    random.seed(player['pid'])
    col = random.sample(["Red","Yellow","Green","White","Black","Indigo","Blue","Purple","Gold","Gray","Orange","Magenta"],1)[0]
    food = random.sample(["Fried Chicken","Spaghetti","Cheeseburgers","Pizza","Ice Cream","Chocolate","Cake","Noodle Soup","Steak","Potato Chips","Lemons","Barbeque Ribs","Omelette"],1)[0]
    dy = 0
    dr = []
    randomscore = 0
    for p2 in players:
        if p2['pid'] == p['pid']:
            dy = p2['draft']['year']
            dr = p2['ratings'][0]
            dpos = p2['ratings'][0]['pos']
            for i in p2['firstName']+p2['lastName']:
                randomscore += ord(i)
    idol = "None"
    maxscore = -1000000000
    listofpotential = []
    for p2 in export['players']:
        if p2['draft']['year'] - dy < -10 and p2['draft']['year'] - dy > -30:
            isgoated = False
            allstars = 0
            for a in p2['awards']:
                if a['type'] == "All-Star":
                    if a['season'] < dy-2:
                        allstars += 1
            peakovrrating = []
            peakovr = 0
            for r in p2['ratings']:
                if r['ovr'] > 70:
                    isgoated = True
                if r['ovr'] > peakovr:
                    peakovr = r['ovr']
                    peakovrrating = r
            
            if allstars > 4:
                isgoated = True
            if isgoated:
                diffs = []

                for ratingitem in ['hgt','stre','endu','jmp','spd','fg','ft','tp','ins','dnk','oiq','diq','drb','pss','reb']:
                    diffs.append(peakovrrating[ratingitem]-dr[ratingitem])
                mean = sum(diffs)/len(diffs)
                var = 0
                for item in diffs:
                    var += abs(item-mean)
                score = -var+500
                #print(var)
                if dpos == peakovrrating['pos']:
                        score += 100
                for l in dpos:
                    if l in peakovrrating['pos']:
                        score += 40
                for a in p2['awards']:
                    if a['type'] == "Finals MVP":
                        score += 10
                    if a['type'] == "Most Valuable Player":
                        score += 10
                    if a['type'] == "Won Championship":
                        score += 5
                if peakovrrating['ovr'] < dr['pot']-3:
    
                    score = score - 75
                if peakovrrating['ovr'] > 70:
                    score += (peakovrrating['ovr']-70)

                if player['country'].split(" ")[-1] == p2['born']['loc'].split(" ")[-1]:
                    if not ('USA' in p2['born']['loc'].split(" ")[-1] or 'United States' in p2['born']['loc'].split(" ")[-1]):

                        score += 150
                listofpotential.append([p2['firstName']+' '+p2['lastName'],score])

    print(listofpotential)
    if len(listofpotential) == 0:
        idol = "None"
    else:
    
        scorelist = [i[1] for i in listofpotential]
        minimum = min(scorelist)
        for i in listofpotential:
            i[1]= math.exp(i[1]/50)/1000
        scorelist = [i[1] for i in listofpotential]
        listofpotential = sorted(listofpotential, key = lambda x: x[1], reverse = True)
        print(listofpotential)
        total = sum(scorelist)
        random.seed(player['pid']+1856)
        threshold = random.random()*total
        print(threshold)
        curtotal = 0
        for i in listofpotential:
            curtotal += i[1]
            if curtotal > threshold:
                idol =i[0]
                break
    
                    
    h = random.sample(["Left","Right","Right","Right"],1)[0]
    nname = "None"
    if "nickname" in shared_info.serversList[str(commandInfo['id'])]:
        nicks = shared_info.serversList[str(commandInfo['id'])]['nickname']
        if str(p['pid']) in nicks:
            nname = nicks[str(p['pid'])]
    embed.add_field(name = "Facts", value = "Favorite Color: "+col+"\n Favorite Food: "+food+"\n Idol: "+idol+"\n Handedness: "+h + "\n Nickname: "+nname)
    
    
        
    

    return(embed)

    
_ATOM_LABELS = {
    'shoot': '3pt',
    'slash': 'slashing',
    'playmake': 'playmaking',
    'defend': 'defense',
    'glass': 'rebounding',
    'post': 'post',
    'rim_protect': 'rim protect',
}
_MAIN_ATOMS = ('shoot', 'slash', 'playmake', 'defend', 'glass', 'post', 'rim_protect')


def _classify_build(player, r, commandInfo):
    """Return (build_label, pctiles_for_player) or (None, None) on error.

    Honors commandInfo['season'] for historical lookups — past-season queries
    classify against THAT season's league baselines, not the current one.

    Any exception here is swallowed (and reported to Sentry) so a classifier
    bug just hides the Build field rather than killing the parent command.
    """
    try:
        import player_builds
        export = shared_info.serverExports.get(str(commandInfo.get('id') or commandInfo.get('serverId') or ''))
        if export is None:
            return (None, None)
        current_season = export['gameAttributes']['season']
        query_season = commandInfo.get('season', current_season)
        snapshot_season = None if query_season == current_season else query_season
        dim_stats = player_builds.league_dim_stats_cached(export, season=snapshot_season)
        all_pctiles = player_builds.league_pctiles_cached(export, season=snapshot_season)
        pid = player.get('pid')
        pctiles = all_pctiles.get(pid) if all_pctiles else None
        if pctiles is None:
            # Free agents (and anyone outside the signed-player ranking pool)
            # aren't pre-scored. Rank them on the fly against the signed pool so
            # their build label + percentile context still show.
            distributions = player_builds.league_distributions_cached(export, season=snapshot_season)
            pctiles = player_builds.percentiles_against_pool(r, dim_stats, distributions)
        position = r.get('pos') or player.get('position', '')
        # Primary label: the canonical BBGM archetype, matched league-relative
        # against the same baseline that drives the percentile caption. Falls
        # back to the 2K-style classifier only if the namer yields nothing
        # (e.g. an unrecognized position).
        label = None
        try:
            import archetype
            ovr = r.get('ovr')
            age = None
            born = player.get('born')
            if isinstance(born, dict):
                born = born.get('year')
            if born is not None:
                age = query_season - born
            label = archetype.archetype(r, position, ovr=ovr, age=age, dim_stats=dim_stats, max_adjectives=2) or None
        except Exception:
            label = None
        if not label:
            label = player_builds.classify(r, position, dim_stats=dim_stats, pctiles=pctiles)
        return (label, pctiles)
    except Exception as e:
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("subsystem", "build_classifier")
                scope.set_tag("pid", str(player.get('pid')))
                sentry_sdk.capture_exception(e)
        except Exception:
            pass
        return (None, None)


def _why_this_build_caption(pctiles):
    """Subtle inline caption: top-3 atoms with their percentile rank.

    Returns None when no league pctile context (e.g. free agents)."""
    if not pctiles:
        return None
    items = [(k, pctiles.get(k, 0)) for k in _MAIN_ATOMS]
    items.sort(key=lambda kv: -kv[1])
    return ', '.join(f"{_ATOM_LABELS[k]} {int(round(p))}%" for k, p in items[:3])


def _pctile_fingerprint_for_ai(pctiles):
    """Compact percentile fingerprint string for AI prompts. None if no context."""
    if not pctiles:
        return None
    items = [(k, pctiles.get(k, 0)) for k in _MAIN_ATOMS]
    items.sort(key=lambda kv: -kv[1])
    tops = [(k, p) for k, p in items if p >= 80][:3]
    bottoms = [(k, p) for k, p in items[-3:] if p <= 30]
    parts = []
    if tops:
        parts.append('strengths: ' + ', '.join(f"top {max(1, int(round(100-p)))}% {_ATOM_LABELS[k]}" for k, p in tops))
    if bottoms:
        parts.append('weaknesses: ' + ', '.join(f"bottom {max(1, int(round(p)))}% {_ATOM_LABELS[k]}" for k, p in bottoms))
    return '; '.join(parts) if parts else None


def ratings(embed, player, commandInfo):
    r = player['ratings']

    build, pctiles = _classify_build(player, r, commandInfo)
    wingspanText = None
    try:
        export = shared_info.serverExports[str(commandInfo['id'])]
        for rawPlayer in export['players']:
            if rawPlayer['pid'] == player['pid']:
                wingspanText = estimate_wingspan(rawPlayer, r)
                break
    except (KeyError, TypeError):
        pass
    buildValue = player['height']
    if wingspanText:
        buildValue += f", {wingspanText} wingspan"
    if build:
        caption = _why_this_build_caption(pctiles)
        build_line = f"{build} · {caption}" if caption else build
        buildValue += '\n' + build_line
    embed.add_field(name='Build', value=buildValue, inline=False)

    physicalBlock = (f"**Height:** {r['hgt']}" + '\n'
                     + f"**Strength:** {r['stre']}" + '\n'
                     + f"**Speed:** {r['spd']}" + '\n'
                     + f"**Jumping:** {r['jmp']}" + '\n'
                     + f"**Endurance:** {r['endu']}")
    shootingBlock = (f"**Inside:** {r['ins']}" + '\n'
                     + f"**Dunks/Layups:** {r['dnk']}" + '\n'
                     + f"**Free Throws:** {r['ft']}" + '\n'
                     + f"**Two Pointers:** {r['fg']}" + '\n'
                     + f"**Three Pointers:** {r['tp']}")
    skillBlock = (f"**Offensive IQ:** {r['oiq']}" + '\n'
                  + f"**Defensive IQ:** {r['diq']}" + '\n'
                  + f"**Dribbling:** {r['drb']}" + '\n'
                  + f"**Passing:** {r['pss']}" + '\n'
                  + f"**Rebounding:** {r['reb']}")
    embed.add_field(name='Physical', value=physicalBlock)
    embed.add_field(name='Shooting', value=shootingBlock)
    embed.add_field(name='Skill', value=skillBlock)
    return embed

def pcompare(embed, player, commandInfo):
    if commandInfo['message'].content.count(",") != 1:
        embed.add_field(name = "use , to deliminate exactly 2 players to compare", value = "yeah, you saw the title")
        return embed
    first,second = " ".join(commandInfo['message'].content.split(" ")[1:]).split(",")
    export = shared_info.serverExports[str(commandInfo['id'])]
    fyear = export['gameAttributes']['season']
    for i in first.split(" "):
        try: fyear = int(i)
        except ValueError:
            pass
        if i.lower() == "career":
            fyear = "career"
    syear = export['gameAttributes']['season']
    for i in second.split(" "):
        try: syear = int(i)
        except ValueError:
            pass
        if i.lower() == "career":
            syear = "career"

    if syear == "career" and (not fyear == "career"):
        fyear = "career"
    if fyear == "career" and (not syear == "career"):
        syear = "career"

    
    poff = False

    if commandInfo['message'].content.__contains__("playoff"):
        poff = True
    first = first.replace(str(fyear),"").replace("playoff","")
    second = second.replace(str(syear),"").replace("playoff","")
    # obtain player names
    fp = basics.find_match(first, export,settings =  shared_info.serversList[str(commandInfo['id'])])
    sp = basics.find_match(second, export,settings =  shared_info.serversList[str(commandInfo['id'])])
    if fp is None or sp is None:
        embed.add_field(name='Could not find players', value='Make sure both names are spelled correctly and exist in this league.', inline=False)
        return embed
    fplayer = None
    splayer = None
    for p in export['players']:
        if p['pid'] == fp:
            fplayer = p
        if p['pid'] == sp:
            splayer = p
    if fplayer is None or splayer is None:
        embed.add_field(name='Could not find players', value='Make sure both names are spelled correctly and exist in this league.', inline=False)
        return embed
    if fyear == export['gameAttributes']['season']:
        if fplayer['draft']['year'] > export['gameAttributes']['season']:
            fyear = fplayer['draft']['year']
    if syear == export['gameAttributes']['season']:
        if splayer['draft']['year'] > export['gameAttributes']['season']:
            syear = splayer['draft']['year'] 
    # biographical info

    fname=fplayer['firstName']+" "+fplayer['lastName']
    fposition = fplayer['ratings'][-1]['pos']
    for r in fplayer['ratings']:
        if r['season'] == fyear:
            fposition = r['pos']
    fround = fplayer['draft']['round']
    fpick = fplayer['draft']['pick']
    fdraft = str(fplayer['draft']['round'])+"-"+str(fplayer['draft']['pick'])
    sname=splayer['firstName']+" "+splayer['lastName']
    sposition = splayer['ratings'][-1]['pos']
    for r in splayer['ratings']:
        if r['season'] == syear:
            sposition = r['pos']
    sround = splayer['draft']['round']
    spick = splayer['draft']['pick']
    sdraft = str(splayer['draft']['round'])+"-"+str(splayer['draft']['pick'])
   

    string = ""
    
    if len(fname) > len(sname):
        string += "**"+str(len(fname))+"**"+"|-Length-|"+str(len(sname))+"\n"
    elif len(sname) > len(fname):
        string += str(len(fname))+"|-Length-|"+"**"+str(len(sname))+"**"+"\n"
    else:
        string += str(len(fname))+"|-Length-|"+""+str(len(sname))+""+"\n"
    string += str(fposition)+"|Position|"+""+str(sposition)+""+"\n"
    if sround*1000+spick < fround*1000+fpick:
        string += fdraft+"|Draft Pick|"+"**"+sdraft+"**"+"\n"
    elif sround*1000+spick > fround*1000+fpick:
        string += "**"+fdraft+"**"+"|Draft Pick|"+sdraft+"\n"
    else:
        string += fdraft+"|Draft Pick|"+sdraft+"\n"
    if not fyear == "career":
        fage = fyear - fplayer['born']['year']
        sage = syear - splayer['born']['year']
        string += str(fage)+"|--Age--|"+""+str(sage)+""+"\n"
    embed.add_field(name ="**"+ fname +" ("+str(fyear)+") V.S. "+sname+" ("+str(syear)+")"+"**", value = string.replace("|"," ** | ** "), inline = False)
    string = ""

    for r in ['ovr','pot','hgt','stre','spd','jmp','endu','ins','dnk','ft','fg','tp','oiq','diq','drb','pss','reb']:
        if fyear == 'career':
            peak = 0
            for rat in fplayer['ratings']:

                if rat[r] > peak:
                    peak = rat[r]
            fvalue = peak
            peak = 0
            for rat in splayer['ratings']:
                if rat[r] > peak:
                    peak = rat[r]
            svalue = peak
        else:
            fvalue= 0
            for rat in fplayer['ratings']:
                if rat['season'] == fyear:
                    fvalue = rat[r]
            svalue= 0
            for rat in splayer['ratings']:
                if rat['season'] == syear:
                    svalue = rat[r]

        if fvalue > svalue:
            string += "**"+str(fvalue)+"**|"+r.upper()+"|"+str(svalue)+"\n"
        elif svalue > fvalue:
            string += str(fvalue)+"|"+r.upper()+"|**"+str(svalue)+"**\n"
        else:
            string += str(fvalue)+"|"+r.upper()+"|"+str(svalue)+"\n"
    ratingsnamestring = "Ratings"
    if fyear == "career":
        ratingsnamestring = "Peak Ratings"
    embed.add_field(name =ratingsnamestring, value = string.replace("|"," ** | ** "))
    # STATS - which are complicated
    fgp = 0
    fpoints = 0
    frebs = 0
    fasts = 0
    fstls = 0
    fblks = 0
    ftovs = 0
    fows = 0
    fdws=0
    fper = 0
    fewa=0
    for fs in fplayer['stats']:
        if fs['playoffs'] == poff:
            if fs['season'] == fyear or fyear == 'career':
                fgp += fs['gp']
                fpoints += fs['pts']
                frebs += fs['orb']+fs['drb']
                fasts += fs['ast']
                fstls += fs['stl']
                fblks += fs['blk']
                ftovs += fs['tov']
                fper += fs['per']*fs['gp']
                fewa += fs['ewa']
                fows += fs['ows']
                fdws += fs['dws']
    sgp = 0
    spoints = 0
    srebs = 0
    sasts = 0
    sstls = 0
    sblks = 0
    stovs = 0
    sows = 0
    sdws = 0
    sper = 0
    sewa=0
    for ss in splayer['stats']:
        if ss['playoffs'] == poff:
            if ss['season'] == syear or syear == 'career':
                sgp += ss['gp']
                spoints += ss['pts']
                srebs += ss['orb']+ss['drb']
                sasts += ss['ast']
                sstls += ss['stl']
                sblks += ss['blk']
                stovs += ss['tov']
                sper += ss['per']*ss['gp']
                sewa += ss['ewa']
                sows += ss['ows']
                sdws += ss['dws']
    if fgp == 0:
        fgp = 0.1
    if sgp == 0:
        sgp = 0.1
    fppg = fpoints/fgp
    frpg = frebs/fgp
    fapg = fasts/fgp
    fstls = fstls/fgp
    fblks = fblks/fgp
    ftovs = ftovs/fgp
    fper = fper/fgp
    sppg = spoints/sgp
    srpg = srebs/sgp
    sapg = sasts/sgp
    sstls = sstls/sgp
    sblks = sblks/sgp
    stovs = stovs/sgp
    sper = sper/sgp

    string = ""
    l1 = [fppg,frpg,fapg,fstls,fblks,ftovs,fper,fows,fdws,fewa]
    l2 = [sppg,srpg,sapg,sstls,sblks,stovs,sper,sows,sdws,sewa]
    names = ['pts','reb','ast','stl','blk','tov','per','ows','dws','ewa']
    for item in range (0, len(l1)):
        if l1[item] > l2[item]:
            string += '**'+str(round(l1[item],1))+'**|'+names[item]+"|"+str(round(l2[item],1))+"\n"
        elif l2[item] > l1[item]:
            string +=str(round(l1[item],1))+'|'+names[item]+"|**"+str(round(l2[item],1))+"**\n"
        else:
            string += str(round(l1[item],1))+'|'+names[item]+"|"+str(round(l2[item],1))+"\n"
    string += "**Awards**\n"
    fa = [0,0,0,0,0,0]
    sa = [0,0,0,0,0,0]
    for a in fplayer['awards']:

        if a['type'] == "Most Valuable Player":
            if fyear == a['season'] or fyear == 'career':
                fa[0] += 1
        if a['type'] == "Won Championship":
            if fyear == a['season'] or fyear == 'career':
                fa[1] += 1
        if a['type'] == "Finals MVP":
            if fyear == a['season'] or fyear == 'career':
                fa[2] += 1
        if a['type'] == "Defensive Player of the Year":
            if fyear == a['season'] or fyear == 'career':
                fa[3] += 1
        if a['type'] == "All-Star":
            if fyear == a['season'] or fyear == 'career':
                fa[4] += 1
    if len(fplayer['awards']) == 0:
        fa[5] = 1
    for a in splayer['awards']:
        if a['type'] == "Most Valuable Player":
            if syear == a['season'] or syear == 'career':
                sa[0] += 1
        if a['type'] == "Won Championship":
            if syear == a['season'] or syear == 'career':
                sa[1] += 1
        if a['type'] == "Finals MVP":
            if syear == a['season'] or syear == 'career':
                sa[2] += 1
        if a['type'] == "Defensive Player of the Year":
            if syear == a['season'] or syear == 'career':
                sa[3] += 1
        if a['type'] == "All-Star":
            if syear == a['season'] or syear == 'career':
                sa[4] += 1

    if len(splayer['awards']) == 0:
        sa[5] = 1
    names = ['MVP','Rings','FMVP','DPOY','AS','Player Exists']
    for item in range (0, len(fa)):
        if fa[item] > sa[item]:
            string += '**'+str(fa[item])+'**|'+names[item]+"|"+str(sa[item])+"\n"
        elif sa[item] > fa[item]:
            string +=str(fa[item])+'|'+names[item]+"|**"+str(sa[item])+"**\n"
        else:
            string += str(fa[item])+'|'+names[item]+"|"+str(sa[item])+"\n"
    embed.add_field(name = "Stats", value = string.replace("|"," ** | ** "))
    string = ""
    if (fyear != 'career'):
        
        compdict1 = calccomp(fplayer,fyear, extra = True)
        compdict2 = calccomp(splayer,syear, extra = True)
        for r in compdict1.keys():
            if not 'syn' in r:
                if compdict1[r] > compdict2[r]:
                    string += '**'+str(round(compdict1[r],2))+'**|'+r+"|"+str(round(compdict2[r],2))+"\n"
                else:
                    string +=str(round(compdict1[r],2))+'|'+r+"|**"+str(round(compdict2[r],2))+"**\n"

        embed.add_field(name = "Composites", value = string.replace("|"," ** | ** "), inline = True)
    return embed
    

def adv(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    poffs = False
    if commandInfo['message'].content.__contains__('padv'):
        poffs = True
    for p in players:
        if p['pid'] == player['pid']:
            s = pull_info.pstats(p, commandInfo['season'], poffs)
    statsTeams = '('
    for tid in s['teams']:
        name = '?'
        for t in teams:
            if t['tid'] == tid:
                name = t['abbrev']
                for season in t['seasons']:
                    if season['season'] == commandInfo['season']:
                        name = season['abbrev']
        statsTeams += name + '/'
    if statsTeams == '(':
        statsTeams = ''
    else:
        statsTeams = statsTeams[:-1] + ')'
    if s['gp'] == 0:
        statsLine = f'*No stats available.*'
        effLine = f'*No stats available.*'
        shootingLine = '*No stats available.*'
    else:
        statsLine = f"{str(s['gp']).replace('.0', '')} GP, {s['min']} MPG, {s['per']} PER, {s['ewa']} EWA, {s['obpm']+s['dbpm']} BPM ({s['obpm']} OBPM, {s['dbpm']} DBPM), {s['vorp']} VORP"
        effLine = f"{s['ows']+s['dws']} WS ({s['ows']} OWS, {s['dws']} DWS), {str(round(((s['ows']+s['dws'])/(s['min']*s['gp']))*48, 3)).replace('0.', '.')} WS/48, {s['ortg']} ORTG, {s['drtg']} DRTG, {s['usgp']}% USG, {s['pm100']} +/- per 100 pos., {s['onOff100']} on/off per 100 pos."
        shootingLine = f"{s['fg']}% FG, {s['tp']}% 3P, {s['ft']}% FT, {s['at-rim']}% at-rim, {s['low-post']}% low-post, {s['mid-range']}% mid-range \n {s['dd']} double-doubles, {s['td']} triple doubles"
    names = f"{commandInfo['season']} Advanced Stats {statsTeams}"
    if poffs:
        names = f"{commandInfo['season']} Playoff Advanced Stats {statsTeams}"
    print(names)
    embed.add_field(name=names, value=statsLine, inline=False)
    embed.add_field(name='Team-Based', value=effLine, inline=False)
    embed.add_field(name='Shooting and Feats', value=shootingLine, inline=False)

    return embed
def answer(embed, player, commandInfo):
    embed = discord.Embed(title="Trivia", description="Guess who")
    channel = commandInfo['message'].channel
    if channel not in trivias:
        embed.add_field(name='No trivia active', value="There's no trivia running in this channel. Use -trivia to start one!")
        return embed
    trivia_data = trivias[channel]
    correct_name = trivia_data['name'].lower()
    guess = commandInfo['message'].content.split(None, 1)
    if len(guess) < 2:
        embed.add_field(name='Usage', value="Use -answer [player name] to submit your guess!")
        return embed
    guess_text = guess[1].strip().lower()
    # Remove the player name that process_text matched — the guess is whatever the user typed after -answer
    # But since process_text already matched a player, we need to use the raw message
    # Partial match: check if guess is contained in the answer or vice versa
    if guess_text in correct_name or correct_name.split()[-1] == guess_text:
        embed = discord.Embed(title="Trivia - Correct!", description=f"The answer was **{trivia_data['name']}**!", color=0x00ff00)
        del trivias[channel]
        return embed
    else:
        wrong_count = trivia_data.get('wrong_count', 0) + 1
        trivia_data['wrong_count'] = wrong_count
        if wrong_count >= 3:
            name = trivia_data['name']
            embed = discord.Embed(title="Trivia - Revealed!", description=f"The answer was **{name}**!", color=0xff6600)
            embed.add_field(name='Out of guesses', value="Better luck next time! Use -trivia to start a new one.")
            del trivias[channel]
        else:
            guesses_left = 3 - wrong_count
            embed.add_field(name='Nope!', value=f"That's not right! You have **{guesses_left}** guess{'es' if guesses_left > 1 else ''} left. Use -hint for a clue.")
        return embed

async def hint(embed, player, commandInfo):
    embed = discord.Embed(title="Trivia", description="Guess who")
    channel = commandInfo['message'].channel
    if channel not in trivias:
        embed.add_field(name='Hint', value="Here's a hint for you: use -trivia to start a trivia in this channel, then you can use this command!")
        return embed
    trivia_data = trivias[channel]
    hint_count = trivia_data.get('hint_count', 0)
    if hint_count == 0:
        # Hint 1: AI-generated cryptic clue
        p_data = trivia_data.get('player_data', {})
        position = p_data.get('position', 'Unknown')
        height = p_data.get('height', 'Unknown')
        college = p_data.get('college', 'Unknown')
        country = p_data.get('country', 'Unknown')
        draft_round = p_data.get('draftRound', 'Unknown')
        seasons_count = len(p_data.get('seasonsPlayed', []))
        awards_count = len(p_data.get('awards', []))
        peak_ovr = p_data.get('peakOvr', 0)
        prompt = f"Give a 1-2 sentence cryptic clue about a basketball player with these attributes without revealing their name or team: Position: {position}, Height: {height}, College: {college}, Country: {country}, Draft round: {draft_round}, Seasons played: {seasons_count}, Awards: {awards_count}, Peak overall rating: {peak_ovr}. Be creative and mysterious."
        try:
            from ai_media import safe_gemini_call
            clue = await safe_gemini_call(prompt)
            if clue:
                embed.add_field(name='Hint 1 - Cryptic Clue', value=clue)
            else:
                embed.add_field(name='Hint 1 - Cryptic Clue', value=f"This player is a {position} standing {height} tall, hailing from {country}.")
        except:
            embed.add_field(name='Hint 1 - Cryptic Clue', value=f"This player is a {position} standing {height} tall, hailing from {country}.")
        trivia_data['hint_count'] = 1
    elif hint_count == 1:
        # Hint 2: Initials
        name = trivia_data['name']
        init = [x[0] for x in name.split(" ")]
        embed.add_field(name='Hint 2 - Initials', value=".".join(init) + ".")
        trivia_data['hint_count'] = 2
    elif hint_count == 2:
        # Hint 3: Team name
        p_data = trivia_data.get('player_data', {})
        tid = p_data.get('tid', -1)
        export = shared_info.serverExports[str(commandInfo['id'])]
        team_name = "Unknown"
        for t in export['teams']:
            if t['tid'] == tid:
                team_name = t['region'] + ' ' + t['name']
                break
        if tid == -1:
            team_name = "Free Agent"
        elif tid == -3:
            team_name = "Retired"
        embed.add_field(name='Hint 3 - Team', value=f"This player's last team: **{team_name}**")
        trivia_data['hint_count'] = 3
    else:
        name = trivia_data['name']
        embed = discord.Embed(title="Trivia - Revealed!", description=f"The answer was **{name}**!", color=0xff6600)
        embed.add_field(name='Out of hints', value="Better luck next time! Use -trivia to start a new one.")
        del trivias[channel]
    return embed
def progs(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    lines = []
    fname = ""
    for p in players:
        if p['pid'] == player['pid']:
            fname = p['firstName']
            ratings = p['ratings']
            for r in ratings:
                line = f"{r['season']} - {player['name']} - {r['season'] - player['born']} yo {r['ovr']}/{r['pot']} {' '.join(r['skills'])}"
                lines.append(f"{r['season']} - {player['name']} - {r['season'] - player['born']} yo {r['ovr']}/{r['pot']} {' '.join(r['skills'])}")
    numDivs, rem = divmod(len(lines), 20)
    numDivs += 1
    for i in range(numDivs):
        newLines = lines[(i*20):((i*20)+20)]
        text = '\n'.join(newLines)
        if len(text) > 1020:
            text = text.replace(fname, fname[0]+".")
        embed.add_field(name='Player Progressions', value=text)
    return embed

def hstats(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    playoffs = False
    allstaryears = []
    mvpyears = []
    fmvpyears = []
    championshipyears = []
    for p in players:
        if p['pid'] == player['pid']:
            for a in p['awards']:
                if a['type'] == 'All-Star':
                    allstaryears.append(a['season'])
                if a['type'] == "Most Valuable Player":
                    mvpyears.append(a['season'])
                if a['type'] == 'Finals MVP':
                    fmvpyears.append(a['season'])
                if a['type'] == "Won Championship":
                    championshipyears.append(a['season'])
    teams = export['teams']
    if commandInfo['message'].content.split(" ")[0].__contains__('phs') or commandInfo['message'].content.split(" ")[0].__contains__('phstats'):
        playoffs = True
    lines = []
    for season in player['seasonsPlayed']:
        for p in players:
            if p['pid'] == player['pid']:
                stats = pull_info.pstats(p, season, playoffs)

        if stats['gp'] > 0:
            teamText = '('
            for tid in stats['teams']:
                for t in teams:
                    if t['tid'] == tid:
                        t = pull_info.tinfo(t, season)
                        teamText += t['abbrev'] + '/'
            teamText = teamText[:-1] + ')'
            line = f"**{season}** {teamText} - {stats['pts']} pts, {stats['reb']} reb, {stats['ast']} ast, {stats['stl']} stl, {stats['blk']} blk, {stats['per']} PER"
            if not playoffs:
                if season in mvpyears:
                    line += " ⭐"
                elif season in allstaryears:
                    line += " ★"
            if playoffs:
                if season in fmvpyears:
                    line += " 🏅"
                if season in championshipyears:
                    line += " 💍"
                
            lines.append(line)
    numDivs, rem = divmod(len(lines), 10)
    numDivs += 1
    for i in range(numDivs):
        newLines = lines[(i*10):((i*10)+10)]
        text = '\n'.join(newLines)
        embed.add_field(name='Player Stats', value=text, inline=False)
    return embed  

def awards(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    lines = []
    for p in players:
        if p['pid'] == player['pid']:
            awards = p['awards']
            totalAwards = []
            for a in awards:
                totalAwards.append(a['type'])
            totalAwards = list(dict.fromkeys(totalAwards))
            for t in totalAwards:
                numAward = 0
                awardSeasons = []
                for a in awards:
                    if a['type'] == t:
                        numAward += 1
                        awardSeasons.append(str(a['season']))
                awardYears = ', '.join(awardSeasons)
                awardYears = '(' + awardYears + ')'
                awardYears = awardYears.replace(', )', ')')
                lines.append(f'{numAward}x {t} {awardYears}')
    if lines == []:
        numAward = 1
        t = "Player Exists"
        awardYears = str(commandInfo['season'])
        lines.append(f'{numAward}x {t} ({awardYears})')
    currentLines = []
    for line in lines:
        test = '\n'.join(currentLines + [line])
        if len(test) > 1024 and currentLines:
            embed.add_field(name='Player Awards', value='\n'.join(currentLines), inline=False)
            currentLines = [line]
        else:
            currentLines.append(line)
    if currentLines:
        embed.add_field(name='Player Awards', value='\n'.join(currentLines), inline=False)
    return embed
def compare(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    #print(commandInfo)
    players = export['players']
    teams = export['teams']
    tocompare = None
    trueplayer = None
    #print(player)
    for play in players:
        if player["pid"] == play["pid"]:
            trueplayer = play
    if trueplayer is None or not trueplayer.get('ratings'):
        embed.add_field(name='Player Not Found', value='Could not locate that player or they have no ratings on file.', inline=False)
        return embed
    for r in trueplayer['ratings']:

        if r['season'] == commandInfo['season']:
            tocompare = r
    if tocompare == None:
        if trueplayer['retiredYear'] == None:
            tocompare = trueplayer['ratings'][-1]
            commandInfo.update({"season":tocompare["season"]})
        else:
            peakovr = 0
            for item in trueplayer['ratings']:
                if item['ovr'] > peakovr:
                    tocompare = item
                    peakovr = item['ovr']
    page = commandInfo["season"]-player["born"]
    mindifference = 10000000
    players2 = []

    for p in players:
        
        if not p["pid"] == trueplayer["pid"]:
            if export['gameAttributes']['season'] > p['draft']['year']:
        
                for r in p['ratings']:
                    age = r['season']-p['born']['year']
                    if age == page:
                        dif = 0
                        for i in ["hgt","stre","endu","reb","drb","pss","oiq","diq","fg","ft","tp","ins","dnk","jmp","spd"]:
                            if i in ["hgt","oiq","diq","stre","jmp","spd","drb","dnk","tp"]:
                                dif += (r[i]-tocompare[i])**2
                            else:
                                dif += 0.5*(r[i]-tocompare[i])**2
                        dif += 5*(r["ovr"]-tocompare["ovr"])**2
                        players2.append((p,r['season'],dif,p['ratings'], p['born']['year']))
    players2 = sorted(players2, key = lambda i: i[2])

    for i in range (0,5):
        resultingplayer = players2[i]
        peakovr = 0
        r = resultingplayer[3]


        peakszn = r[0]['season']
        peakpos = r[0]['pos']
        for r in resultingplayer[3]:
            if r['season']-resultingplayer[4]>= page:
                if r['ovr'] > peakovr:
                    peakovr = r['ovr']
                    peakszn = r['season']
                    peakpos = r['pos']
        score = resultingplayer[2]
        resultingplayer =pull_info.pinfo(resultingplayer[0], season = peakszn)
        if resultingplayer['tid'] >= 0:
             t = pull_info.tinfo(teams[resultingplayer['tid']], peakszn)
        else:
             t = pull_info.tgeneric(resultingplayer['tid'])
        s= str(resultingplayer["stats"]['pts'])+"pts, "+str(resultingplayer["stats"]['reb'])+"reb, "+str(resultingplayer["stats"]['ast'])+"ast, "+str(resultingplayer["stats"]['stl'])+"stl, "+str(resultingplayer["stats"]['blk'])+"blk, "+str(resultingplayer["stats"]['per'])+" PER"
        if 'abbrev' in t:
            text = str(peakszn)+" "+peakpos+" "+ resultingplayer["name"]+", "+str(peakszn-resultingplayer["born"])+" years old, "+str(resultingplayer["ovr"])+"/"+str(resultingplayer["pot"])+" ("+t["abbrev"]+")\n"+s
            
        else:
            text = str(peakszn)+" "+peakpos+" "+ resultingplayer["name"]+", "+str(peakszn-resultingplayer["born"])+" years old, "+str(resultingplayer["ovr"])+"/"+str(resultingplayer["pot"])+" ("+t["name"]+")\n"+s
        text = text + "\n Similarity score: "+str(round(10000/score,2))
        embed.add_field(name='Player Comparison', value=text, inline=False)
    return embed
def progressionchart(embed, player, commandInfo):
    cum = False

    export = shared_info.serverExports[str(commandInfo['id'])]
    #print(commandInfo)
    players = export['players']
    if not " " in commandInfo['message'].content:
        embed.add_field(name = "Error",value = "specify points, rebounds, or assists, then follow with comma separated player names")
        return embed
    if 'cschart' in commandInfo['message'].content:
        cum = True
    message = commandInfo['message'].content.split(" ",1)[1]
    typeto = "Age"
    message = message.replace(" age","")
    if "season" in message.split(" "):
        typeto = "Season"
        message = message.replace("season","")
    if "year" in message.split(" "):
        typeto = "Year in League"
        message = message.replace("year","")
    tochart = "pts"
    message = message.replace("points","")
    if "rebounds" in message.split(" ") or"rebound" in message.split(" ") or"reb" in message.split(" "):
        tochart = "rebounds"
        message = message.replace("rebounds","").replace("rebound","").replace("reb","")
        # offensive and defensive rebounds are tracked separately, this case will be separately handled
    if "assists" in message.split(" ") or "assist" in message.split(" "):
        tochart = "ast"
        message = message.replace("assists","").replace("assist","")
    if "blocks" in message.split(" ") or "block" in message.split(" "):
        tochart = "blk"
        message = message.replace("blocks","").replace("block","")
    if "steals" in message.split(" ") or "steal" in message.split(" "):
        tochart = "stl"
        message = message.replace("steals","").replace("stl","")
    if "threes" in message.split(" "):
        tochart = "tp"
        message = message.replace("threes","")
    if "turnovers" in message.split(" ") or "turnover" in message.split(" "):
        tochart = "tov"
        message = message.replace("turnovers","").replace("turnover","")
    for c in ['pts','tov','tp','blk','stl','ast','gp']:
        if c in message.split(" "):
            tochart = c
            message = message.replace(c,"")
    pergame = False
    if "per game" in message:
        pergame = True
    if "ppg" in message:
        tochart = "pts"
        message = message.replace("ppg","")
        pergame = True
    if "rpg" in message:
        tochart = "rebounds"
        message = message.replace("rpg","")
        pergame = True
    if "apg" in message:
        tochart = "ast"
        message = message.replace("apg","")
        pergame = True
    if "bpg" in message:
        tochart = "blk"
        message = message.replace("bpg","")
        pergame = True
    if "spg" in message:
        tochart = "stl"
        message = message.replace("spg","")
        pergame = True
    if pergame:
        if cum:
            embed.add_field(name = "Error",value = "per game stats not meaningful cumulatively")
            return embed
    playerstosearch = []
    print(message)
    for s in message.split(","):
        playerstosearch.append(basics.find_match(s, export,settings =  shared_info.serversList[str(commandInfo['id'])]))
    names = []
    statslist = []
    gameslist = []
    valmin = 100000
    moqp= []
    valmax = 0
    for p in players:
        firstseason = 0
        if p['pid'] in playerstosearch:

            names.append(p['firstName']+" "+p['lastName'])
            stats = dict()
            mo = 0
            games = dict()
            
                                            
            for s in p['stats']:
                if firstseason == 0:
                    firstseason = s['season']
                if not s['playoffs']:
                    if typeto == "Age":
                        quantity = s['season']-p['born']['year']
                    elif typeto == "Season":
                        quantity = s['season']
                    else:
                        #year in league
                        quantity = s['season'] - firstseason +1

                    if tochart == "rebounds":
                        value = s['orb'] + s['drb']
                    
                    else:
                        value = s[tochart]
                
                    if quantity in stats:
                        stats.update({quantity:stats[quantity]+value})
                        games.update({quantity:games[quantity]+s['gp']})
                    else:
                        stats.update({quantity:value})
                        games.update({quantity:s['gp']})
                    if quantity  < valmin:
                        valmin = quantity
                    if quantity > valmax:
                        valmax = quantity
            if typeto == "Season":
                mo = export['gameAttributes']['season']
            elif typeto == "Year in League":
                mo = export['gameAttributes']['season'] - firstseason 
            elif typeto == "Age":
                mo = export['gameAttributes']['season'] - p['born']['year']
            if pergame:
                for d in stats:
                    if games[d] > 0:
                        stats.update({d:stats[d]/games[d]})
            statslist.append(stats)

            moqp.append(mo)
    dicttoconvert = dict()
    valminadj = valmin
    if cum:
        valminadj = valmin-1
    dicttoconvert.update({typeto:range(valminadj, valmax+1)})
    nameindex = 0
    
    for stat in statslist:
        lastrememberedvalue = 0
        track = []
        
        for q in range(valminadj, valmax+1):
            if cum:
                if q in stat:
                    track.append(stat[q]+lastrememberedvalue)
                    lastrememberedvalue = stat[q]+lastrememberedvalue
                else:
                    if q > moqp[nameindex]:
                         track.append(float('nan'))
                    else:
                        track.append(lastrememberedvalue)
            else:
                if q in stat:
                    track.append(stat[q])
                else:
                    if q > moqp[nameindex]:
                        track.append(float('nan'))
                    else:
                        track.append(0)
        dicttoconvert.update({names[nameindex]:track})
        nameindex += 1
    df = pandas.DataFrame(dicttoconvert)
    df.set_index(typeto, inplace=True, drop=True)
    statnames = {"pts":"Points","rebounds":"Rebounds","ast":"Assists",'blk':"Blocks",'stl':'Steals','tov':'Turnovers','tp':'Three pointers','gp':'Games Played'}
    pgv = ""
    if pergame:
        pgv = " per game"
    fig = px.line(df,labels = {"index":typeto,"value":"Amount"}, title = "Career progression of "+statnames[tochart]+pgv, markers = True)


    fig.write_image('first_figure.png')
    del fig
    return embed





def progschart(embed, player, commandInfo):
    
    finalthree = commandInfo['message'].content[-3:]
    #print(finalthree)
    key = "ovr"
    pname = player["name"]
    for item in ["pot", "hgt","dnk","oiq","tre","ins","diq","spd"," ft","drb","jmp","pss"," fg","ndu"," tp","reb"]:
        if finalthree == item:
            key = item
            if key == " ft":
                key = "ft"
            if key == "tre":
                key = "stre"
            if key == " fg":
                key = "fg"
            if key == "ndu":
                key = "endu"
            if key == " tp":
                key = "tp"
    export = shared_info.serverExports[str(commandInfo['id'])]
    #print(commandInfo)
    players = export['players']
    teams = export['teams']
    for play in players:
        if player["pid"] == play["pid"]:
            player = play
    #player = players[player['pid']]
    newthing = player['ratings']
            
    birthyear = player.get("born").get("year")
    seasons = []
    ages = []
    rtg = []
    season = -1000
                
    names = [key]
    for item in newthing:
         if int(item.get("season"))>=season:
            print(item)
            seasons.append(int(item.get("season")))
            ages.append(-birthyear+int(item.get("season")))
            rtg.append(int(item.get(key)))
    df = pandas.DataFrame(rtg, index=ages,columns = names)
    fig = px.line(df,labels = {"index":"Age","value":"Rating"}, title = "Progs for "+pname+" "+key)
    fig.update_layout(

    yaxis=dict( # Here
        range=[0,100] # Here
    ) # Here
    )
    fig.write_image('first_figure.png')
    del fig
    return embed
def series(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    try: games = export['games']

    except KeyError: 
        embed.add_field(name='Error', value='No box scores in this export.')
        return embed
    f = open('dumb.json','w')
    f.write(json.dumps(games))
    f.close()
    lines = []
    totallength = 0

    maxday = 0
    for g in games:
        if g['season'] == commandInfo['season']:
            if g['day'] > maxday:
                maxday = g['day']
    b = export['gameAttributes']['numGamesPlayoffSeries']
    if not isinstance(b[0],int):
        for element in b:
            k = element['start']
            v = element['value']
            if k is None:
                k = -9999
            if int(k) <= commandInfo['season']:
                tempb = v
        b = tempb

    testday = maxday - sum(b)
    byes = export['gameAttributes']['numPlayoffByes']

    if not isinstance(byes,int):
        for element in byes:
            k = element['start']
            v = element['value']

            if k is None:
                k = -9999
            if int(k) <= commandInfo['season']:
                tempbyes = v
        byes = tempbyes
    print(byes)

    limit = 2**(len(b)-1) - byes

    numgamesdict = dict()
    for g in games:
        if g['season'] == commandInfo['season']:
            if g['day'] >= testday:
                if g['day'] not in numgamesdict:
                    numgamesdict.update({g['day']:0})
                numgamesdict.update({g['day']:numgamesdict[g['day']]+1})
    minday = 1000000
    for k, v in numgamesdict.items():
        if v == limit:
            if k < minday:
                minday = k
    curteam = None
    for p in players:
        if p['pid'] == player['pid']:
            if len(p['stats']) < 1:
                embed.add_field(name = 'this guy has no games played', value = 'yeh')
                return embed
            for s in p['stats']:
                if s['playoffs']:
                    if s['season'] == commandInfo['season']:
                        curteam = s['tid']
    #print(curteam)
    if curteam is None:
        embed.add_field(name = 'looks like this guy did not have a playoff run that year', value = 'ok')
        return embed
    for t in teams:
        if t['tid'] == curteam:
            curteam = t['name']
    print(curteam)

    seriescounts = dict()
    seriestotals = dict()
    orderedopps = []
    for g in games:
        if g['day'] >= minday:
            if g['won']['tid'] > -1 and g['season'] ==commandInfo['season']:
                gameInfo = pull_info.game_info(g, export, commandInfo['message'])
                for gt in g['teams']:
                    for pl in gt['players']:
                        if pl['pid'] == player['pid']:
                            if pl['min'] > 0:
                                #statLine = f"{round(pl['min'], 1)} min, {pl['pts']} pts, {pl['orb']+pl['drb']} reb, {pl['ast']} ast, {pl['blk']} blk, {pl['stl']} stl, {pl['fg']}/{pl['fga']} FG, {pl['tp']}/{pl['tpa']} 3P"
                                key = gameInfo['home']
                                key2 = gameInfo['away']
     
                                opp = key
                                if opp == curteam:
                                    opp = key2
                                if not opp in orderedopps:
                                    orderedopps.append(opp)
                                if not opp in seriescounts:
                                    seriestotals.update({opp:pl.copy()})
                                    seriescounts.update({opp:1})

                                else:
                                    a = seriestotals[opp]
                                    for k, v in pl.items():
                                        if isinstance(v, int) or isinstance(v, float):
                                            a.update({k:a[k] + v})
                                    seriestotals.update({opp:a})
                                    seriescounts.update({opp:seriescounts[opp]+1})
    lines = ""
    for opp in orderedopps:
        pl = seriestotals[opp]
        for term in ['fta','tpa','fga']:
            if pl[term] == 0:
                pl[term] = float('nan')
        count = seriescounts[opp]
        for t in teams:
            if t['name'] == opp:
                oppabrev = t['abbrev']
        statLine = f"{round(pl['min']/count, 1)} min, **{round(pl['pts']/count,1)}** ppg, ** {round((pl['orb']+pl['drb'])/count,1)}**  rpg, ** {round((pl['ast'])/count,1)}**  apg, {round((pl['stl'])/count,1)} stl, {round((pl['blk'])/count,1)} blk, {round((pl['tov'])/count,1)} tov,\n{round(pl['fg']/pl['fga']*100,1)} FG%, {round(pl['tp']/pl['tpa']*100,1)} 3P%, {round(pl['ft']/pl['fta']*100,1)} FT%"
        

        lines = lines + "\n**"+oppabrev+"** "+str(count)+" GP, "+statLine
    if lines == "":
        embed.add_field(name= "No playoff series are found for that year", value = "I have nothing for you")
        return embed
    embed.add_field(name= "Playoff series stats", value = lines)
    return embed
                                
                        
def pgamelog(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    teams = export['teams']
    print(export['gameAttributes'])
    try: games = export['games']

    except KeyError: 
        embed.add_field(name='Error', value='No box scores in this export.')
        return embed
    f = open('dumb.json','w')
    f.write(json.dumps(games))
    f.close()
    lines = []
    totallength = 0

    for g in games:

        if g['won']['tid'] > -1 and g['season'] == export['gameAttributes']['season']:
            for gt in g['teams']:
                for pl in gt['players']:
                    if pl['pid'] == player['pid']:
                        if pl['min'] > 0:
                            statLine = f"{round(pl['min'], 1)} min, {pl['pts']} pts, {pl['orb']+pl['drb']} reb, {pl['ast']} ast, {pl['blk']} blk, {pl['stl']} stl, {pl['fg']}/{pl['fga']} FG, {pl['tp']}/{pl['tpa']} 3P"
                        else:
                            statLine = 'Did not play'
                        gameInfo = pull_info.game_info(g, export, commandInfo['message'])
                        #print(gameInfo)
                        newLine = f"{gameInfo['abbrevScore']} - ``{statLine}``"
                        lines.append(newLine)
                        
    numDivs, rem = divmod(len(lines), 10)
    numDivs += 1
    pagenum = 1
    pages = []
    for item in commandInfo['message'].content.split(" "):
        try:

            pagenum = int(item)
        except ValueError:
            pass
        
    for i in range(numDivs):
        newLines = lines[(i*10):((i*10)+10)]
        text = '\n'.join(newLines)
        pages.append(text+"\n Page " +str(i+1)+" out of "+str(numDivs))
    if pagenum > len(pages):
        pagenum = 1

    embed.add_field(name='Player Game Log '+str( export['gameAttributes']['season']), value=pages[pagenum-1], inline=False)
    return embed
def calccompsingle(r, extra):
    rect = dict()
    rect.update({'3':(r['tp']+r['oiq']*0.1)/1.1})
    rect.update({'3-syn':1/(1+math.exp(-15*(0.01*rect['3']-0.59)))})
    rect.update({'A':(r['stre']+r['jmp']+r['spd']+0.75*r['hgt'])/3.75})
    rect.update({'A-syn':1/(1+math.exp(-15*(0.01*rect['A']-0.63)))})
    rect.update({'B':(r['drb']+r['spd'])/2})
    rect.update({'B-syn':1/(1+math.exp(-15*(0.01*rect['B']-0.68)))})
    rect.update({'Po':(r['hgt']+0.6*r['stre']+0.2*r['spd']+r['ins']+0.4*r['oiq'])/3.2})
    rect.update({'Po-syn':1/(1+math.exp(-15*(0.01*rect['Po']-0.61)))})
    rect.update({'Ps':(0.4*r['drb']+r['pss']+0.5*r['oiq'])/1.9})
    rect.update({'Ps-syn':1/(1+math.exp(-15*(0.01*rect['Ps']-0.63)))})
    rect.update({'Di':(2.5*r['hgt']+r['stre']+0.5*r['spd']+0.5*r['jmp']+2*r['diq'])/6.5})
    rect.update({'Di-syn':1/(1+math.exp(-15*(0.01*rect['Di']-0.57)))})
    rect.update({'Dp':(0.5*r['hgt']+r['stre']*0.5+2*r['spd']+0.5*r['jmp']+r['diq'])/4.5})
    rect.update({'Dp-syn':1/(1+math.exp(-15*(0.01*rect['Dp']-0.61)))})
    rect.update({'R':(2*r['hgt']+0.1*r['stre']+2*r['reb']+0.1*r['jmp']+0.5*r['diq']+0.5*r['oiq'])/5.2})
    rect.update({'R-syn':1/(1+math.exp(-15*(0.01*rect['R']-0.61)))})
    if (extra):
        rect.update({'Bl':(2.5*r['hgt']+1.5*r['jmp']+0.5*r['diq'])/4.5})
        rect.update({'D':(r['hgt']+0.5*r['jmp']+r['stre']+r['spd']+2*r['diq'])/5.5})
        rect.update({'Usage':(r['ins']*1.5+r['dnk']+r['fg']+r['tp']+r['spd']*0.5+r['hgt']*0.5+r['drb']*0.5+r['oiq']*0.5)/6.5})
        rect.update({'Tov':(25+r['ins']+r['pss']-r['oiq'])/1.5})
        rect.update({'Rim':(r['hgt']*2+0.3*r['stre']+0.3*r['dnk']+0.2*r['oiq'])/2.8})
        rect.update({'Mid Range':(r['fg']-r['oiq']*0.5+0.2*r['stre'])/0.7})
        rect.update({'Stl':(50+r['spd']+2*r['diq'])/4})
        rect.update({'Foul':(150+r['hgt']-r['diq']-r['spd'])/2})
        rect.update({'Draw Foul':(r['hgt']+r['spd']+r['drb']+r['dnk']+r['oiq'])/5})
        rect.update({'FT':r['ft']})
        rect.update({'Endurance':r['endu']*0.5+25})   
    return rect
def calccomp(player,s, extra = False):

    for r in player['ratings']:

        if r['season'] == s:
            
            return calccompsingle(r, extra)
    for r in player['ratings']:
        if r['season'] > s:
            return calccompsingle(r, extra)
    return None
        
                                    
def composites(embed, player, commandInfo):
    
    compdict = calccomp(commandInfo['fullplayer'], commandInfo['season'], extra = True)
    if compdict is None:
        return embed
    s= ""
    parity = 0
    terms = {'3':'Three pointers','A':'Athleticism  ','B':'Ball Handling','Po':'Post Scoring',
             'Ps':'Passing','Di':'Interior Def.','Dp':'Rerimeter Def.','R':'Rebounding'}
    secondlist = {'D':'General Defense','Stl':'Steals','Bl':'Blocks','FT':'Free throws','Rim':'At-Rim Scoring','Tov':'Turnovers'}
    ke = list(terms.keys())
    for t in ke:
        terms.update({t+"-syn":t+" Synergy"})
    defense = ""
    for term in ['Di','Dp','R','D','Bl','Stl','Foul']:
        name = term
        if term in terms:
            name = terms[term]
        if name in secondlist:
            name = secondlist[name]
        defense += "**"+name + "**: "+str(round(compdict[term],1))
        if term+'-syn' in terms:
            name = terms[term+'-syn']
            defense += " ("+str(round(compdict[term+'-syn'],3))+' '+term + ")" 
        defense = defense + '\n'
    
    offense = ""
    for term in ['Po','B','Ps','3','A','Usage','Rim','FT','Mid Range','Draw Foul','Tov']:
        name = term
        if term in terms:
            name = terms[term]
        if name in secondlist:
            name = secondlist[name]
        offense += "**"+name + "**: "+str(round(compdict[term],1))
        if term+'-syn' in terms:
            name = terms[term+'-syn']
            offense += " ("+str(round(compdict[term+'-syn'],3))+' '+term + ")" 
        offense = offense + '\n'
    embed.add_field(name = "Offense", value = offense, inline = True)
    embed.add_field(name = "Defense", value = defense, inline= True)
    embed.add_field(name = "Other", value = '**Endurance**: '+str(round(compdict['Endurance'],1)), inline = False)
    s = ''
    count = 0
    for term in ['3-syn','A-syn','Po-syn','R-syn','Di-syn','Dp-syn','B-syn','Ps-syn']:
        if 'syn' in term:
            s += '**'+terms[term]+"**: "+str(round(compdict[term],3))
            count += 1
            if count % 2 == 0:
                s += '\n'
            else:
                s += '  |  '
    embed.add_field(name = 'Synergy summary', value = s, inline = True)
    return embed
def sumfor(dl,s):
    su = 0
    for k in dl:
        su = su + k[s+'-syn']

    return su
def sumfor2(dl,s):
    su = 0
    for k in dl:
        su = su + k[s]

    return su
def lineupsynergycalc(players, season):
    if len(players) != 5:
        return None
    d = dict()
    synergies = []
    for p in players:
        synergies.append(calccomp(p,season, extra = True))

    for i in synergies:
        if i is None:
            return None
    s = sumfor(synergies, '3')
    d.update({'3':5/(1+math.exp(-3*(s-2)))})
    s = sumfor(synergies, 'A')
    
    d.update({'A':1/(1+math.exp(-15*(s-1.75)))+1/(1+math.exp(-5*(s-2.75)))})
    s = sumfor(synergies, 'B')
    d.update({'B':3/(1+math.exp(-15*(s-0.75)))+1/(1+math.exp(-5*(s-1.75)))})
    s = sumfor(synergies, 'Po')
    d.update({'Po':1/(1+math.exp(-15*(s-0.75)))})
    s = sumfor(synergies, 'Ps')
    d.update({'Ps':3/(1+math.exp(-15*(s-0.75)))+1/(1+math.exp(-5*(s-1.75)))+1/(1+math.exp(-5*(s-2.75)))})
    s = sumfor(synergies, 'A')
    d.update({'dA':1/(1+math.exp(-5*(s-2)))+1/(1+math.exp(-5*(s-3.25)))})
    s = sumfor(synergies, 'Dp')
    d.update({'Dp':1/(1+math.exp(-15*(s-0.75)))})
    s = sumfor(synergies, 'Di')
    d.update({'Di':2/(1+math.exp(-15*(s-0.75)))})
    s = sumfor(synergies, 'R')
    d.update({'R':1/(1+math.exp(-15*(s-0.75)))+1/(1+math.exp(-5*(s-1.75)))})
    d.update({'P':(math.sqrt(1+sumfor(synergies, '3')+sumfor(synergies, 'B')+sumfor(synergies,'Ps'))-1)/2})
    if d['P'] < 0:
        d.update({'P':0})
    d.update({'O':(d['Ps']+d['Po']+d['A']+d['B']+d['3'])/17*(0.5+0.5*d['P'])})
    d.update({'D':1/6*(d['dA']+d['Di']+d['Dp'])})
    d.update({'Rs':d['R']/4})
    synfac = 0.25
    d.update({'drbcomposite':sumfor2(synergies,'B')/100 + synfac*d['O']})
    d.update({'psscomposite':sumfor2(synergies,'Ps')/100 + synfac*d['O']})
    d.update({'rebcomposite':sumfor2(synergies,'R')/100 + synfac*d['Rs']})
    d.update({'defcomposite':sumfor2(synergies,'D')/100 + synfac*d['D']})
    d.update({'dicomposite':sumfor2(synergies,'Di')/100 + synfac*d['D']})
    d.update({'dpcomposite':sumfor2(synergies,'Dp')/100 + synfac*d['D']})
    return d
def lineupcompletion(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    listps = []
    m = commandInfo['message'].content

    season = commandInfo['season']
    if season < 100:
        season = None
    typetoadd = 'total'
    if 'offensive' in m.lower():
        m = m.lower().replace('offensive','')
        typetoadd = 'O'
    if 'defensive' in m.lower():
        m = m.lower().replace('defensive','')
        typetoadd = 'D'
    if 'rebounding' in m.lower():
        m = m.lower().replace('rebounding','')
        typetoadd = 'R'
    maxovr = 100
    for t in m.split(" "):
        try:
            b = int(t)
            if (b > 25 and b < 100):
                maxovr = b
                m = m.replace(str(maxovr),"")
            else:
                season = b
                m = m.replace(str(b),"")
        except ValueError:
            pass
    if season is None:
        season = export['gameAttributes']['season']
    listps = []
    # Use the cleaned message for player name parsing
    cleaned = ' '.join(m.split()[1:]) if len(m.split()) > 1 else ''
    for part in cleaned.split(","):
        part = part.strip()
        if part:
            p = basics.find_match(part, export,settings =  shared_info.serversList[str(commandInfo['id'])])
            listps.append(p)
    if len(listps) != 4:
        embed.add_field(name = "Maybe you should Synergy your brain cells",value = "include 4 comma separated players for this. *or else...*")
        return embed
    listplayers = []
    for p in export['players']:
        if p['pid'] in listps:
            listplayers.append(p)
    candidates = []
    p = listplayers
    t = p[0]['firstName']+" "+p[0]['lastName']+", "+p[1]['firstName']+" "+p[1]['lastName']+", "+p[2]['firstName']+" "+p[2]['lastName']+", "+p[3]['firstName']+" "+p[3]['lastName']+" - Lineup Complements"
    if maxovr != 100:
        t = t + " under "+str(maxovr)+" ovr"
    embed = discord.Embed(title = t, description = "")
    print(maxovr)
    # Build team name lookup
    team_abbrevs = {}
    for tm in export['teams']:
        team_abbrevs[tm['tid']] = tm['abbrev']

    for lastp in export['players']:
        if not lastp['pid'] in listps:
            if lastp['tid'] != -1:
                r = lastp['ratings']
                for v in r:
                    if v['season'] == season and v['ovr'] < maxovr:
                        # we've found a valid last player to potentially insert into this lineup
                        dictionary = lineupsynergycalc(listplayers + [lastp], season)
                        if dictionary is None:
                            embed.add_field(name = "something went wrong", value = "perhaps someone in your lineup is already retired")
                            return embed

                        if len(candidates) > 0 and candidates[-1][0] == lastp['pid']:
                            candidates = candidates[:-1]
                        team_abbrev = team_abbrevs.get(lastp['tid'], '??')
                        candidates.append((lastp['firstName']+" "+lastp['lastName'],dictionary['O'],dictionary['D'],dictionary['Rs'],v['ovr'],v['pot'],v['pos'],team_abbrev))
    if typetoadd == 'O':
        candidates = sorted(candidates, key = lambda x: x[1], reverse = True)
    if typetoadd == 'D':
        candidates = sorted(candidates, key = lambda x: x[2], reverse = True)
    if typetoadd == 'R':
        candidates = sorted(candidates, key = lambda x: x[3], reverse = True)
    if typetoadd == 'total':
        candidates = sorted(candidates, key = lambda x: x[1]+x[2]+x[3], reverse = True)
    top30 = candidates[:30]
    s = ''
    index = 0
    for c in top30[0:10]:
        index += 1
        s += str(index)+'. '+ c[6]+" **"+c[0]+"** "+str(c[4])+"/"+str(c[5])+" ("+c[7]+"): "+str(round(c[1],3))+" O, "+str(round(c[2],3))+" D, "+str(round(c[3],3))+" R, "+str(round(c[1]+c[2]+c[3],3))+" total\n"
    embed.add_field(name = "Best Synergy Complements to your Lineup", value = s, inline = False)
    s = ''
    for c in top30[10:20]:
        index += 1
        s += str(index)+'. '+ c[6]+" **"+c[0]+"** "+str(c[4])+"/"+str(c[5])+" ("+c[7]+"): "+str(round(c[1],3))+" O, "+str(round(c[2],3))+" D, "+str(round(c[3],3))+" R, "+str(round(c[1]+c[2]+c[3],3))+" total\n"
    embed.add_field(name = "Best Synergy Complements to your Lineup", value = s, inline = False)
    s = ''
    for c in top30[20:30]:
        index += 1
        s += str(index)+'. '+ c[6]+" **"+c[0]+"** "+str(c[4])+"/"+str(c[5])+" ("+c[7]+"): "+str(round(c[1],3))+" O, "+str(round(c[2],3))+" D, "+str(round(c[3],3))+" R, "+str(round(c[1]+c[2]+c[3],3))+" total\n"
    embed.add_field(name = "Best Synergy Complements to your Lineup", value = s, inline = False)
    return embed
def realsynergy(embed,commandInfo,listplayers, replace, addnote = True):
   
    d = lineupsynergycalc(listplayers, commandInfo['season'])
    if d is None:
        embed.add_field(name = "Error", value = "maybe someone already retired")
        return embed
    p = listplayers
    if replace:
        embed = discord.Embed(title = p[0]['firstName']+" "+p[0]['lastName']+", "+
                              p[1]['firstName']+" "+p[1]['lastName']+", "+
                              p[2]['firstName']+" "+p[2]['lastName']+", "+
                              p[3]['firstName']+" "+p[3]['lastName']+", "+
                              p[4]['firstName']+" "+p[4]['lastName']+" - Lineup Synergy", description = "")
    else:
        embed.add_field(name = "Synergy of starting lineup", value = "", inline = False)

    s = 'Three pointers: '+str(round(d['3'],3))+"/5\n"
    s = s + 'Athleticism: '+str(round(d['A'],3))+"/2\n"
    s = s + 'Ball Handling: '+str(round(d['B'],3))+"/4\n"
    s = s + 'Post Scoring: '+str(round(d['Po'],3))+"/1\n"
    s = s + 'Passing: '+str(round(d['Ps'],3))+"/5\n"
    s = s + 'Perimeter: ' + str(round(d['P'],3))+"/2\n"
    s = s + '**Total: '+str(round(d['O'],3))+"/1.25**"
    if addnote:
       
        s = s + "\n\n Note: Perimeter synergy is a compound synergy calculated from Ps, B, and 3 synergies, and is factored into total offensive synergy. "
    embed = embed.add_field(name = 'Offensive', value = s, inline = True)
    s = 'D. Athleticism: ' + str(round(d['dA'],3))+"/2\n"
    s = s + 'Interior defense: ' + str(round(d['Di'],3))+"/2\n"
    s = s + 'Perimeter defense: ' + str(round(d['Dp'],3))+"/1\n"
    s = s + '**Total: '+str(round(d['D'],3))+"/0.833**\n"
    embed = embed.add_field(name = 'Defensive', value = s, inline = True)
    s = 'Rebounding (raw): ' + str(round(d['R'],3))+"/2\n"
    s =s +  '**Rebounding: '+str(round(d['Rs'],3))+"/0.5**\n"
    embed = embed.add_field(name = 'Rebounding', value = s)

    if (replace):
        s = 'Rebounding: '+str(round(d['rebcomposite'],3))+"\n"
        s = s + 'Passing: '+str(round(d['psscomposite'],3))+"\n"
        s = s + 'Dribbling: '+str(round(d['drbcomposite'],3))+"\n"
        s = s + 'Defense: '+str(round(d['defcomposite'],3))+"\n"
        s = s + 'Int Defense: '+str(round(d['dicomposite'],3))+"\n"
        s = s + 'Per Defense: '+str(round(d['dpcomposite'],3))+"\n"
        embed.add_field(name = 'Team Composites', value = s + "\n Note: these assume playoff environment, no fatigue, and tied score. Yes, all 3 would change team composite ratings.", inline = False)
        

    

                                           
    return embed
def synergy(embed, player, commandInfo):
    export = shared_info.serverExports[str(commandInfo['id'])]
    raw = ' '.join(commandInfo['message'].content.split(' ')[1:]).strip()

    if not raw:
        # Default: top 5 players from user's lineup by rosterOrder
        userTid = shared_info.serversList[str(commandInfo['id'])]['teamlist'].get(str(commandInfo['message'].author.id), -1)
        if userTid == -1:
            embed.add_field(name='Error', value="You're not assigned to a team. Provide 5 comma-separated players instead.")
            return embed
        roster = [p for p in export['players'] if p['tid'] == userTid]
        # If rosterOrder isn't set, fall back to sorting by OVR
        if all(p.get('rosterOrder', 9999) == 9999 for p in roster):
            roster.sort(key=lambda p: p['ratings'][-1]['ovr'] if p.get('ratings') else 0, reverse=True)
        else:
            roster.sort(key=lambda p: p.get('rosterOrder', 9999))
        listplayers = roster[:5]
        if len(listplayers) < 5:
            embed.add_field(name='Error', value="Your roster has fewer than 5 players.")
            return embed
        return realsynergy(embed, commandInfo, listplayers, True)

    listps = []
    for m in raw.split(","):
        p = basics.find_match(m, export, settings=shared_info.serversList[str(commandInfo['id'])])
        listps.append(p)
    if len(listps) != 5:
        embed.add_field(name='Error', value="Please include exactly 5 comma-separated players, or use `-synergy` with no arguments to use your lineup's top 5.")
        return embed
    listplayers = []
    for p in export['players']:
        if p['pid'] in listps:
            listplayers.append(p)
    return realsynergy(embed, commandInfo, listplayers, True)
        
        
def progspredict(embed, player, commandInfo):
    timespent = 100
    for item in commandInfo['message'].content.split(" "):
        if item == "next":
            timespent = 1
    rating = 'ovr'
    for item in commandInfo['message'].content.split(" "):
        if item.lower() in ['endu','stre','jmp','spd','tp','fg','ft','dnk','ins','pss','reb','drb','oiq','diq']:
            rating = item.lower()
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    play = 0
    for p in players:
        if p['pid'] == player['pid']:
            play = p
    ratings = play['ratings']
    keyrating = None
    if play['draft']['year'] > export['gameAttributes']['season']:
        if export['gameAttributes']['season'] == commandInfo['season']:
            commandInfo.update({'season':play['draft']['year']})
    for item in ratings:
        if commandInfo['season'] == item['season']:
            keyrating = item
    if keyrating == None:
        embed.add_field(name = "Error: Out of Range", value = "nothing I can do.")
        return embed
    curage = commandInfo['season'] - play['born']['year']
    curovr = keyrating[rating]
    global thing

    if thing is None:
        f = open("progs.txt")
        print("reading")
        for line in f:
            thing = json.loads(line)
            
            break
    t = thing[rating]
    peaks = []
    print("ok")
    threshold = 1.5
    if timespent == 1:
        threshold = 0.5
    for line in t.split("|"):
        peak = 99999
        start = 999999
        for item in line.replace("\n","").split(","):

            age, ovr = item.split(":")
            diff = int(age)-start
            if diff > timespent:
                break
            if int(age) == curage and abs(int(ovr) - curovr) <  threshold:
                peak = 0
                start = int(age)

            elif int(ovr) > peak:
                peak = int(ovr)
            
        if peak > 0 and peak < 1000:
            peaks.append(peak)

    if len(peaks) < 1:
        embed.add_field(name = "Error: Nobody found with same age and overall in database", value = "Your player is just one of a kind.")
        return embed
    values = []
    quantities = []
    cols = ["#F63309","#0921F1"]
    if min(peaks) != curovr:
        cols =  ["#0921F1","#F63309"]
    for elm in range(min(peaks),max(peaks)+1):
        values.append(elm)
        quantities.append([elm,peaks.count(elm),str(elm == curovr)])



    df = pandas.DataFrame(quantities,index=values)
    df.columns = ['Value','frequency','Current']
    bid = "Career peak "+rating+" for players similar to "+player['name']+" "+str(commandInfo['season'])
    if timespent == 1:
        bid = "Next prog result for players similar to "+player['name']+" "+str(commandInfo['season'])

    fig = px.bar(df,x ='Value', y='frequency', color = 'Current',color_discrete_sequence = cols,title =bid)
    peaks = sorted(peaks)
    median = peaks[int(len(peaks)/2)]
    mean = round(sum(peaks)/len(peaks),2)
    fq = peaks[int(len(peaks)/4)]
    tq = peaks[int(len(peaks)/4*3)]

    text = ""
    text1=str(max(peaks))
    text2=str(tq)+"\n"
    text3=str(median)+"\n"
    text4=str(mean)+"\n"
    text5=str(fq)+"\n"
    text6=str(min(peaks))
    embed.add_field(name="Mean",value=text4,inline=True)
    if len(peaks) < 50:
        embed.add_field(name="Maximum",value=text1,inline=True)
        embed.add_field(name="Minimum",value=text6,inline=True)
        embed.add_field(name="Median",value=text3,inline=True)
        embed.add_field(name="25th percentile",value=text5,inline=True)
        embed.add_field(name="75th percentile",value=text2,inline=True)
    else:
        embed.add_field(name="10th percentile",value=peaks[int(len(peaks)/10)],inline=True)
        embed.add_field(name="25th percentile",value=text5,inline=True)
        embed.add_field(name="Median",value=text3,inline=True)
        embed.add_field(name="75th percentile",value=text2,inline=True)
        embed.add_field(name="90th percentile",value=peaks[int(9*len(peaks)/10)],inline=True)
    
    embed.add_field(name="Sample Size",value=str(len(peaks)),inline=True)
    fig.write_image('first_figure.png')
    del fig
    print("wrote")
    embed.add_field(name= "Tip", value = "Now you can call progspredict on individual ratings! For example '-progspredict Victor Wembanyama reb' plots outcomes for Victor Wembanyama's peak rebounding rating!", inline= False)
    if (rating != 'ovr'):
        embed.title = embed.title + " - "+rating.upper()
    return embed
        
            

    
    
def trivia(embed, player, commandInfo):
    embed = discord.Embed(title="Trivia", description="Guess who")
    d = "Guess who"
    if commandInfo['message'].channel in trivias:
        d = "By the way, the last trivia's solution was **" + trivias[commandInfo['message'].channel]['name'] + "**"
    embedresult = discord.Embed(title="Trivia", description=d)
    export = shared_info.serverExports[str(commandInfo['id'])]
    players = export['players']
    newcommandinfo = {'id':commandInfo['id'], 'message':commandInfo['message']}
    found = False
    track = 1
    while not found:
        track += 1
        player_key = random.sample(players, 1)[0]
        player = pull_info.pinfo(player_key)
        if player['peakOvr'] > 59 or track == 10000:
            found = True
    t = "Player Progressions"
    if random.random() < 0.5:
        embed2 = progs(embed, player, newcommandinfo)
    else:
        t = "Player Stats"
        embed2 = hstats(embed, player, newcommandinfo)
    newstring = ""
    for field in embed.fields:
        newstring = field.value.replace(player['name'], 'X')
        if "(" in newstring:
            while "(" in newstring:
                newstring = newstring[0:newstring.index("(")]+newstring[newstring.index(")")+1:]
        embedresult.add_field(name = t, value = newstring)
    print(player['pid'])
    prefix = shared_info.serversList[str(commandInfo['id'])].get('prefix', '-')
    embedresult.add_field(name="How to Play", value=f"Use **{prefix}answer [player name]** to guess\nUse **{prefix}hint** for a clue", inline=False)
    trivias.update({commandInfo['message'].channel: {
        'name': player['name'],
        'player_data': player,
        'hint_count': 0
    }})

    return embedresult

def grade(val):
    if val >= 80: return "elite"
    if val >= 70: return "excellent"
    if val >= 60: return "above average"
    if val >= 50: return "average"
    if val >= 40: return "below average"
    if val >= 25: return "poor"
    return "very poor"

def format_skills(skills_list):
    skill_map = {
        '3': 'Three-Point Shooter', 'A': 'Athlete', 'B': 'Ball Handler',
        'Di': 'Interior Defender', 'Dp': 'Perimeter Defender',
        'Po': 'Post Scorer', 'Ps': 'Passer', 'R': 'Rebounder',
        'V': 'Volume Scorer',
    }
    return ', '.join(skill_map.get(s, s) for s in skills_list) if skills_list else 'None'

async def nbacomp(embed, player, commandInfo):
    from ai_media import safe_gemini_call
    from gemini_integration import model

    if not model:
        embed.add_field(name='NBA Comparison', value='AI service not available.', inline=False)
        return embed

    export = shared_info.serverExports[str(commandInfo['id'])]
    full_player = None
    for p in export['players']:
        if p['pid'] == player['pid']:
            full_player = p
            break

    if not full_player:
        embed.add_field(name='Error', value='Could not find player data.', inline=False)
        return embed

    season = commandInfo['season']
    age = season - full_player['born']['year']
    r = full_player['ratings'][-1]
    for rating in full_player['ratings']:
        if rating['season'] == season:
            r = rating
            break

    skills = format_skills(r.get('skills', []))

    ovr = r['ovr']
    if ovr >= 70: tier = "superstar-caliber"
    elif ovr >= 60: tier = "solid starter"
    elif ovr >= 55: tier = "role player"
    elif ovr >= 45: tier = "bench player"
    else: tier = "end-of-bench or developmental"

    # Pull actual season stats if available
    stats = pull_info.pstats(full_player, season)
    stats_line = ""
    similar = []
    if stats.get('gp', 0) > 0:
        rpg = (stats.get('orb', 0) + stats.get('drb', 0))
        stats_line = f"""
Season Stats (context only — stats can be inflated/deflated by team quality and role):
{stats['pts']:.1f} PPG, {rpg:.1f} RPG, {stats['ast']:.1f} APG, {stats['stl']:.1f} SPG, {stats['blk']:.1f} BPG
Shooting: {stats['fg']:.1f}% FG, {stats['tp']:.1f}% 3PT, {stats['ft']:.1f}% FT"""

        # Statistical similarity matching against real NBA data
        import nba_data
        if nba_data._df is not None:
            bbgm_stats = {
                'ppg': float(stats['pts']),
                'rpg': float(rpg),
                'apg': float(stats['ast']),
                'spg': float(stats['stl']),
                'bpg': float(stats['blk']),
                'tov': float(stats.get('tov', 0)),
                'mpg': float(stats.get('min', 0)),
                'fg_pct': float(stats['fg']),
                'tp_pct': float(stats['tp']),
                'ft_pct': float(stats['ft']),
            }
            similar = nba_data.find_similar(bbgm_stats, top_n=2)

    trait_checks = [
        (r.get('tp', 0), 'Shooting'), (r.get('ins', 0), 'Inside'), (r.get('dnk', 0), 'Finishing'),
        (r.get('pss', 0), 'Passing'), (r.get('drb', 0), 'Handles'), (r.get('diq', 0), 'Defense'),
        (r.get('spd', 0), 'Speed'), (r.get('stre', 0), 'Strength'), (r.get('jmp', 0), 'Athleticism'),
        (r.get('reb', 0), 'Rebounding'), (r.get('oiq', 0), 'Off. IQ')
    ]
    trait_checks.sort(key=lambda x: x[0], reverse=True)
    top_traits = [name for val, name in trait_checks[:3]]
    bottom_traits = [name for val, name in trait_checks[-3:]]

    current_line = f"✦ {' · '.join(top_traits)}\n✧ {' · '.join(bottom_traits)}\n\n"

    # League-relative context for the AI prompt — stops Gemini from writing
    # generic "good scorer" prose when the player is actually top-2% in the league.
    build_label, build_pctiles = _classify_build(player, r, commandInfo)
    fingerprint = _pctile_fingerprint_for_ai(build_pctiles)
    ai_context = ''
    if build_label or fingerprint:
        ai_context = '\nLeague context (use this for accuracy):\n'
        if build_label:
            ai_context += f'Build archetype: {build_label}\n'
        if fingerprint:
            ai_context += f'Percentile fingerprint — {fingerprint}\n'

    if similar:
        # Calculate similarity percentages from distance
        for s in similar:
            s['match_pct'] = max(0, round(100 / (1 + s['distance'])))

        # Build stat lines and Gemini prompt with the statistical matches
        comp_lines = []
        for s in similar:
            comp_lines.append(f"- {s['player']} ({s['season']}): {s['ppg']:.1f} PPG, {s['rpg']:.1f} RPG, {s['apg']:.1f} APG, {s['spg']:.1f} SPG, {s['bpg']:.1f} BPG, {s['fg_pct']:.1f}% FG, {s['tp_pct']:.1f}% 3PT, {s['ft_pct']:.1f}% FT")
        comp_list = "\n".join(comp_lines)

        prompt = f"""A basketball sim player has this profile:
Position: {r.get('pos', player['position'])}, Height: {player['height']}, Weight: {player['weight']} lbs, Age: {age}, OVR: {ovr}
Physical: hgt {r.get('hgt', 0)}, spd {r.get('spd', 0)}, stre {r.get('stre', 0)}, jmp {r.get('jmp', 0)}
Shooting: tp {r.get('tp', 0)}, ft {r.get('ft', 0)}, fg {r.get('fg', 0)}
Finishing: ins {r.get('ins', 0)}, dnk {r.get('dnk', 0)}
Playmaking: pss {r.get('pss', 0)}, drb {r.get('drb', 0)}
Defense: diq {r.get('diq', 0)}, reb {r.get('reb', 0)}
Basketball IQ: oiq {r.get('oiq', 0)}
Skills: {skills}
{stats_line}{ai_context}

These real NBA players were found as the closest statistical matches:
{comp_list}

For each player, write ONE punchy sentence (like a real scouting report) about the playstyle similarity. Be specific — name concrete skills, not generic phrases. Do NOT use "you" or "your" — refer to the sim player by name or in third person.

Reply with ONLY this format, nothing else:

1. {similar[0]['player']} ({similar[0]['season']}) — [one punchy sentence]
2. {similar[1]['player']} ({similar[1]['season']}) — [one punchy sentence]

No explanations, no introductions, no commentary. Just the 2 lines."""

        result = await safe_gemini_call(prompt)

        # Build combined display: stats + scouting blurb per comp
        # Parse AI result into per-player lines
        ai_lines = {}
        if result:
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and '—' in line:
                    blurb = line.split('—', 1)[1].strip()
                    for idx, s in enumerate(similar):
                        if s['player'] in line:
                            ai_lines[idx] = blurb
                            break

        comp_display = []
        for idx, s in enumerate(similar):
            entry = f"**{s['player']}** ({s['season']} {s['team']}) — {s['match_pct']}% match"
            entry += f"\n{s['ppg']:.1f} PPG / {s['rpg']:.1f} RPG / {s['apg']:.1f} APG — {s['fg_pct']:.1f}% FG, {s['tp_pct']:.1f}% 3PT"
            if idx in ai_lines:
                entry += f"\n> *{ai_lines[idx]}*"
            comp_display.append(entry)

        embed.add_field(name='NBA Comparisons', value=current_line + "\n\n".join(comp_display), inline=False)
    else:
        # No stat matches — fall back to pure AI comparison
        prompt = f"""Given this basketball player's skill profile, find 2 real NBA players (past or present) who have a similar playstyle and skill set. Match based on how they play, not just stats.

Rating scale: 0-100 where 80+ = elite, 70-79 = excellent, 60-69 = above average, 50-59 = average, 40-49 = below average, <40 = poor

Position: {r.get('pos', player['position'])}
Height: {player['height']}, Weight: {player['weight']} lbs
Age: {age} | Player level: {tier} (OVR {ovr})

Physical: hgt {r.get('hgt', 0)}, spd {r.get('spd', 0)}, stre {r.get('stre', 0)}, jmp {r.get('jmp', 0)}
Shooting: tp {r.get('tp', 0)}, ft {r.get('ft', 0)}, fg {r.get('fg', 0)}
Finishing: ins {r.get('ins', 0)}, dnk {r.get('dnk', 0)}
Playmaking: pss {r.get('pss', 0)}, drb {r.get('drb', 0)}
Defense: diq {r.get('diq', 0)}, reb {r.get('reb', 0)}
Basketball IQ: oiq {r.get('oiq', 0)}
Special skills: {skills}
{ai_context}

IMPORTANT: Match comparisons to the player's caliber. A role player should be compared to real NBA role players, not Hall of Famers. A superstar can be compared to superstars.

Reply with ONLY this format, nothing else:

1. **[Player Name]** ([Year]) — [one punchy scouting-style sentence about the playstyle similarity]
2. **[Player Name]** ([Year]) — [one punchy scouting-style sentence about the playstyle similarity]

No explanations, no introductions, no commentary. Just the 2 lines."""

        result = await safe_gemini_call(prompt)
        if not result:
            embed.add_field(name='NBA Comparisons', value=current_line + 'AI comparison timed out. Try again.', inline=False)
            return embed
        output = current_line + result
        if len(output) > 1024:
            output = output[:1021] + "..."
        embed.add_field(name='NBA Comparisons', value=output, inline=False)

    return embed

async def scout(embed, player, commandInfo):
    from ai_media import safe_gemini_call
    from gemini_integration import model

    if not model:
        embed.add_field(name='Scouting Report', value='AI service not available.', inline=False)
        return embed

    export = shared_info.serverExports[str(commandInfo['id'])]
    full_player = None
    for p in export['players']:
        if p['pid'] == player['pid']:
            full_player = p
            break

    if not full_player:
        embed.add_field(name='Error', value='Could not find player data.', inline=False)
        return embed

    season = commandInfo['season']
    age = season - full_player['born']['year']
    r = full_player['ratings'][-1]
    for rating in full_player['ratings']:
        if rating['season'] == season:
            r = rating
            break
    skills = format_skills(r.get('skills', []))
    experience = len(player['seasonsPlayed'])

    is_prospect = experience <= 1 and full_player['draft']['year'] >= season

    # Determine player tier from OVR/POT
    ovr = r['ovr']
    pot = r['pot']
    if ovr >= 70: tier = "superstar-caliber player"
    elif ovr >= 60: tier = "solid starter"
    elif ovr >= 55: tier = "role player"
    elif ovr >= 45: tier = "bench player"
    else: tier = "end-of-bench or developmental player"

    if pot >= 70: ceiling = "superstar ceiling"
    elif pot >= 60: ceiling = "starter ceiling"
    elif pot >= 55: ceiling = "role player ceiling"
    else: ceiling = "limited ceiling"

    # Pull actual season stats if available
    stats = pull_info.pstats(full_player, season)
    stats_line = ""
    if stats.get('gp', 0) > 0:
        rpg = (stats.get('orb', 0) + stats.get('drb', 0))
        stats_line = f"""
Season Stats (context only — stats can be inflated/deflated by team quality and role):
{stats['pts']:.1f} PPG, {rpg:.1f} RPG, {stats['ast']:.1f} APG, {stats['stl']:.1f} SPG, {stats['blk']:.1f} BPG
Shooting: {stats['fg']:.1f}% FG, {stats['tp']:.1f}% 3PT, {stats['ft']:.1f}% FT"""

    # League-relative context so the AI can write specific evaluations
    # instead of generic "good shooter" prose. Skipped silently if pctiles
    # aren't available (e.g. free agents).
    build_label, build_pctiles = _classify_build(player, r, commandInfo)
    fingerprint = _pctile_fingerprint_for_ai(build_pctiles)
    league_context = ''
    if build_label or fingerprint:
        league_context = '\nLeague context (use this for accuracy):\n'
        if build_label:
            league_context += f'Build archetype: {build_label}\n'
        if fingerprint:
            league_context += f'Percentile fingerprint — {fingerprint}\n'

    wingspanText = estimate_wingspan(full_player, r)
    wingspan_part = f", {wingspanText} wingspan" if wingspanText else ""

    scouting_profile = f"""Rating scale: 0-100 where 80+ = elite, 70-79 = excellent, 60-69 = above average, 50-59 = average, 40-49 = below average, <40 = poor

Player: {player['name']}
Position: {r.get('pos', player['position'])} | Age: {age} | {player['height']}{wingspan_part}, {player['weight']} lbs
(Weigh his length naturally like a real scout would — long arms boost defensive/finishing projection, short arms are a flaw worth noting — but don't make wingspan the centerpiece.)
Experience: {experience} seasons
Current level: {tier} (OVR {ovr}) | Upside: {ceiling} (POT {pot})

Physical: hgt {r.get('hgt', 0)}, spd {r.get('spd', 0)}, stre {r.get('stre', 0)}, jmp {r.get('jmp', 0)}
Shooting: tp {r.get('tp', 0)}, ft {r.get('ft', 0)}, fg {r.get('fg', 0)}
Finishing: ins {r.get('ins', 0)}, dnk {r.get('dnk', 0)}
Playmaking: pss {r.get('pss', 0)}, drb {r.get('drb', 0)}
Defense: diq {r.get('diq', 0)}, reb {r.get('reb', 0)}
Basketball IQ: oiq {r.get('oiq', 0)}
Special skills: {skills}
{stats_line}{league_context}"""

    if is_prospect:
        combine = combine_results(full_player, r)
        if combine:
            embed.add_field(name='Combine Results', value=combine, inline=False)
        notebook = prospect_notebook(export, full_player, r)
        if notebook:
            embed.add_field(name="Scout's Notebook", value=notebook, inline=False)
        combine_context = f"\nDraft combine results:\n{combine}\n" if combine else ""
        if notebook:
            combine_context += f"\nScout's notebook (weave these into the report naturally):\n{notebook}\n"
        prompt = f"""Write a pre-draft scouting report for this basketball prospect. Write like a real NBA scout — no numbers, no ratings, just basketball evaluation.

{scouting_profile}{combine_context}

Format EXACTLY like this:

**Physical Profile:** [1-2 sentences — body, athleticism, how he moves]
**Offensive Tools:** [1-2 sentences — shooting, finishing, creating, passing]
**Defensive Upside:** [1 sentence — what kind of defender could he be]
**Concerns:** [1 sentence — what needs to develop]
**Projection:** [1 sentence — what archetype and role he could become]
**NBA Projection:** [NBA Player Name] — [what this player could become based on their ceiling and skill profile]

CRITICAL: Keep the TOTAL response under 900 characters. Never mention ratings, numbers, or scales."""
    else:
        prompt = f"""Write a basketball scouting report for this player. Write like a real NBA scout — no numbers, no ratings, just basketball evaluation.

{scouting_profile}

Format EXACTLY like this:

**Strengths:** [2 sentences — what he does well on the court, be descriptive and specific]

**Weaknesses:** [2 sentences — what he struggles with, be specific]

**Role:** [1 sentence — what role does he fill on a team]

**Outlook:** [1 sentence — where is his career headed given age and upside]

**NBA Comparison:** [NBA Player Name] — [few words why, based on skill profile not stats]

CRITICAL: Keep the TOTAL response under 900 characters. Never mention ratings, numbers, or scales."""

    result = await safe_gemini_call(prompt)
    if not result:
        embed.add_field(name='Scouting Report', value='AI scouting timed out. Try again.', inline=False)
        return embed

    if len(result) > 1024:
        result = result[:1021] + "..."
    embed.add_field(name='Scouting Report', value=result, inline=False)
    return embed

async def playerroast(embed, player, commandInfo):
    from ai_media import safe_gemini_call
    from gemini_integration import model

    if not model:
        embed.add_field(name='Roast', value='AI service not available.', inline=False)
        return embed

    export = shared_info.serverExports[str(commandInfo['id'])]
    full_player = None
    for p in export['players']:
        if p['pid'] == player['pid']:
            full_player = p
            break

    if not full_player:
        embed.add_field(name='Error', value='Could not find player data.', inline=False)
        return embed

    season = commandInfo['season']
    age = season - full_player['born']['year']
    stats = pull_info.pstats(full_player, season)
    career = pull_info.pstats(full_player, 'career')
    experience = len(player['seasonsPlayed'])

    # Get team name
    team_name = "Free Agent"
    for tm in export['teams']:
        if tm['tid'] == full_player['tid']:
            team_name = f"{tm['region']} {tm['name']}"
            break

    prompt = f"""Roast this basketball player in 2-3 sentences. Be funny, savage, and specific to their stats. No mercy.

Player: {player['name']}
Age: {age} | Position: {player['position']} | Team: {team_name}
Experience: {experience} seasons | Contract: ${player['contractAmount']}M/yr
Season Stats: {stats['pts']:.1f} PPG, {(stats.get('orb',0)+stats.get('drb',0)):.1f} RPG, {stats['ast']:.1f} APG, {stats['blk']:.1f} BPG, {stats['stl']:.1f} SPG
Shooting: {stats['fg']:.1f}% FG, {stats['tp']:.1f}% 3PT, {stats['ft']:.1f}% FT
Career: {career['pts']:.1f} PPG, {(career.get('orb',0)+career.get('drb',0)):.1f} RPG, {career['ast']:.1f} APG

Keep it short and brutal. No intro, just the roast. Never mention ratings or OVR."""

    result = await safe_gemini_call(prompt)
    if not result:
        embed.add_field(name='Roast', value='Even the AI refused to waste time on this player.', inline=False)
        return embed

    if len(result) > 1024:
        result = result[:1021] + "..."
    embed.add_field(name='Roast', value=result, inline=False)
    return embed


_MOOD_TRAIT_LABELS = {
    'W': ('Winning', 'wants to play for a contender'),
    'F': ('Fame', 'prefers big markets and engaged fan bases'),
    'L': ('Loyal', 'favors staying with current team long-term'),
    '$': ('Money', 'chases the biggest contract; rarely refuses to negotiate'),
}


def _compute_mood_components(p, target_team, export):
    """Python port of ZenGM's src/worker/core/player/moodComponents.ts.

    Returns a dict of the 9 mood components (each bounded per BBGM rules
    and scaled by trait multipliers). Skips difficulty modulation (not
    exposed) and the playing-time regression (requires league-wide minute
    distribution that's heavy to reconstruct — defaults to 0).
    """
    import math
    ga = export['gameAttributes']
    season = ga.get('season', 0)
    teams = export['teams']
    active = [t for t in teams if not t.get('disabled')]

    comp = {
        'marketSize': 0.0, 'facilities': 0.0, 'teamPerformance': 0.0,
        'hype': 0.0, 'loyalty': 0.0, 'trades': 0.0, 'playingTime': 0.0,
        'rookieContract': 0.0, 'relatives': 0.0,
    }

    target_season = None
    for s in target_team.get('seasons', []):
        if s.get('season') == season:
            target_season = s; break

    # Tied-rank averaging — when several teams share a population value
    # (e.g. equalizeRegions=True flattens all pops to the same number),
    # every team should get the same popRank, not a tiebreaker-driven
    # unique index. BBGM's addPopRank uses standard averaged ranking.
    target_pop = target_team.get('pop', 0)
    higher = sum(1 for t in active if t.get('pop', 0) > target_pop)
    ties = sum(1 for t in active if t.get('pop', 0) == target_pop)
    pop_rank = higher + (ties + 1) / 2
    denom = max(1, len(active) - 1)
    comp['marketSize'] = -2 + ((len(active) - pop_rank) / denom) * 4

    # Facilities — ZenGM's getLevelLastThree short-circuits to
    # DEFAULT_LEVEL (effect=0) when the `budget` setting is off, which is
    # common in custom leagues. expenseLevels stores level*gp summed over
    # the season, so the per-game level is the value divided by games
    # played that season. Avg the last 3 seasons.
    budget_on = bool(ga.get('budget', False))
    if budget_on:
        fac_levels = []
        for s in target_team.get('seasons', [])[-3:]:
            el = s.get('expenseLevels')
            raw = None
            if isinstance(el, dict):
                raw = el.get('facilities')
            elif isinstance(el, list):
                for item in el:
                    if isinstance(item, (list, tuple)) and len(item) == 2 and item[0] == 'facilities':
                        raw = item[1]; break
            if not isinstance(raw, (int, float)):
                continue
            gp = (s.get('won', 0) + s.get('lost', 0)
                  + s.get('tied', 0) + s.get('otl', 0))
            if gp > 0:
                fac_levels.append(raw / gp)
        if fac_levels:
            avg = sum(fac_levels) / len(fac_levels)
            x = (3 * (round(avg) - 1)) / 99 - 1
            effect = 1.1 * (x if x < 0 else math.tanh(x))
            comp['facilities'] = 2 * effect
    # else: facilities stays 0 — budget off means no facilities effect

    if target_season:
        won = target_season.get('won', 0)
        lost = target_season.get('lost', 0)
        tied = target_season.get('tied', 0)
        gp = won + lost + tied
        if gp > 0:
            winp = (won + 0.5 * tied) / gp
            tp = -2 + ((winp - 0.25) * 4) / 0.5
            if tp < 0:
                tp *= 2
            comp['teamPerformance'] = min(2, tp)

    if target_season:
        h = target_season.get('hype')
        if isinstance(h, (int, float)):
            comp['hype'] = -2 + 4 * h

    n_with = sum(1 for r in (p.get('stats') or []) if r.get('tid') == target_team['tid'])
    comp['loyalty'] = n_with / 8
    if p.get('tid') == target_team['tid']:
        comp['loyalty'] += 2

    n_traded = None
    if p.get('tid', -1) == -1:
        normalized = p.get('numPlayersTradedAwayNormalized') or {}
        if isinstance(normalized, dict):
            n_traded = normalized.get(str(target_team['tid']))
    if n_traded is None:
        recent = target_team.get('seasons', [])[-3:]
        n_traded = (sum(s.get('numPlayersTradedAway', 0) for s in recent) / len(recent)) if recent else 5
    comp['trades'] = min(0, -(n_traded - 5) / 4)

    contract = p.get('contract') or {}
    if contract.get('rookie') or contract.get('rookieResign'):
        comp['rookieContract'] = 8

    rel_pids = {r.get('pid') for r in (p.get('relatives') or []) if r.get('pid') is not None}
    if rel_pids:
        team_pids = {pp['pid'] for pp in export.get('players', []) if pp.get('tid') == target_team['tid']}
        comp['relatives'] = 2 * len(rel_pids & team_pids)

    # Difficulty modulation — exact port of moodComponents.ts.
    # User-team branch shrinks positives / amplifies negatives as
    # difficulty rises. Non-user-team branch (or spectator) applies a
    # baseline 0.5-amount moderation so AI teams' players are stickier.
    spectator = bool(ga.get('spectator', False))
    difficulty = 0 if spectator else (ga.get('difficulty', 0) or 0)
    user_tids = ga.get('userTids') or []
    target_is_user = target_team['tid'] in user_tids and not spectator
    if target_is_user:
        if difficulty != 0:
            for key in list(comp.keys()):
                v = comp[key]
                if difficulty > 0:
                    comp[key] = v / (1 + difficulty) if v > 0 else v * (1 + difficulty)
                else:
                    comp[key] = v * (1 - difficulty) if v > 0 else v / (1 - difficulty)
    else:
        amount = 0.5 - max(-0.25, min(0.25, difficulty / 2))
        for key in list(comp.keys()):
            v = comp[key]
            if amount > 0:
                comp[key] = v / (1 + amount) if v > 0 else v * (1 + amount)
            else:
                comp[key] = v * (1 - amount) if v > 0 else v / (1 - amount)

    # Bounds (post-difficulty, pre-traits)
    comp['marketSize'] = max(-2, min(2, comp['marketSize']))
    comp['facilities'] = max(-2, min(2, comp['facilities']))
    comp['teamPerformance'] = min(2, comp['teamPerformance'])
    comp['hype'] = max(-2, min(2, comp['hype']))
    comp['loyalty'] = max(0, comp['loyalty'])
    comp['trades'] = min(0, comp['trades'])
    comp['playingTime'] = min(2, comp['playingTime'])
    comp['rookieContract'] = max(0, comp['rookieContract'])

    if ga.get('playerMoodTraits', True):
        traits = p.get('moodTraits') or []
        if 'F' in traits:
            comp['marketSize'] *= 2.5; comp['hype'] *= 2.5; comp['playingTime'] *= 2.5
        if 'L' in traits:
            comp['marketSize'] *= 0.5; comp['loyalty'] *= 2.5; comp['trades'] *= 2.5
        if '$' in traits:
            comp['facilities'] *= 1.5; comp['marketSize'] *= 0.5; comp['teamPerformance'] *= 0.5
        if 'W' in traits:
            comp['marketSize'] *= 0.5; comp['playingTime'] *= 0.5; comp['teamPerformance'] *= 2.5

    return comp


_MOOD_COMPONENT_ORDER = (
    'marketSize', 'facilities', 'teamPerformance', 'hype',
    'loyalty', 'trades', 'playingTime', 'rookieContract', 'relatives',
)


def _mood_component_text(key, value, gender='male'):
    """BBGM's exact phrasing per component+sign, ported from Mood.tsx.

    Returns None for value == 0 (BBGM hides those lines)."""
    if value == 0:
        return None
    is_female = gender == 'female'
    he = 'she' if is_female else 'he'
    his = 'her' if is_female else 'his'
    if value > 0:
        return {
            'marketSize':     'Enjoys playing in a large market',
            'facilities':     'Likes the lavish team facilities',
            'teamPerformance':"Happy with the team's performance",
            'hype':           'Likes the energy from the fan base',
            'loyalty':        'Is loyal to the franchise',
            'playingTime':    f'Happy with {his} playing time',
            'rookieContract': 'Eager to sign first non-rookie contract',
            'relatives':      f'Wants to play with {his} ' + ('relative' if value <= 2 else 'relatives'),
        }.get(key)
    return {
        'marketSize':     'Dislikes playing in a small market',
        'facilities':     'Dislikes the outdated team facilities',
        'teamPerformance':"Unhappy with the team's performance",
        'hype':           'Wishes fans were more excited',
        'trades':         f"Worried {he}'ll be traded away",
        'playingTime':    'Wants more playing time',
    }.get(key)


def _compute_will_resign_probability(p, target_team, components, export):
    """Port of moodInfo.ts probability formula (basketball baselines).

    Logit on (sumComponents - 0.5 - valueDiffPenalty - aiPenalty), with
    valueDiff capped when re-signing your own player. Honors the
    playersRefuseToNegotiate and rookiesCanRefuse game settings."""
    import math
    ga = export['gameAttributes']

    if not ga.get('playersRefuseToNegotiate', True):
        return 1.0
    if components.get('rookieContract', 0) > 0 and not ga.get('rookiesCanRefuse', True):
        return 1.0

    sum_components = sum(components.values())
    sum_and_stuff = sum_components - 0.5

    if p.get('tid', -1) == -1:  # free agent: longer in FA = more willing
        days = max(0, min(30, p.get('numDaysFreeAgent', 0)))
        sum_and_stuff += days / 3

    # valueDiff penalty — better players are pickier
    p_value = p.get('value', 65)
    value_diff = (p_value - 65) / 2  # basketball baseline = 65
    MAX_RESIGNING_VALUE_DIFF = 4
    if value_diff > MAX_RESIGNING_VALUE_DIFF and p.get('tid') == target_team['tid']:
        value_diff = MAX_RESIGNING_VALUE_DIFF
    if value_diff > 0:
        sum_and_stuff -= math.sqrt(value_diff)
    else:
        sum_and_stuff -= value_diff

    # AI-team penalty (more AI players test FA)
    user_tids = ga.get('userTids') or []
    if target_team['tid'] not in user_tids:
        sum_and_stuff -= 3

    return 1 / (1 + math.exp(-0.7 * sum_and_stuff))


_MOOD_TRAIT_NAMES = {
    'W': 'winning', 'F': 'fame', 'L': 'loyalty', '$': 'money',
}


async def mood(embed, player, commandInfo):
    """Show a player's mood toward their current team, mirroring BBGM's
    in-game mood popover (Mood.tsx). Components are rounded to integers,
    zero values are hidden, each non-zero component renders as the exact
    descriptive phrase BBGM uses. Probability uses BBGM's logit formula
    from moodInfo.ts — not the bot's homemade resign_odds."""
    export = shared_info.serverExports[str(commandInfo['id'])]
    full_player = None
    for p in export['players']:
        if p['pid'] == player['pid']:
            full_player = p; break
    if full_player is None:
        embed.add_field(name='Error', value='Could not find player data.', inline=False)
        return embed

    tid = full_player.get('tid', -1)
    if tid < 0:
        embed.add_field(name='No current team', value='*Free agent — mood breakdown needs a target team.*', inline=False)
        return embed

    target_team = None
    for t in export['teams']:
        if t['tid'] == tid:
            target_team = t; break
    if target_team is None:
        embed.add_field(name='Error', value='Could not resolve current team.', inline=False)
        return embed

    ga = export['gameAttributes']
    gender = ga.get('gender', 'male')

    # Priorities (mood traits) — BBGM's one-line format
    trait_codes = full_player.get('moodTraits') or []
    if trait_codes:
        prio_names = [_MOOD_TRAIT_NAMES.get(c, c) for c in trait_codes]
        embed.add_field(name='Priorities', value=', '.join(prio_names), inline=False)

    # Component breakdown — BBGM's phrasing, rounded, zeros hidden
    try:
        comp = _compute_mood_components(full_player, target_team, export)
        rounded = {k: round(v) for k, v in comp.items()}
        lines = []
        for key in _MOOD_COMPONENT_ORDER:
            v = rounded.get(key, 0)
            text = _mood_component_text(key, v, gender)
            if text:
                sign = '+' if v > 0 else ''
                lines.append(f"**{sign}{v}** {text}")
        if not lines:
            lines.append('*No notable factors — fully neutral mood toward this team.*')

        prob = _compute_will_resign_probability(full_player, target_team, comp, export)
        if prob > 0.99 and prob < 1:
            pct_str = '>99'
        elif prob > 0 and prob < 0.01:
            pct_str = '<1'
        else:
            pct_str = f"{round(prob * 100)}"

        # "with you" if it's the user's team, else "with [team]"
        user_tids = ga.get('userTids') or []
        team_label = 'with you' if target_team['tid'] in user_tids else f"with the {target_team['region']} {target_team['name']}"
        lines.append(f"\n**Odds player would re-sign {team_label}: {pct_str}%**")

        embed.add_field(
            name=f"Mood toward {target_team['region']} {target_team['name']}",
            value='\n'.join(lines),
            inline=False,
        )
    except Exception as e:
        embed.add_field(name='Mood Breakdown', value=f'*Could not compute mood: {type(e).__name__}.*', inline=False)

    return embed


async def nickname(text, message):
    serversList = shared_info.serversList
    serverId = str(message.guild.id)
    export = shared_info.serverExports[serverId]
    players = export['players']
    settings = serversList[serverId]
    prefix = settings.get('prefix', '-')

    if "nickname" not in settings:
        nicks = dict()
    else:
        nicks = settings['nickname']

    # Get user's team id
    userTid = settings.get('teamlist', {}).get(str(message.author.id), -1000)

    embed = discord.Embed(title='Nicknames', description="The second dumbest feature in the bot (trailing only -mostaverage)")

    if len(text) == 1:
        embed.add_field(name="Please say one of the following", value=f"``{prefix}nickname view``\n``{prefix}nickname add [Player]: [Nickname]``\n``{prefix}nickname remove [Player]``")
        await message.channel.send(embed=embed)
        return

    subcmd = str.lower(text[1])

    if subcmd == "add":
        raw = message.content
        if ":" not in raw:
            embed.add_field(name="Format", value=f"``{prefix}nickname add Kobe Bryant: The Black Mamba``")
            await message.channel.send(embed=embed)
            return
        pname = " ".join(raw.split(":")[0].split(" ")[2:])
        nname = raw.split(":")[1].strip()
        player = basics.find_match(pname, export, False, True, settings=settings)
        for p in players:
            if p['pid'] == player:
                if p['tid'] == -2 or p['tid'] == userTid or message.author.guild_permissions.manage_messages:
                    if len(nname) == 0:
                        embed.add_field(name="The emptyness of my soul...", value="can still not yet be compared to the emptiness of the nickname you provided.")
                    else:
                        isunique = True
                        for item, value in nicks.items():
                            if value.lower().strip() == nname.lower().strip() and item != str(p['pid']):
                                isunique = False
                                for p2 in players:
                                    if p2['pid'] == int(item):
                                        embed.add_field(name="Non-unique", value="Already used for " + p2['firstName'] + " " + p2['lastName'])
                        if isunique:
                            nicks[str(p['pid'])] = nname
                            settings['nickname'] = nicks
                            await basics.save_db(serversList)
                            embed.add_field(name="Nicknames", value="Added nickname **" + nname + "** for " + p['firstName'] + " " + p['lastName'])
                else:
                    embed.add_field(name="Can't add a nickname for a guy not on your team", value="for player " + p['firstName'] + " " + p['lastName'])

    elif subcmd == "view":
        s = ""
        field_count = 0
        for p in players:
            if str(p['pid']) in nicks:
                line = "**" + p['firstName'] + " " + p['lastName'] + "**: " + nicks[str(p['pid'])] + "\n"
                if len(s) + len(line) > 900:
                    field_count += 1
                    embed.add_field(name="Nicknames" if field_count == 1 else "Nicknames (cont.)", value=s, inline=False)
                    s = ""
                s += line
        if len(s) > 0:
            field_count += 1
            embed.add_field(name="Nicknames" if field_count == 1 else "Nicknames (cont.)", value=s, inline=False)
        if field_count == 0:
            embed.add_field(name="Nicknames", value="No nicknames set yet.")

    elif subcmd == "remove":
        if len(text) < 3:
            embed.add_field(name="Format", value=f"``{prefix}nickname remove [Player Name]`` or ``{prefix}nickname remove all``")
            await message.channel.send(embed=embed)
            return
        pname = " ".join(text[2:])
        if pname.lower() == 'all':
            if message.author.guild_permissions.manage_messages:
                removed = []
                for p in players:
                    if str(p['pid']) in nicks:
                        removed.append(p['firstName'] + " " + p['lastName'])
                nicks.clear()
                settings['nickname'] = nicks
                await basics.save_db(serversList)
                if removed:
                    embed.add_field(name="Removed all nicknames", value=", ".join(removed))
                else:
                    embed.add_field(name="Nothing to remove", value="No nicknames were set.")
            else:
                embed.add_field(name="Mods only", value="Only moderators can remove all nicknames.")
        else:
            player = basics.find_match(pname, export, False, True, settings=settings)
            for p in players:
                if p['pid'] == player:
                    if p['tid'] == -2 or p['tid'] == userTid or message.author.guild_permissions.manage_messages:
                        if str(p['pid']) in nicks:
                            del nicks[str(p['pid'])]
                            settings['nickname'] = nicks
                            await basics.save_db(serversList)
                            embed.add_field(name="Removed nickname for " + p['firstName'] + " " + p['lastName'], value="Their nickname is now gone.")
                        else:
                            embed.add_field(name="No nickname", value=p['firstName'] + " " + p['lastName'] + " doesn't have a nickname.")
                    else:
                        embed.add_field(name="Can't remove nickname for a guy not on your team", value="for player " + p['firstName'] + " " + p['lastName'])
    else:
        embed.add_field(name="Please say one of the following", value=f"``{prefix}nickname view``\n``{prefix}nickname add [Player]: [Nickname]``\n``{prefix}nickname remove [Player]``")

    embed.set_footer(text=shared_info.embedFooter(message.guild))
    await message.channel.send(embed=embed)
