from shared_info import serverExports
from shared_info import serversList
import shared_info
import pull_info
import basics
import random
import json
import numpy as np
import discord
from sklearn.linear_model import LinearRegression
import plotly_express as px
import player_commands

import pandas
#LEAGUE COMMANDS
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
def findnlargest(listoflists,index,n):#takes in a list of equally length list finds the top n entries according to index
    x=1
    returnedlist = []
    while x<=n:
        maximum = listoflists[0][index]
        maxdex = 0
        for i in range (0,len(listoflists)):
            if listoflists[i][index]>maximum:
                maxdex = i
                maximum = listoflists[i][index]
        returnedlist.append(listoflists[maxdex])   
        listoflists.pop(maxdex)
        x+=1
    return returnedlist
def godprogs(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    message = commandInfo['message']
    minyears = 3
    minovr=0
    if message.content.__contains__(" "):
        age= int(message.content.split(" ")[1])
        if message.content.count(" ")>1:
            
            minyears= int(message.content.split(" ")[2])
            if minyears>11:
                minovr = minyears
                minyears = 3
            if message.content.count(" ")>2:
                if minovr == 0:
                    minovr = int(message.content.split(" ")[3])
                
            
    else:
        age = 0

    saddeststreaks = []
    for player in export['players']:
        ratings = player['ratings']
        birthyear = player.get("born").get("year")
        saddeststreak = [0,0,0,0,0,0]
        #first = True
        firstyear = ratings[0].get("season")
        ovrs = []
        curseason = firstyear-1
        for rating in ratings:
            if not rating.get("season")==curseason:
                ovrs.append(rating.get("ovr"))
                curseason = rating.get("season")
        if not ovrs[0]==ratings[0].get("ovr"):
            ovrs[0]=ratings[0].get("ovr")
        
        for x in range(0,len(ovrs)):
            for y in range (x+1,len(ovrs)):
                #print("c")
                if y-x >= minyears and x+firstyear-birthyear>=age:
                    if ovrs[y]>ovrs[x] and ovrs[x]>minovr:
                        #print("a")
                        if (-ovrs[x]+ovrs[y])/(y-x)>saddeststreak[5]:
                            saddeststreak = [player['firstName']+" "+player['lastName'], firstyear+x, firstyear+y, ovrs[x],ovrs[y],round((-ovrs[x]+ovrs[y])/(y-x),2)]
        if not sum(saddeststreak[1:])==0:
            saddeststreaks.append(saddeststreak)
    #print(saddeststreaks)
    n1 = findnlargest(saddeststreaks, 5, min(10,len(saddeststreaks)))
    embed = discord.Embed(title = "Whatever, here you go, i'm tired of all these calculations. Zzz.....")
    rank = 1
    bigstring = ""
    for n in n1:
        string = str(rank)+". **"+n[0]+"** "+str(n[1])+"-"+str(n[2])+" **"+str(n[3])+"→"+str(n[4])+"**, rise per year of **"+str(n[5])+"**.\n"
        bigstring += string
        
        rank += 1
    embed.add_field(name="Oh dear.", value= bigstring,inline=False)
    embed.add_field(name="Tip.", value= "You can specify first the minimum age to get young players who progressed poorly, and secondly the stretch of years.",inline=False)
    return embed

def sadprogs(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    message = commandInfo['message']
    minyears = 3

    if message.content.__contains__(" "):
        age= int(message.content.split(" ")[1])
        if message.content.count(" ")>1:
            minyears= int(message.content.split(" ",2)[2])
            if minyears>11:
                embed.add_field(name = 'error', value = "Over such long durations, the soothing hands of time would have diluted the sadness of any bad progs, hence, none make the list.")
                return embed
    else:
        age = 30
    if age>30:
        embed.add_field(name = 'error', value = "There are no sad progs after age 30, because everyone is in decline. And that fact is just terribly upsetting.")
        return embed
    if age<19:
        embed.add_field(name = 'error', value = "They are not yet at an age that can properly comprehend sadness.")
        return embed
    saddeststreaks = []
    for player in export['players']:

        ratings =player['ratings']
        birthyear = player.get("born").get("year")
        saddeststreak = [0,0,0,0,0,0]
        #first = True
        firstyear = ratings[0].get("season")
        ovrs = []
        curseason = firstyear-1
        for rating in ratings:
            if not rating.get("season")==curseason:
                ovrs.append(rating.get("ovr"))
                curseason = rating.get("season")
        if not ovrs[-1]==ratings[-1].get("ovr"):
            ovrs[-1]=ratings[-1].get("ovr")
        
        for x in range(0,len(ovrs)):
            for y in range (x+1,len(ovrs)):
                #print("c")
                if y-x >= minyears and y+firstyear-birthyear<=age:
                    if ovrs[y]<ovrs[x]:
                        #print("a")
                        if (ovrs[x]-ovrs[y])/(y-x)>saddeststreak[5]:
                            saddeststreak = [player['firstName']+" "+player['lastName'], firstyear+x, firstyear+y, ovrs[x],ovrs[y],round((ovrs[x]-ovrs[y])/(y-x),2)]
        if not sum(saddeststreak[1:])==0:
            saddeststreaks.append(saddeststreak)
    #print(saddeststreaks)
    n1 = findnlargest(saddeststreaks, 5, min(10,len(saddeststreaks)))
    #embed = discord.Embed(title = "Us mortals are not yet prepared for the sadness that I am about to present. So rise above the mundane physical realm, or get your tissues ready.")
    rank = 1
    bigstring = ""
    for n in n1:
        string = str(rank)+". **"+n[0]+"** "+str(n[1])+"-"+str(n[2])+" **"+str(n[3])+"→"+str(n[4])+"**, drop per year of **"+str(n[5])+"**.\n"
        bigstring += string
        
        rank += 1
    embed.add_field(name="And here we go, into the annals of despair.\nHere are the worst "+str(minyears)+"-year continual stretches of player progression for players "+str(age)+" years or younger.", value= bigstring,inline=False)
    embed.add_field(name="Tip.", value= "You can specify first the maximum age to get young players who progressed poorly, and secondly the stretch of years.")
    return embed


def getabbrev(export, tid):
    for t in export['teams']:
        if t['tid'] == tid:
            return t['abbrev']
def gettname(export, tid):
    for t in export['teams']:
        if t['tid'] == tid:
            return t['region']+" "+t['name']
def gsos(export, tid):
    road = 0
    home = 0
    oppWins = 0
    oppLoses = 0
    for s in export['schedule']:
        oppTid = None
        gametype = "none"
        if s['homeTid'] == tid:
            oppTid = s['awayTid']
            home += 1
            gametype = "home"
        if s['awayTid'] == tid:
            oppTid = s['homeTid']
            road += 1
            gametype = "away"
        if oppTid != None:
            for t in export['teams']:
                if t['tid'] == oppTid:
                    oppWins += t['seasons'][-1]['won']
                    oppLoses += t['seasons'][-1]['lost']
    if home + road == 0:
        return 0.5
    
    sos = oppWins / (oppWins+oppLoses)
    homediff = (home-road)/(home+road)
    return sos-0.1*homediff
def specialists(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    message = commandInfo['message']
    content = ""
    if len(message.content.split(" ")) > 1:
        content = message.content.split(" ",1)[1]
    year = -100
    if content[-4:].__contains__("1") or content[-4:].__contains__("2"):
        year = int(content[-4:])
        content = content[0:-4]
    specialities = ["athleticism","rebounding","passing","defense","shooting","scoring", "pass+shoot", "agility","inside"]
    abbrevs = ["ath","reb","pass","def","shot","sco", "p s", "agi","ins"]
    index = -1
    for item in range (0,len(specialities)):
        
        if content.strip().lower() == specialities[item] or content.strip().lower() == abbrevs[item]:
            index = item
    if index == -1:
        embed.add_field( name = "Please specify a speciality. Specialities include "+str(specialities), value = "Abbreviations for these specialities (in order) are "+str(abbrevs))
        
        return embed
    print(index)
    specialratings = [["hgt","stre","endu","jmp","spd"],["hgt","reb","spd","jmp","stre"],["drb","pss"],["hgt","reb","diq","stre","jmp","spd"],["fg","ft","tp"],["fg","tp","ft","ins","dnk"],["pss","drb","tp","fg"],["spd","jmp"],["ins","dnk","hgt","stre"]]
    weights = [[1,1,0.25,1,1],[1,2,0.25,0.25,0.25],[0.5,1],[0.25,0.25,1,0.25,0.5,0.5],[0.5,0.25,1],[0.75,0.5,1,1,1],[1,0.75,0.75,1],[1,1],[1,0.5,0.5,0.5]]
    dictofrelevantratings = dict()
    names = dict()
    
    for p in players:
        number =0
        ss = p['ratings']
        for ratingseason in ss:
            number += 1

            ss = p['stats']
            for elm in ss:
                if elm.get("season") == ratingseason.get("season"):
                    ratingseason.update({"tid":elm.get("tid")})
            if ((year>-100 and ratingseason.get("season") == year) or year == -100) and (ratingseason.get("ovr")>39.5 or ratingseason.get("pot")>49.5):
                dictofrelevantratings.update({str(number)+" "+str(p['pid']):ratingseason})
                names.update({p['pid']:p['firstName']+" "+p['lastName']})
            
    array = []
    for index2 in dictofrelevantratings.keys():
        pid = int(index2.split(" ",1)[1])
        rating = dictofrelevantratings.get(index2)
        ovr = max(rating.get("ovr"),50)
        specialscore = 0
        for i in range(0,len(specialratings[index])):
            specialscore = specialscore+rating.get(specialratings[index][i])*weights[index][i]
        specialscore = specialscore/sum(weights[index])-ovr*0.5
        shouldadd = True
        for element in array:
            #print(element)
            if element[0] == pid and element[1] > specialscore:
                shouldadd = False
            
                

        if shouldadd:
            for element in array:
                if element[0] == pid:
                    array.remove(element)
            array.append([pid,specialscore,rating.get("season"), rating.get("ovr"),rating.get("pot"), rating.get("tid"), " ".join(rating.get('skills'))])
    newlist = sorted(array, key = lambda i:i[1], reverse = True)
    if len(newlist) > 20:
        newlist = newlist[0:20]

    
    rank = 1
    for item in newlist:
        name = names[item[0]]
        #print(item)
        if item[5] == None:
            abv = "N/A"
        else:
            for t in export['teams']:
                if t['tid'] == item[5]:
                    abv = t['abbrev']
                    for s in t['seasons']:
                        if s['season'] == item[2]:
                            abv = s['abbrev']
            
        embed.add_field(name=str(rank)+": "+str(item[2])+" "+name,value=str(item[3])+"/"+str(item[4])+", "+item[6]+ ", "+abv)
        rank += 1
    return embed

def standingspredict(embed,commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    if export['gameAttributes']['phase'] == 0:
        embed.add_field(name = "sorry, but", value = "we don't support preseason predictions yet, as team MOV plays a large part into record prediction")
        return embed
    names = []
    wins = []
    losses = []
    gp = []
    rates = []
    mov = []
    ratings = []
    confs = dict()
    abbrevs = dict()
    sos = []
    for t in export['teams']:
        
        for s in t['seasons']:
            if s['season'] == season:
                names.append(s['region']+" "+s['name'])
                confs.update({s['region']+" "+s['name']:t['cid']})
                wins.append(s['won'])
                losses.append(s['lost'])
                rates.append(min(0.999,max(0.001,s['won']/(s['won']+s['lost']))))
                gp.append(s['won']+s['lost'])
                abbrevs.update({s['region']+" "+s['name']:s['abbrev']})
        for s in t['stats']:
            if s['season'] == season and s['playoffs'] == False:
                gp_s = s.get('gp', 0)
                if gp_s <= 0:
                    continue
                mov.append((s['pts']-s['oppPts'])/gp_s)
                sos.append(gsos(export, t['tid']))
        roster = []
        for p in export['players']:

            if p['tid'] == t['tid']:
                roster.append(p['ratings'][-1]['ovr'])
        if len(t['stats']) > 0:
            for s in t['seasons']:
                if s['season'] == season:

                    ratings.append(int(pull_info.team_rating(roster, False)))

    extendmov = []
    extendedrates = []
    for t in export['teams']:
        for s in t['seasons']:
            e = s['season']
            matchexists = False
            for ss in t['stats']:
                if ss['season'] == e:
                    matchexists = True
            if matchexists:
                extendedrates.append(min(0.999,max(0.001,s['won']/(s['won']+s['lost']))))
        for s in t['stats']:
            if s['playoffs'] == False:
                gp_s = s.get('gp', 0)
                if gp_s <= 0:
                    continue
                extendmov.append((s['pts']-s['oppPts'])/gp_s)
        

    logrates = []
    for item in rates:
        logrates.append(np.log(item/(1-item)))
    logextrates = []
    for item in extendedrates:
        logextrates.append(np.log(item/(1-item)))
    logextrates_a = np.array(logextrates)
    extendmov_a = np.array(extendmov).reshape((-1, 1))
    model = LinearRegression()
    model.fit(extendmov_a, logextrates_a)
    

    model2 = LinearRegression()
    ratings_a = np.array(ratings).reshape((-1,1))
    mov_a = np.array(mov)

    model2.fit(ratings_a,mov_a)

    predictedmov = []
    for item in range (0, len(names)):
        predictedmov.append(model2.coef_[0]*ratings[item]+model2.intercept_)

    predictedmovweight = []
    if isinstance(export['gameAttributes']['numGames'],list):
        ng = export['gameAttributes']['numGames'][-1]['value']
    else:
        ng = export['gameAttributes']['numGames']
    for i in range (0, len(names)):
        predictedmovweight.append(0.9-gp[i]/ng*0.6)

    # START THE SIMULATIONS
    pdict= dict()
    for iti in names:
        pdict.update({iti:0})
    random.seed(sum(gp))
    np.random.seed(sum(gp))

    try:
        ep = export['gameAttributes']['numGamesPlayoffSeries'][-1]['value']

    except  Exception:
        ep = export['gameAttributes']['numGamesPlayoffSeries']
    b = export['gameAttributes']['numPlayoffByes']

    if not isinstance(b, int):
        b = b[-1]['value']

    totalplayoffspots = 2**(len(ep))-b
    confsset = set()
    for t in confs:
        confsset.add(confs[t])
    playoffslotsperconf = int(totalplayoffspots/len(confsset))
    playoffsvector = []
    if export['gameAttributes']['playIn']:
        for i in range(0,playoffslotsperconf-2):
            playoffsvector.append(1)

        playoffsvector.append(0.75)
        playoffsvector.append(0.75)
        playoffsvector.append(0.25)
        playoffsvector.append(0.25)
    else:
        for i in range(0,playoffslotsperconf):
            playoffsvector.append(1)
    number = 2500
    for sim in range (0,number):
        
        eststandings = dict()


        for t in range (0, len(names)):
            tname = names[t]
            # first generate ros movs
            ros_mov=predictedmov[t]*predictedmovweight[t]+(1-predictedmovweight[t])*mov[t]+np.random.normal(0,np.sqrt(ng/gp[t])) # a bit of random noise
            s = sos[t]
            ros_wr = model.coef_[0]*ros_mov + model.intercept_-np.log(s/(1-s))
            ros_wr = np.exp(ros_wr)/(1+np.exp(ros_wr))

            remaininggameswin = np.random.binomial(ng-gp[t],ros_wr)
            numwins = wins[t]+remaininggameswin
            eststandings.update({tname:numwins})

        # now for deciding who makes playoffs
        c0members = []
        for t in eststandings.keys():
            if confs[t] == 0:
                c0members.append(t)
        
        c0standings = sorted(c0members, key = lambda x : (1-confs[x])*eststandings[x]+np.random.normal(0,0.0001), reverse = True)
        c1members = []
        for t in eststandings.keys():
            if confs[t] == 1:
                c1members.append(t)
        c1standings = sorted(c1members, key = lambda x : (confs[x])*eststandings[x]+np.random.normal(0,0.0001), reverse = True)

        for x in range (0, min(len(playoffsvector), len(c0standings))):
            
            temp = pdict[c0standings[x]]
            pdict.update({c0standings[x]:playoffsvector[x]+temp})
        for x in range (0, min(len(playoffsvector), len(c1standings))):
            temp = pdict[c1standings[x]]
            pdict.update({c1standings[x]:playoffsvector[x]+temp})

    # final display
    confstandings = [[],[]]
    for t in range(0, len(names)):
        n = names[t]
        ros_mov=predictedmov[t]*predictedmovweight[t]+(1-predictedmovweight[t])*mov[t]
        s = sos[t]
        ros_wr = model.coef_[0]*ros_mov + model.intercept_-np.log(s/(1-s))
        ros_wr = np.exp(ros_wr)/(1+np.exp(ros_wr))
        ros_ew = (ng-gp[t])*ros_wr
        ew = wins[t]+ros_ew
        conf = confs[n]
        confstandings[conf].append((n,rates[t],wins[t],losses[t],ros_mov,ew,pdict[n]/number))
    confstandings[0] = sorted(confstandings[0], key = lambda x : x[1], reverse = True)
    confstandings[1] = sorted(confstandings[1], key = lambda x : x[1], reverse = True)
    
    i = -1
    for c in confstandings:
        i += 1
        s = "Record | Pre. MOV | Pre. Wins | Playoff Prob."+"\n"
        print(export['gameAttributes']['confs'])
        try:
            n = export['gameAttributes']['confs'][i-1]['name']
        except Exception:
            if len(export['gameAttributes']['confs'][-1]['value']) > i:
                
                n = export['gameAttributes']['confs'][-1]['value'][i-1]['name']
                print("n is "+n)
        for t in c:
            temps = s
            s += "**"+abbrevs[t[0]]+"**: "+str(t[2])+"-"+str(t[3])+" | "+str(round(t[4],2))+" | "+str(round(t[5],1))+" | **"+str(round(t[6]*100,2))+"**%\n"
            if len(s) > 1024:
                embed.add_field(name = n, value = temps, inline = False)
                embed.add_field(name = "There were more teams, but they sucked too much, so I won't be including them.", value = "Get better.")
        if len(s) < 1024:
            embed.add_field(name = n, value = s, inline = False)
        
    return embed
            
            
                
                
        
def draftorder(embed, commandInfo):
    dround = "All Rounds"
    for item in commandInfo['message'].content.split(" "):
        if len(item) == 1:
            try:
                dround = int(item)
            except ValueError:
                pass
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    if export['gameAttributes']['phase'] != 5 and export['gameAttributes']['phase'] != 6 and export['gameAttributes']['phase'] != -1:
        embed.add_field(name = "Order! ORDER!", value= "You can't have draft order unless its draft phase")
        return embed
    ls = []
    for p in export['draftPicks']:
        if p['season'] == export['gameAttributes']['season'] or p['season'] == 'fantasy':
            if dround == "All Rounds" or p['round'] == dround:
                if p['pick'] > 0:
                    ls.append(p)
    ls = sorted(ls, key = lambda x:x['round']*100000+x['pick'])
    if len(ls) > 100:
        ls = ls[0:100]
    s = ""
    c = 1
    if len(ls) == 0:
        embed.add_field(name = "Draft Order for round "+str(dround), value= "For some reason, no draft picks for that round were detected in the export. You might want to check with your local lawn inspection agency.")
        return embed
    fround = ls[0]['round']
    s += "---**Round "+str(fround)+"**---\n"
    for p in ls:
        
        s = s + str(p['pick'])+": "+getabbrev(export,p['tid'])
        if p['originalTid'] != p['tid']:
            s = s + ' (from '+getabbrev(export,p['originalTid'])+")"
        s = s + "\n"
        if len(ls) > c:
            if ls[c]['round'] > ls[c-1]['round']:
                s += "---**Round "+str(ls[c]['round'])+"**---\n"
        c += 1
    embed.add_field(name = "Draft Order for round "+str(dround), value=s)
    return embed
    
def mostuniform(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]

    
    timewarp = commandInfo['message'].content.split(" ")
    year = -1000
    listofdevs = []
    if len(timewarp)>1:
        year = int(timewarp[1])
    for p in export['players']:
        rates = p['ratings']
        priorminimum = 1000
        pname = p['firstName'].strip() + " " + p['lastName'].strip()
        for rts in rates:
                
            if year == -1000 or rts.get("season") == year:
                    
                #print(rts)
                ratingslist = ["hgt","dnk","oiq","stre","ins","diq","spd","ft","drb","jmp","pss","fg","endu","tp","reb"]
                ratingslist2 = []
                totdeviation = 0
                tot = 0
                for name in ratingslist:
                    tot += rts.get(name)
                avg = tot/15
                for name in ratingslist:
                    ratingslist2.append(rts.get(name))
                    deviation = rts.get(name)-avg
                    if deviation<0:
                        deviation = -deviation
                    totdeviation += deviation
                szn = rts.get("season")
                if totdeviation<priorminimum:
                    for item1 in listofdevs:
                        if item1[0]==pname:
                            listofdevs.remove(item1)
                    listofdevs.append([pname,totdeviation,szn,avg])
                    priorminimum = totdeviation
                            
                        
                    #print(listofdevs[-1])
        #print(listofdevs)
    title = "Most Average Players: \n"
    string = ""
    tenlargest = sorted(listofdevs, key = lambda i:i[1])[0:10]
    for item in tenlargest:
        string = string+(str(item[2])+" "+item[0]+", Deviation of "+str(round(item[1],2))+" from average of "+str(round(item[3],1))+"\n")
    embed.add_field(name = title, value = string)
    return embed
def stripnames(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    for p in players:
        p.update({'firstName':p['firstName'].strip()})
        p.update({'lastName':p['lastName'].strip()})
    return embed
def pickvalue(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    startseason = export['gameAttributes']['startingSeason']-1
    endseason = export['gameAttributes']['season'] - 10
    if endseason < startseason:
        embed.add_field(name = "Error", value = "Not enough data, play 10 seasons! losers")
        return embed
    pickstats = dict()
    pickratings = dict()
    for p in export['players']:
        r = p['draft']['round']
        pick = p['draft']['pick']
        yr = p['draft']['year']
        if yr >= startseason and yr <= endseason and r > 0:
            s = str(r)+"-"+str(pick)
            total = 0
            for st in p['stats']:
                if not st['playoffs']:
                    total += st['ows']+st['dws']
            maxovr = 0
            for ra in p['ratings']:
                if ra['ovr'] > maxovr:
                    maxovr = ra['ovr']
            if not s in pickstats:
                pickstats.update({s:[]})
            pickstats[s].append(total)
            if not s in pickratings:
                pickratings.update({s:[]})
            pickratings[s].append(maxovr)

    ms = ""
    picks = []
    wss = []
    ratings = []
    for pick in sorted(pickstats, key = lambda i: int(i.split("-")[0])*1000+int(i.split("-")[1])):
        if len(pickstats[pick]) > 9:
            picks.append(pick)
            s = pickstats[pick]
            r = pickratings[pick]
            ratings.append(round(sum(r)/len(r),2))
            wss.append(round(sum(s)/len(s),2))
            ms += pick + " Avg WS: "+str(round(sum(s)/len(s),2))+", Avg Peak Ovr: "+str(round(sum(r)/len(r),2))+"\n"
            if len(ms) > 980:
                embed.add_field(name = "Pick values", value = ms)
                ms = ""
    if len(ms) > 0:
        embed.add_field(name = "Pick values", value = ms)
    df = pandas.DataFrame([wss,ratings], index=['win shares','peak rating'],columns = picks).transpose()
    fig = px.line(df,labels = {"index":"Pick","value":"Peak Rating/WS"}, title = "Pick Value")
    fig.update_layout(

    yaxis=dict( # Here
        range=[0,100] # Here
    ) # Here
    )
    fig.write_image('third_figure.png')
    del fig

    return embed
def reprog(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    
    if export['gameAttributes']['phase'] > 0:
        embed.add_field(name = "It's not preseason", value = "this can only be done in preseason")
        return embed
    f = open("summaries.txt")
    summaries = json.load(f)
    random.seed(export['gameAttributes']['season']) # should give deterministic ish results on reruns with the same variance
    variance = 0
    for item in commandInfo['message'].content.split(" "):
        try:
            variance = abs(float(item)/2)
        except ValueError:
            pass
    if variance > 5:
        variance = 5
    ratingslist = ["stre","jmp","endu","spd","ins","reb","pss","fg","tp","ft","dnk","drb","oiq","diq"]
    for p in export['players']:
        if p['retiredYear'] is None:
            if p['draft']['year'] < export['gameAttributes']['season'] and len(p['ratings']) > 1:
                age = max(min(export['gameAttributes']['season'] - 1 - p['born']['year'],37),19)
                potgap = {18:25,19:20,20:15,21:12,22:9,23:6,24:4,25:2,26:2,27:1,28:1}
                truevar = variance * 5/(age-10) + 0.05
                pvar = np.random.normal(0,np.sqrt(truevar))
                pratings = p['ratings']

                base = pratings[-2]
                current = pratings[-1]
                if p['pid'] == 637:
                    print(current)
                
                sum_age = summaries[str(age)]
                
                for ratings in ratingslist:
                    
                    yboost = 0
                    if age > 27:
                        yboost = 0.375
                    elif age < 29:
                        yboost  = 0.5
                    elif age < 31:
                        yboost = 0.25
                    newr = base[ratings]+float(sum_age[ratings])+yboost+pvar+np.random.normal(0,np.sqrt(truevar))
                    baser = int(newr)
                    frac = newr - baser
                    if random.random() < frac:
                        baser = baser + 1
                    current[ratings] = baser
                compdict = player_commands.calccomp(p, export['gameAttributes']['season'], extra = True)
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
                #print(p['ratings'][-1]['skills'])
                p['ratings'][-1]['skills'] = skillstring
                p['ratings'][-1]['ovr'] = player_commands.ovr(current)
                if age < 18:
                    p['ratings'][-1]['pot'] = min(100,ovr(current) + 30)
                elif age > 28:
                    p['ratings'][-1]['pot'] = min(100,ovr(current))
                else:
                    p['ratings'][-1]['pot'] = min(100,ovr(current) + potgap[age+1])

    embed.add_field(name = "Progs Done with variance "+str(variance*2), value = "go ahead and do -pratings on everyone now.")
    
    return embed
                
                
    

def mostaverage(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    if commandInfo['message'].content.__contains__("mostuniform"):
        return mostuniform(embed, commandInfo)
    
    timewarp = commandInfo['message'].content.split(" ")
    year = -1000
    listofdevs = []
    if len(timewarp)>1:
        year = int(timewarp[1])
    for p in export['players']:
        rates = p['ratings']
        priorminimum = 1000
        pname = p['firstName'].strip() + " " + p['lastName'].strip()
        for rts in rates:
                
            if year == -1000 or rts.get("season") == year:
                    
                #print(rts)
                ratingslist = ["hgt","dnk","oiq","stre","ins","diq","spd","ft","drb","jmp","pss","fg","endu","tp","reb"]
                ratingslist2 = []
                totdeviation = 0
                for name in ratingslist:
                    ratingslist2.append(rts.get(name))
                    deviation = rts.get(name)-50
                    if deviation<0:
                        deviation = -deviation
                    totdeviation += deviation
                szn = rts.get("season")
                if totdeviation<priorminimum:
                    for item1 in listofdevs:
                        if item1[0]==pname:
                            listofdevs.remove(item1)
                    listofdevs.append([pname,totdeviation,szn])
                    priorminimum = totdeviation
                            
                        
                    #print(listofdevs[-1])
        #print(listofdevs)
    title = "Most Average Players: \n"
    string = ""
    tenlargest = sorted(listofdevs, key = lambda i:i[1])[0:10]
    for item in tenlargest:
        string = string+(str(item[2])+" "+item[0]+", Deviation of "+str(item[1])+"\n")
    embed.add_field(name = title, value = string)
    return embed


def mostunbalanced(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    if commandInfo['message'].content.__contains__("mostuniform"):
        return mostuniform(embed, commandInfo)
    
    timewarp = commandInfo['message'].content.split(" ")
    year = -1000
    listofdevs = []
    if len(timewarp)>1:
        year = int(timewarp[1])
    for p in export['players']:
        rates = p['ratings']
        priorminimum = 0
        pname = p['firstName'].strip() + " " + p['lastName'].strip()
        for rts in rates:
                
            if year == -1000 or rts.get("season") == year:
                    
                #print(rts)
                ratingslist = ["hgt","dnk","oiq","stre","ins","diq","spd","ft","drb","jmp","pss","fg","endu","tp","reb"]
                ratingslist2 = []
                totdeviation = 0
                tot = 0
                for name in ratingslist:
                    tot += rts.get(name)
                avg = tot/15
                for name in ratingslist:
                    ratingslist2.append(rts.get(name))
                    deviation = rts.get(name)-avg
                    if deviation<0:
                        deviation = -deviation
                    totdeviation += deviation
                szn = rts.get("season")
                if totdeviation>priorminimum:
                    for item1 in listofdevs:
                        if item1[0]==pname:
                            listofdevs.remove(item1)
                    listofdevs.append([pname,totdeviation,szn,avg])
                    priorminimum = totdeviation
                            
                        
                    #print(listofdevs[-1])
        #print(listofdevs)
    title = "Least Balanced Players: \n"
    string = ""
    tenlargest = sorted(listofdevs, key = lambda i:i[1], reverse = True)[0:10]
    for item in tenlargest:
        string = string+(str(round(item[2],2))+" "+item[0]+", Deviation of "+str(round(item[1],2))+"\n"+" from average of "+str(round(item[3],1))+"\n")
    embed.add_field(name = title, value = string)
    return embed

def playoffs(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    playoffs = export['playoffSeries']
    teams = export['teams']
    tid_dict = dict()
    for t in teams:
        for s in t['seasons']:
            if s['season'] == commandInfo['season']:
                tid_dict.update({t['tid']:s['region']+" "+s['name']})
    found = False
    for p in playoffs:
        if p['season'] == commandInfo['season']:
            found = True
            
            series = p['series']
            for index in range(0, len(series)):
                p_round = series[index]
                s = ""
                for ind_series in p_round:
                    if 'away' in ind_series:
                        print(ind_series)

                        s = s + "("+str(ind_series['home']['seed'])+") "+tid_dict[ind_series['home']['tid']]+" **"+str(ind_series['home']['won'])+"-"+str(ind_series['away']['won'])+"** "+tid_dict[ind_series['away']['tid']]+" ("+str(ind_series['away']['seed'])+") "+"\n"
                      
                nm = "Round "+str(index+1)
                if index == len(series)-1:
                    nm = "Finals"
                print(s)
                embed.add_field(name = nm, value = s, inline = False)
    if not found:
        embed.add_field(name = "Maybe you can run the playoffs in a test sim or something,", value = "Because there sure isn't one in the current export for that season.", inline = False)
    return embed

def _simulate_cola_lottery(eligible, num_picks=4, n_sims=4000):
    """Weighted-without-replacement lottery sim. Returns {tid: [p1, p2, ...]}."""
    import random as _r
    results = {t['tid']: [0]*num_picks for t, _ in eligible}
    for _ in range(n_sims):
        pool = [(t, c) for t, c in eligible]
        for pick_idx in range(num_picks):
            tot = sum(c for _, c in pool)
            if tot <= 0:
                break
            r = _r.random() * tot
            cum = 0
            for i, (t, c) in enumerate(pool):
                cum += c
                if r <= cum:
                    results[t['tid']][pick_idx] += 1
                    pool.pop(i)
                    break
    return {tid: [v / n_sims for v in counts] for tid, counts in results.items()}


_COLA_ALPHA = 1000      # base allocation added per non-playoff season
_COLA_OPT_OUT_PEN = 2000
_PHASE_PLAYOFFS = 3     # BBGM phase enum value; alpha is added when phase <= 3


def cola(embed, commandInfo):
    """COLA lottery standings — only for leagues with draftType='cola'.

    Mirrors ZenGM's lottery-chance logic from
    src/worker/core/draft/genOrder.ts and cola.ts:
      - Lottery pool = non-playoff teams (this season's playoffRoundsWon == -1).
      - If your own first-round pick was traded, effective chances = 0.
      - If your team opted out (colaOptOut), effective chances = 0.
      - Otherwise: banked chances + COLA_ALPHA (alpha added during reg season /
        playoffs since the current year's +1000 isn't baked in until the
        lottery runs). Banked chances live in team.draftLottery.chances.
    """
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    ga = export['gameAttributes']
    if ga.get('draftType') != 'cola':
        embed.add_field(
            name='Not a COLA league',
            value=(
                f"This league uses `{ga.get('draftType', 'unknown')}` draft type. "
                "`-cola` only works on leagues with the COLA (Carry-Over Lottery "
                "Allocation) draft type."
            ),
            inline=False,
        )
        return embed

    teams = export['teams']
    num_picks = ga.get('draftLotteryCustomNumPicks', 4)
    season_now = ga.get('season')
    phase = ga.get('phase', 0)
    add_alpha = _COLA_ALPHA if phase <= _PHASE_PLAYOFFS else 0

    # Build pick-ownership lookup for this season: original_tid → round1 current_tid
    own_r1_currenttid = {}
    for dp in export.get('draftPicks', []) or []:
        if dp.get('season') != season_now or dp.get('round') != 1:
            continue
        otid = dp.get('originalTid')
        if otid is None:
            continue
        own_r1_currenttid[otid] = dp.get('tid')

    # Build the lottery pool: non-playoff teams this season
    pool = []
    for t in teams:
        if t.get('disabled'):
            continue
        made_playoffs = False
        played_this_season = False
        for s in t.get('seasons', []):
            if s.get('season') == season_now:
                played_this_season = True
                if s.get('playoffRoundsWon', -1) >= 0:
                    made_playoffs = True
                break
        if not played_this_season or made_playoffs:
            continue
        own_pick_tid = own_r1_currenttid.get(t['tid'])
        traded_away = (own_pick_tid is not None and own_pick_tid != t['tid'])
        opted_out = bool(t.get('colaOptOut'))
        raw_cola = (t.get('draftLottery') or {}).get('chances', 0)
        if traded_away or opted_out:
            effective = 0
        else:
            effective = raw_cola + add_alpha
        pool.append({
            't': t, 'cola': raw_cola, 'eff': effective,
            'traded': traded_away, 'opted_out': opted_out,
        })

    if not pool:
        embed.add_field(name='No lottery teams', value='No non-playoff teams found for this season.', inline=False)
        return embed

    pool.sort(key=lambda x: (-x['eff'], -x['cola']))

    # User team
    user_tid = None
    teamlist = serversList.get(str(commandInfo['serverId']), {}).get('teamlist', {})
    msg = commandInfo.get('message')
    if msg is not None:
        u = str(getattr(msg.author, 'id', ''))
        if u in teamlist:
            user_tid = teamlist[u]

    eligible_pool = [p for p in pool if p['eff'] > 0]
    ineligible_pool = [p for p in pool if p['eff'] <= 0]
    eligible_for_sim = [(p['t'], p['eff']) for p in eligible_pool]
    sim = _simulate_cola_lottery(eligible_for_sim, num_picks=num_picks) if eligible_for_sim else {}
    total_eff = sum(p['eff'] for p in eligible_pool)

    # Header summary
    embed.add_field(
        name=f'COLA Lottery — {season_now}',
        value=f"{len(eligible_pool)} eligible · {total_eff:,} chances in the pool",
        inline=False,
    )

    # Standings — markdown lines (no code block) so the table reflows
    # on mobile instead of getting trapped behind a horizontal scrollbar.
    rows = []
    for idx, p in enumerate(eligible_pool, start=1):
        t = p['t']
        record = '-'
        for s in t.get('seasons', []):
            if s.get('season') == season_now:
                record = f"{s.get('won', 0)}-{s.get('lost', 0)}"
                break
        probs = sim.get(t['tid'], [0]*num_picks)
        p1 = probs[0] * 100
        ptop = sum(probs) * 100
        share = p['eff'] / max(total_eff, 1) * 100
        star = ' ⭐' if t['tid'] == user_tid else ''
        rows.append(
            f"**{idx}.** `{t['abbrev']}`{star} ({record}) — "
            f"🎟 **{p['eff']:,}** · pool **{share:.1f}%** · #1 **{p1:.1f}%** · Top{num_picks} **{ptop:.1f}%**"
        )

    if rows:
        first = True
        chunk = []
        chunk_len = 0
        for row in rows:
            if chunk_len + len(row) + 1 > 1000:
                embed.add_field(name='Standings' if first else 'Continued',
                                value='\n'.join(chunk), inline=False)
                first = False
                chunk = []
                chunk_len = 0
            chunk.append(row)
            chunk_len += len(row) + 1
        if chunk:
            embed.add_field(name='Standings' if first else 'Continued',
                            value='\n'.join(chunk), inline=False)

    # Ineligible — compact list with reasons
    if ineligible_pool:
        ineligible_lines = []
        for p in ineligible_pool:
            reason = 'pick traded' if p['traded'] else 'opted out' if p['opted_out'] else 'ineligible'
            ineligible_lines.append(f"{p['t']['abbrev']} ({reason}, raw {p['cola']})")
        embed.add_field(
            name=f"Ineligible — {len(ineligible_pool)} team{'s' if len(ineligible_pool) != 1 else ''}",
            value=' · '.join(ineligible_lines),
            inline=False,
        )

    # User team callout
    if user_tid is not None:
        for idx, p in enumerate(pool, start=1):
            if p['t']['tid'] != user_tid:
                continue
            probs = sim.get(user_tid, [0]*num_picks)
            p1 = probs[0] * 100
            ptop = sum(probs) * 100
            if p['traded']:
                value = (
                    f"**Ineligible** — your own first-rounder was traded.\n"
                    f"Raw COLA: **{p['cola']:,}** chances banked for next year."
                )
            elif p['opted_out']:
                value = f"**Ineligible** — opted out of this year's lottery."
            else:
                eligible_rank = next((i for i, ep in enumerate(eligible_pool, start=1) if ep['t']['tid'] == user_tid), idx)
                share = p['eff'] / max(total_eff, 1) * 100
                value = (
                    f"Rank **#{eligible_rank}** of {len(eligible_pool)} · "
                    f"**{p['eff']:,}** chances ({share:.1f}% of pool)\n"
                    f"Pick **#1: {p1:.1f}%** · Top {num_picks}: **{ptop:.1f}%** · "
                    f"Outside top {num_picks}: {(1-sum(probs))*100:.1f}%"
                )
            embed.add_field(name=f"⭐ {p['t']['region']} {p['t']['name']}", value=value, inline=False)
            break

    embed.add_field(
        name='Gaining & Losing Tickets',
        value=(
            "**Gain 📈**\n"
            f"• Miss the playoffs → **+{_COLA_ALPHA:,}** tickets, banked into the pool.\n"
            "• Tickets **roll over** every year you stay in the lottery — they pile up the longer you're down.\n"
            "\n"
            "**Burn 🔥**\n"
            "• Win the lottery → your tickets burn: the **#1 pick wipes them all**, picks **#2–4 burn a smaller share**.\n"
            "• Playoff success burns tickets too — the deeper the run, the more you lose.\n"
            "\n"
            "**Ineligible this year 🚫** (tickets still bank for next year)\n"
            "• Trade away your own first-round pick.\n"
            "• Opt out of the lottery."
        ),
        inline=False,
    )

    embed.add_field(
        name='What is COLA?',
        value=(
            "**Carry-Over Lottery Allocation.** Your draft-lottery odds come from "
            "tickets you bank over time, not just this year's record — so the longer "
            "you stay bad and out of the playoffs, the better your shot at the #1 pick."
        ),
        inline=False,
    )
    return embed


def standings(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    teams = export['teams']
    season = commandInfo['season']
    print(season)
    confs = dict()
    exportconfs = export['gameAttributes']['confs']
    
    if 'start' in exportconfs[0]:
        old = None
        for c in exportconfs:
            if isinstance(c['start'],int):
                if c['start'] > season:
                    exportconfs = old['value']
                    break
            old = c
        if exportconfs == export['gameAttributes']['confs']:
            exportconfs = old['value']
        
    print(exportconfs)
    for t in teams:
        for s in t['seasons']:
            if s['season'] == season:
                
                if not exportconfs[s['cid']]['name'] in confs:
                    confs.update({exportconfs[s['cid']]['name']:[]})
                i = confs[exportconfs[s['cid']]['name']]
                if 'clinchedPlayoffs' in s:
                    p = s['clinchedPlayoffs']
                else:
                    p = ""
                
                i.append((t['region']+" "+t['name'],s['won'],s['lost'],p))
                confs.update({exportconfs[s['cid']]['name']:i})
    for i in confs:
        teams = sorted(confs[i], key = lambda p:p[1]/(max(p[1]+p[2],0.00001)), reverse = True)
        string = ""
        for t in teams:
            string +=t[0]+": "+str(t[1])+"-"+str(t[2])+" "+t[3]+ "\n"
        embed.add_field(name = i, value = string)

    return embed
                    
def po(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    serverSettings = serversList[str(commandInfo['serverId'])]
    if "PO" in serverSettings:
        text = ""
        todelete = []
        l = serverSettings["PO"]
        print(l)
        for i in l:

            name = "who's this, idk. "+str(i)
            teamname = None
            for p in export['players']:
                if p['pid'] == int(i):

                    name = '**'+p['firstName']+" "+p['lastName']+"**"
                    contract = str(p['contract']['amount']/1000)
                    team = p['tid']
                    if team < 0:
                        if team == -1:
                            if 'negotiations' in export:
                                for neg in export['negotiations']:

                                    if neg['pid'] == int(i):
                                        team = neg['tid']


                    ovr = p['ratings'][-1]['ovr']
                    pot = p['ratings'][-1]['pot']
                    
                    for t in export['teams']:

                        if t['tid'] == team:
                            teamname = t['abbrev']
            if teamname == None:
                todelete.append(i)
                    
            
            text += str(name) +", "+str(ovr)+"/"+str(pot)+", "+str(teamname)+ ", $"+str(l[i][0])+"M until "+str(l[i][1])+"\n"
            if len(text) > 970:
                embed.add_field(name = "POs", value = text[0:1023])
                text = ""
        for i in todelete:
            del serverSettings["PO"][i]

        embed.add_field(name = "POs", value = text[0:1023])
        return embed
    else:
        embed.add_field(name = "What in the world!!!!!", value = "There's no POs in existence here. This is barren territory.")
                
def to(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    serverSettings = serversList[str(commandInfo['serverId'])]
    if "TO" in serverSettings:
        text = ""
        todelete = []
        l = serverSettings["TO"]
        print(l)
        for i in l:

            name = "who's this, idk. "+str(i)
            teamname = None
            for p in export['players']:
                if p['pid'] == int(i):

                    name = '**'+p['firstName']+" "+p['lastName']+"**"
                    contract = str(p['contract']['amount']/1000)
                    team = p['tid']
                    if team < 0:
                        if team == -1:
                            if 'negotiations' in export:
                                for neg in export['negotiations']:

                                    if neg['pid'] == int(i):
                                        team = neg['tid']



                    ovr = p['ratings'][-1]['ovr']
                    pot = p['ratings'][-1]['pot']
                    
                    for t in export['teams']:

                        if t['tid'] == team:
                            teamname = t['abbrev']
            if teamname == None:
                todelete.append(i)
                    
            
            text += str(name) +", "+str(ovr)+"/"+str(pot)+", "+str(teamname)+ ", $"+str(l[i][0])+"M until "+str(l[i][1])+"\n"
            if len(t) > 1000:
                embed.add_field(name = "TOs", value = text)
                text = ""
        for i in todelete:
            del serverSettings["TO"][i]
        print(todelete)
        embed.add_field(name = "TOs", value = text)
        return embed
    else:
        embed.add_field(name = "What in the world!!!!!", value = "There's no TOs in existence here. This is barren territory.")
                
    
def fa(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    sortBy = 'ovr'
    values = ['ovr', 'pot', 'hgt', 'stre', 'spd', 'jmp', 'endu', 'ins', 'dnk', 'ft', 'fg', 'tp', 'oiq', 'diq', 'drb', 'pss', 'reb']
    if len(commandInfo['text']) > 1:
        if str.lower(commandInfo['text'][1]) in values:
            sortBy = commandInfo['text'][1]
    freeAgents = []
    for p in players:
        if p['tid'] == -1:
            playerInfo = pull_info.pinfo(p)
            freeAgents.append(playerInfo)
    commandContent = basics.player_list_embed(freeAgents, commandInfo['pageNumber'], export['gameAttributes']['season'], sortBy)
    
    embed.add_field(name=f"Sorted by {commandContent[1]}", value=commandContent[0])
    return embed
def topall(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    t = commandInfo['message'].content.split(" ")
    pagenumber = 1
    for item in t:
        try:
            pagenumber = int(item)
        except:
            pass
    datatype = "rating"
    for item in t:
        if item.lower() == "stat" or item.lower() in ["points","assists", "rebounds","threes","minutes","turnovers","blocks","steals","double"]:
            datatype = "stat"
        if item.lower() == "awards":
            datatype = "award"
    correctawards = ["MVP","All League","First Team","Second Team","Third Team","All Defensive","First Team All Defensive","Second Team All Defensive","Third Team All Defensive", "Sixth Man","Most Improved",
                         "All Star","Rookie of the Year","All Rookie","Defensive Player of the Year","Finals MVP","Semifinals MVP","Won Championship","Scoring Leader","Assists Leader","Rebounds Leader","Steals Leader","Blocks Leader","Biggest Booty"]
    for item in correctawards:
        
        if item.lower() in commandInfo['message'].content.lower():
            datatype = "award"
    if datatype == "rating":
        types = ["pot","endu","tp","reb","pss","fg","jmp","spd","ft","drb","diq","oiq","dnk","ins","hgt","stre"]
        indicate = "ovr"
        for item in t:
            print(item)
            if item.lower() in types:
                indicate = item.lower()
        plist = []
        for p in players:
            peak = 0
            for r in p['ratings']:
                val = r[indicate]
                if val > peak:
                    peak = val
            plist.append((p['firstName']+" "+p['lastName'],peak))
    if datatype == "stat":
        pergame = False
        playoffs = False
        if commandInfo['message'].content.lower().__contains__("per game"):
            pergame = True
        if commandInfo['message'].content.lower().__contains__("playoffs"):
            playoffs = True
        indicate = "points"
        for item in t:
            print(item)
            if item.lower() in ["assists", "rebounds","threes","turnovers","blocks","steals", "minutes"]:
                indicate = item.lower()
        if "triple double" in commandInfo['message'].content.lower():
            indicate = "triple double"
        plist = []
        for player in players:
            total = 0
            gp = 0
            for s in player['stats']:
                if s['playoffs'] == playoffs:
                    gp += s['gp']
                    if indicate == "points":
                        total += s.get("pts", 0)
                    if indicate == "minutes":
                        total = round(total + s.get('min', 0), 1)

                    if indicate == "rebounds":
                        total += s.get("orb", 0) + s.get("drb", 0)
                    if indicate == "assists":
                        total += s.get("ast", 0)
                    if indicate == "blocks":
                        blk = s.get("blk", 0)
                        if isinstance(blk, int):
                            total += blk
                    if indicate == "triple double" or indicate == "triple doubles":
                        td = s.get("td", 0)
                        if isinstance(td, int):
                            total += td
                    if indicate == "steals":
                        stl = s.get("stl", 0)
                        if isinstance(stl, int):
                            total += stl
                    if indicate == "threes":
                        total += s.get("tp", 0)
                    if indicate == "turnovers":
                        total += s.get("tov", 0)
            if pergame:
                if gp > 0:
                    total = round(total / gp, 2)
            if total > 0:
                plist.append((player['firstName']+" "+player['lastName'],total))
    if datatype == "award":
        plist = []
        indicate = "Error"
        for item in correctawards:
            if item.lower().replace(" ","") in commandInfo['message'].content.lower().replace(" ",""):
                indicate = item
        if indicate == "First Team" or indicate == "Second Team" or indicate == "Third Team":
            indicate = indicate + " All League"
        if indicate == "MVP":
            indicate = "Most Valuable Player"
        if indicate == "Error":
            embed.add_field(name = "Please specify exactly one of the following: ",value = ",".join(correctawards))
            return embed
        for player in players:
            a = player['awards']
            t = 0
            for award in a:
                if award["type"].replace("-"," ").lower().__contains__(indicate.lower()):
                    t += 1
                if indicate == "Biggest Booty":
                    if "All-Star MVP" in award["type"]:
                         t = 1
                    if "Slam Dunk" in award["type"]:
                        t += 1
                    if "Three Point" in award["type"]:
                        t += 1
                
            if t > 0:
                plist.append((player['firstName']+" "+player['lastName'],t))
            
                
                        
        
    plist = sorted(plist, key = lambda i:i[1], reverse = True)
    t = ""
    totalpages = int((len(plist)-1)/15)+1
    pagenumber = min(pagenumber, totalpages)
    ccc = 0
    for i in plist[(pagenumber-1)*15:pagenumber*15]:
        t +=str(pagenumber*15-14+ccc)+": "+ i[0]+": "+str(i[1])+"\n"
        ccc += 1
    embed.add_field(name="Best of all time for "+datatype+" "+str(indicate)+", page "+str(pagenumber)+" out of "+str(totalpages), value=t)
    return embed
def draft(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = export['gameAttributes']['season']
    players = export['players']
    sortBy = ['draftRound']
    values = ['ovr', 'pot', 'hgt', 'stre', 'spd', 'jmp', 'endu', 'ins', 'dnk', 'ft', 'fg', 'tp', 'oiq', 'diq', 'drb', 'pss', 'reb']
    if len(commandInfo['text']) > 1:
        if str.lower(commandInfo['text'][1]) in values:
            sortBy = commandInfo['text'][1]
    draftProspects = []
    for p in players:
        if commandInfo['season'] < season:
            if p['draft']['year'] == commandInfo['season'] and p['draft']['round'] != 0:
                playerInfo = pull_info.pinfo(p)
                draftProspects.append(playerInfo)
                draftProspects.sort(key=lambda p: p['draftPick'])
        else:
            if p['draft']['year'] == commandInfo['season'] and p['tid'] == -2:
                playerInfo = pull_info.pinfo(p)
                draftProspects.append(playerInfo)
                if sortBy == ['draftRound']:
                    sortBy = ['value']
    
    if sortBy == ['draftRound']:
        commandContent = basics.player_list_embed(draftProspects, commandInfo['pageNumber'], export['gameAttributes']['season'], sortBy, False, True)
    else:
        commandContent = basics.player_list_embed(draftProspects, commandInfo['pageNumber'], export['gameAttributes']['season'], sortBy)
    embed.add_field(name=f"Sorted by {commandContent[1]}", value=commandContent[0])
    return embed
    
def pr(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = export['gameAttributes']['season']

    powerRanking = []

    for t in teams:
        roster = []
        for p in players:
            if commandInfo['season'] == season:
                if p['tid'] == t['tid']:
                    roster.append(p['ratings'][-1]['ovr'])
            else:
                if 'stats' in p:
                    stats = p['stats']
                    lastTeam = -1
                    for s in stats:
                        if s['season'] == commandInfo['season']:
                            lastTeam = s['tid']
                    if lastTeam == t['tid']:
                        roster.append(pull_info.pinfo(p, commandInfo['season'])['ovr'])
        teamInfo = pull_info.tinfo(t, commandInfo['season'])
        powerRanking.append([teamInfo['name'], teamInfo['record'], pull_info.team_rating(roster, False)])
    
    powerRanking.sort(key=lambda p: float(p[2]), reverse=True)
    lines = []
    number = 1
    for p in powerRanking:
        lines.append(f"``{number}.`` **{p[0]}** ({p[1]}) - **{p[2]}/100** TR")
        number += 1
    # Chunk by characters (Discord caps field value at 1024 and total embed at 6000).
    chunk = []
    chunk_len = 0
    total_chars = 0
    truncated = False
    for line in lines:
        if chunk_len + len(line) + 1 > 1000:
            value = '\n'.join(chunk)
            if total_chars + len(value) > 5500:
                truncated = True
                break
            embed.add_field(name="Power Rankings", value=value, inline=False)
            total_chars += len(value)
            chunk = []
            chunk_len = 0
        chunk.append(line)
        chunk_len += len(line) + 1
    if chunk and not truncated:
        value = '\n'.join(chunk)
        if total_chars + len(value) <= 5500:
            embed.add_field(name="Power Rankings", value=value, inline=False)
        else:
            truncated = True
    if truncated:
        embed.add_field(name='…', value='Power rankings truncated to fit in one message.', inline=False)
    return embed
def leaguesynergy(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = commandInfo['season']

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

    results = []
    for t in teams:
        if t.get('disabled'):
            continue
        roster = [p for p in players if p['tid'] == t['tid']]
        if len(roster) < 5:
            continue
        if all(p.get('rosterOrder', 9999) == 9999 for p in roster):
            roster.sort(key=lambda p: p['ratings'][-1]['ovr'] if p.get('ratings') else 0, reverse=True)
        else:
            roster.sort(key=lambda p: p.get('rosterOrder', 9999))
        top5 = roster[:5]
        d = player_commands.lineupsynergycalc(top5, season)
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
        ti = pull_info.tinfo(t)
        teamOvrs = [p['ratings'][-1]['ovr'] for p in roster if p.get('ratings')]
        tr = pull_info.team_rating(list(teamOvrs), False)
        results.append((score, d, ti['abbrev'], ti['name'], tr))

    if not results:
        embed.add_field(name='Error', value='No teams had a valid 5-player lineup to evaluate.')
        return embed

    results.sort(key=lambda x: x[0], reverse=True)

    lines = []
    for rank, (score, d, abbrev, name, tr) in enumerate(results, 1):
        lines.append(
            f"``{rank}.`` **{abbrev}** — {round(score, 3)} {sort_label} | TR {tr} "
            f"(O {round(d['O'], 3)} | D {round(d['D'], 3)} | R {round(d['Rs'], 3)})"
        )

    chunk = []
    chunk_len = 0
    field_idx = 0
    for line in lines:
        if chunk_len + len(line) + 1 > 1000:
            embed.add_field(name=f"League Synergy ({sort_label})" if field_idx == 0 else "Continued",
                            value='\n'.join(chunk), inline=False)
            chunk = []
            chunk_len = 0
            field_idx += 1
        chunk.append(line)
        chunk_len += len(line) + 1
    if chunk:
        embed.add_field(name=f"League Synergy ({sort_label})" if field_idx == 0 else "Continued",
                        value='\n'.join(chunk), inline=False)

    embed.add_field(
        name='What is Synergy?',
        value=("Each team's starting 5 (by lineup order, OVR fallback) is scored. "
               "**O** max 1.25, **D** max 0.833, **R** max 0.5. "
               "Sort with `off`/`def`/`reb` (e.g. `-leaguesynergy off`)."),
        inline=False
    )
    return embed
def leaguebuilds(embed, commandInfo):
    import player_builds
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    counts = player_builds.count_league_builds(players)
    if not counts:
        embed.add_field(name='Error', value='No classifiable builds found.', inline=False)
        return embed
    total = sum(counts.values())
    sorted_desc = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    chunks, cur, cur_len = [], [], 0
    for tag, c in sorted_desc:
        line = f"``{c:>3}`` {tag} · {c/total*100:.1f}%"
        if cur_len + len(line) + 1 > 950:
            chunks.append('\n'.join(cur))
            cur, cur_len = [], 0
        cur.append(line)
        cur_len += len(line) + 1
    if cur:
        chunks.append('\n'.join(cur))
    for idx, chunk in enumerate(chunks):
        name = 'Build Distribution' if idx == 0 else 'Build Distribution (cont.)'
        embed.add_field(name=name, value=chunk, inline=False)

    embed.add_field(
        name='Summary',
        value=f"{total} active players · {len(counts)} distinct builds",
        inline=False
    )
    return embed


def lgoptions(embed, commandInfo):
    listofthings2 = 'gp, min, fg, fga, fgAtRim, fgaAtRim, fgLowPost, fgaLowPost, fgMidRange, fgaMidRange, tp, tpa, ft, fta, orb, drb, ast, tov, stl, blk, pf, pts, dd, td, qd, fxf, oppFg, oppFga, oppFgAtRim, oppFgaAtRim, oppFgLowPost, oppFgaLowPost, oppFgMidRange, oppFgaMidRange, oppTp, oppTpa, oppFt, oppFta, oppOrb, oppDrb, oppAst, oppTov, oppStl, oppBlk, oppPf, oppPts, oppDd, oppTd, oppQd, oppFxf, rid, reb, wins, losses, win%, oppReb, ptsPerGame, oppPtsPerGame, rebPerGame, oppRebPerGame, astPerGame, oppAstPerGame, blkPerGame, oppBlkPerGame, stlPerGame, oppStlPerGame, tovPerGame, oppTovPerGame, pfPerGame, oppPfPerGame, fgPerGame, oppFgPerGame, tpPerGame, oppTpPerGame, ftPerGame, oppFtPerGame, tp%, oppTp%, ft%, oppFt%, fg%, oppFg%, fgAtRim%, oppFgAtRim%, fgLowPost%, oppFgLowPost%, fgMidRange%, oppFgMidRange%, ptdiff'
    embed.add_field(name = "Stats options", value = listofthings2)
    return embed
def leaguegraph(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    message = commandInfo['message']
    listofthings2 = 'gp, min, fg, fga, fgAtRim, fgaAtRim, fgLowPost, fgaLowPost, fgMidRange, fgaMidRange, tp, tpa, ft, fta, orb, drb, ast, tov, stl, blk, pf, pts, dd, td, qd, fxf, oppFg, oppFga, oppFgAtRim, oppFgaAtRim, oppFgLowPost, oppFgaLowPost, oppFgMidRange, oppFgaMidRange, oppTp, oppTpa, oppFt, oppFta, oppOrb, oppDrb, oppAst, oppTov, oppStl, oppBlk, oppPf, oppPts, oppDd, oppTd, oppQd, oppFxf, rid, reb, wins, losses, win%, oppReb, ptsPerGame, oppPtsPerGame, rebPerGame, oppRebPerGame, astPerGame, oppAstPerGame, blkPerGame, oppBlkPerGame, stlPerGame, oppStlPerGame, tovPerGame, oppTovPerGame, pfPerGame, oppPfPerGame, fgPerGame, oppFgPerGame, tpPerGame, oppTpPerGame, ftPerGame, oppFtPerGame, tp%, oppTp%, ft%, oppFt%, fg%, oppFg%, fgAtRim%, oppFgAtRim%, fgLowPost%, oppFgLowPost%, fgMidRange%, oppFgMidRange%, ptdiff'
    prefix = serversList[str(message.guild.id)]['prefix']
    if True:
        
        m=message.content.replace(prefix+'leaguegraph',"").strip()
        try:
            yr = int(message.content.split(" ")[-1])
            m=m.replace(str(yr),"").strip()
        except ValueError:
            yr = export['gameAttributes']['season']
        firststatname = "ptdiff"
        secondstatname = "win%"
        assigned = False
        secondisassigned = False
        poff = False

        t = m.split(" ")
        for item in t:
            if len(item)>1:
                if not assigned:
                    firststatname = item
                    assigned = True
                else:
                    if not secondisassigned:
                        secondstatname = item
                        secondisassigned = True


        teams = export['teams']
        seasons = list()
        stats= list()
        colors = list()
        firststat=list()
        secondstat=list()
        finalcolors = list()
        tcolors = ["#F63309","#09F621","#090FF6","#F68509","#F3F609","#09c3ba","#601A83","#83221A","#835B1A","#b1d5fb","#BB22B5","#FF13CD","#6891f8","#fcc5f4","#1d6b05","#878787","#787878","#A36B41","#87B5FF","#F5BFBD","#4E1B4B","#76190F","#41203E","#0A144A"]
        sizes=list()
        names=list()
        for t in teams:
            for season in t.get("seasons"):
                if season.get("season")==yr:
                    seasons.append(season)
                    
            for season in t.get("stats"):
                if season.get("season")==yr and not season.get("playoffs"):
                    stats.append(season)
                    colors.append(t.get("colors")[0])
        #print(seasons)
        for index in range (0,len(stats)):
            st = stats[index]
            tid = stats[index].get("tid")
            for season in teams[tid]['seasons']:
                if season['season'] == yr:
                    name = season['region']+" "+season['name']
            #print(tid)
            names.append(name)
            s = dict()
            for ss in seasons:
                if ss.get("tid")==tid:
                    s = ss
            #print(s)
            st.update({"reb":st.get("orb")+st.get("drb")})
            st.update({"wins":s.get("won")})
            st.update({"losses":s.get("lost")})
            st.update({"win%":s.get("won")/st.get("gp")})
            #print(firststatname,secondstatname)
            st.update({"oppReb":st.get("oppOrb")+st.get("oppDrb")})
            for rating in ["pts","reb","ast","blk","stl","tov","pf","fg","tp","ft"]:
                st.update({rating+"PerGame":st.get(rating)/st.get("gp")})
                rating = rating.capitalize()
                st.update({"opp"+rating+"PerGame":st.get("opp"+rating)/st.get("gp")})
            for rating in ["tp","ft", "fg","fgAtRim","fgLowPost","fgMidRange"]:
                st.update({rating+"%":st.get(rating)/st.get(rating[0:2]+"a"+rating[2:])})
                rating = rating[0:2].capitalize()+rating[2:]
                #print(rating)
                st.update({"opp"+rating+"%":st.get("opp"+rating)/st.get("opp"+rating[0:2]+"a"+rating[2:])})
            st.update({"ptdiff":(st.get("ptsPerGame")-st.get("oppPtsPerGame"))})
            if not (st.__contains__(firststatname) and st.__contains__(secondstatname)):
                t22 = ""
  
                t22 += "Something about the two variables you specified is invalid.\n"
                t22 += "To help you out: what we received from you was: "+firststatname+" and "+secondstatname+"\n"
                embed.add_field(name = "Error", value = t22)
                return embed
            firststat.append(st.get(firststatname))
            secondstat.append(st.get(secondstatname))
            sizes.append(4)
            #print(st.keys())
            finalcolors.append(teams[tid].get("colors")[0])
        #print(firststat)
        fig = px.scatter(x=firststat, y=secondstat,color=names,size = sizes, size_max = 10, color_discrete_sequence = finalcolors[0:len(secondstat)])
        fig.update_layout(
        title='The league in year '+str(yr),
        xaxis=dict(
            title=firststatname,

        ),
        yaxis=dict(
            title=secondstatname,
        ))
        #fig.show()
        fig.write_image('third_figure.png',height=750, width = 790)
        del fig

        t22 = ""
        t22 += "Call "+prefix+"lgoptions to see options"
        embed.add_field(name = "Behold the worst graph you will ever see!", value = t22)
        return embed


def top(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    sortBy = 'ovr'
    if len(commandInfo['text']) > 1:
        sortBy = commandInfo['text'][1]

    pos = ""

    if len(commandInfo['text']) > 1:
        if commandInfo['text'][1].upper() in ['PG','G','GF','SG','SF','PF','F','FC','C']:
            pos = commandInfo['text'][1].upper()
        elif len(commandInfo['text']) > 2 and commandInfo['text'][2].upper() in ['PG','G','GF','SG','SF','PF','F','FC','C']:
            pos = commandInfo['text'][2].upper()
    activePlayers = []
    for p in players:
        if p['tid'] > -2:
            if pos in p['ratings'][-1]['pos']:
                playerInfo = pull_info.pinfo(p)
                activePlayers.append(playerInfo)
    if 'bottom' in commandInfo['message'].content.split(" ")[0]:
        totalPages, remainder = divmod(len(activePlayers), 12)
        totalPages += 1
        commandInfo['pageNumber'] = totalPages + 1 - commandInfo['pageNumber']
    commandContent = basics.player_list_embed(activePlayers, commandInfo['pageNumber'], export['gameAttributes']['season'], sortBy)
    
    embed.add_field(name=f"Sorted by {commandContent[1]}", value=commandContent[0])
    return embed

def injuries(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']

    injuries = []
    for p in players:
        if p['injury']['type'] != 'Healthy':
            injuries.append([f"{p['ratings'][-1]['pos']} **{p['firstName']} {p['lastName']}** ({p['ratings'][-1]['ovr']}/{ p['ratings'][-1]['pot']})", p['ratings'][-1]['ovr']+p['injury']['gamesRemaining'], p['injury']])
    injuries.sort(key=lambda i: i[1], reverse=True)
    lines = []
    for i in injuries:
        lines.append(f"{i[0]} - {i[2]['type']}, {i[2]['gamesRemaining']} games")
    numDivs, rem = divmod(len(lines), 15)
    numDivs += 1
    for i in range(numDivs):
        newLines = lines[(i*15):((i*15)+15)]
        text ='\n'.join(newLines)
        embed.add_field(name=f"Injuries", value=text, inline=False)
    
    return embed


def deaths(embed, commandInfo):
    cont = commandInfo['message'].content.split(' ')
    deathInfo = ['deathInfo', 'yearDied']
    if len(cont) > 1:
        if str.lower(cont[1]) in ['age', 'oldest']:
            deathInfo = ['deathInfo', 'ageDied']

    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    deadPlayers = []
    for p in players:
        p = pull_info.pinfo(p)
        if p['deathInfo']['died']:
            deadPlayers.append(p)
    deadPlayers.sort(key=lambda p: p['deathInfo']['yearDied'], reverse=True)
    commandContent = basics.player_list_embed(deadPlayers, commandInfo['pageNumber'], export['gameAttributes']['season'], deathInfo)
    
    embed.add_field(name=f"Sorted by {commandContent[1]}", value=commandContent[0])
    return embed

def leaders(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    statTypes = ['pts', 'reb', 'drb', 'orb', 'ast', 'stl', 'blk', 'tov', 'min', 'tov', 'pm', 'gp', 'ows', 'dws', 'ortg', 'drtg', 'pm100', 'onOff100', 'vorp', 'obpm', 'dbpm', 'ewa', 'per', 'usgp', 'dd', 'td', 'qd', 'fxf', 'fg%', 'tp%', 'ft%', 'at-rim%', 'low-post%', 'mid-range%']
    sortBy = ['stats', 'pts']
    if len(commandInfo['text']) > 1:
        if commandInfo['text'][1] in statTypes:
            sortBy = ['stats', str.lower(commandInfo['text'][1]).replace('%', '')]
        else:
            text = "These stats are supported: " + '\n' + '\n'
            for s in statTypes:
                text += f"• ``{s}``" + '\n'
            embed.add_field(name='Error', value=text)
            return embed
    playerList = []
    for p in players:
        played = False
        stats = p['stats']
        for s in stats:
            if s['season'] == commandInfo['season']:
                if s['gp'] > 0:
                    played = True
        if played:
            playerInfo = pull_info.pinfo(p, commandInfo['season'])
            playerList.append(playerInfo)
    commandContent = basics.player_list_embed(playerList, commandInfo['pageNumber'], commandInfo['season'], sortBy)
    
    embed.add_field(name=f"Sorted by {commandContent[1]}", value=commandContent[0])
    return embed

def combine(embed, commandInfo):
    import player_commands
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    # stat key -> (label, lower-is-better)
    statTypes = {
        'height': ('Height (no shoes)', False),
        'wingspan': ('Wingspan', False),
        'reach': ('Standing reach', False),
        'weight': ('Weight', False),
        'fat': ('Body fat', True),
        'lane': ('Lane agility', True),
        'sprint': ('3/4 sprint', True),
        'vert': ('Max vertical', False),
        'bench': ('Bench press (185 lbs)', False),
        'wonderlic': ('Wonderlic', False),
    }
    tokens = [str.lower(t) for t in commandInfo['text'][1:]]
    allTime = str.lower(commandInfo['text'][0]) == 'combineall' or 'all' in tokens
    statArgs = [t for t in tokens if t != 'all']
    if not statArgs or statArgs[0] not in statTypes:
        text = "Pick a stat, e.g. ``-combine vert`` for this year's class or ``-combineall vert`` for all-time records:" + '\n'
        for s, (label, _) in statTypes.items():
            text += f"• ``{s}`` — {label}" + '\n'
        embed.add_field(name='Combine Records', value=text)
        return embed
    stat = statArgs[0]
    rows = []
    for p in players:
        if not p.get('ratings'):
            continue
        if not allTime and p['draft']['year'] != commandInfo['season']:
            continue
        # Combine is a pre-draft event: always use the draft-year ratings row.
        # If the export was created mid-career, the earliest row isn't the
        # rookie year — no real combine data exists for that player, skip him.
        if p['ratings'][0].get('season') != p['draft']['year']:
            continue
        c = player_commands.combine_numbers(p, p['ratings'][0])
        if c:
            rows.append((c[stat], p))
    label, ascending = statTypes[stat]
    rows.sort(key=lambda x: x[0], reverse=not ascending)
    lines = []
    for i, (val, p) in enumerate(rows[:10], 1):
        if stat in ('height', 'wingspan', 'reach'):
            v = player_commands._feet_inches(val)
        elif stat in ('lane', 'sprint'):
            v = f"{val:.2f}s"
        elif stat == 'vert':
            v = f"{round(val * 2) / 2:g}\""
        elif stat == 'bench':
            v = f"{val} reps"
        elif stat == 'wonderlic':
            v = f"{val}"
        elif stat == 'fat':
            v = f"{val:.1f}%"
        else:
            v = f"{val:.1f} lbs"
        lines.append(f"{i}. **{p['firstName']} {p['lastName']}** — {v} ({p['draft']['year']})")
    value = '\n'.join(lines) if lines else 'No players found.'
    title = f"All-Time Combine Records — {label}" if allTime else f"{commandInfo['season']} Draft Combine — {label}"
    embed.add_field(name=title, value=value, inline=False)
    return embed

def _add_blocks(embed, blocks, firstName='Players'):
    """Add lines as fields, chunked under Discord's 1024 cap."""
    name = firstName
    chunk = ''
    for b in blocks:
        if chunk and len(chunk) + len(b) + 1 > 1000:
            embed.add_field(name=name, value=chunk, inline=False)
            chunk = ''
            name = '​'
        chunk += b + '\n'
    if chunk:
        embed.add_field(name=name, value=chunk, inline=False)

def _find_team_by_name(export, query):
    """Match a team by abbreviation, then by region/name substring."""
    q = query.strip().lower()
    if not q:
        return None
    teams = export['teams']
    for t in teams:
        if t['abbrev'].lower() == q:
            return t
    for t in teams:
        full = (t['region'] + ' ' + t['name']).lower()
        if q in full or q in t['name'].lower() or q in t['region'].lower():
            return t
    return None

def retired(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']

    # Optional team filter: -retired [team] limits to players who ever played there.
    # Drop pure-numeric tokens — those are the page number (the router captures it
    # in commandInfo['pageNumber'] but doesn't strip it from text).
    teamQuery = ' '.join(tok for tok in commandInfo['text'][1:] if not tok.isdigit()).strip()
    teamTid = None
    teamLabel = None
    if teamQuery:
        teamObj = _find_team_by_name(export, teamQuery)
        if teamObj is None:
            embed.add_field(name='Team not found',
                            value=f"Couldn't find a team matching `{teamQuery}`.")
            return embed
        teamTid = teamObj['tid']
        teamLabel = teamObj['region'] + ' ' + teamObj['name']

    retiredPlayers = []
    for p in players:
        if p.get('retiredYear') is None:
            continue
        if teamTid is not None:
            if not any(s.get('tid') == teamTid and s.get('gp', 0) > 0 for s in p['stats']):
                continue
        # highest rating they ever reached
        peakOvr = -1
        peakSeason = None
        for r in p['ratings']:
            if r['ovr'] > peakOvr:
                peakOvr = r['ovr']
                peakSeason = r['season']
        if peakOvr < 0:
            continue
        retiredPlayers.append({
            'name': p['firstName'] + ' ' + p['lastName'],
            'retiredYear': p['retiredYear'],
            'peakOvr': peakOvr,
            'peakSeason': peakSeason,
        })

    if not retiredPlayers:
        msg = 'No players have retired in this league yet.'
        if teamTid is not None:
            msg = f"No retired players have played for the {teamLabel}."
        embed.add_field(name='No retired players', value=msg)
        return embed

    # most recently retired first; break ties by who was better at their peak
    retiredPlayers.sort(key=lambda r: (r['retiredYear'], r['peakOvr']), reverse=True)
    perPage = 20
    totalPages = (len(retiredPlayers) + perPage - 1) // perPage
    page = commandInfo['pageNumber']
    if page < 1:
        page = 1
    if page > totalPages:
        page = totalPages
    pageRows = retiredPlayers[(page - 1) * perPage: page * perPage]

    embed.title = 'Retired Players'
    embed.description = 'Most recently retired'
    if teamLabel:
        embed.description += f" · {teamLabel}"
    blocks = []
    rank = (page - 1) * perPage + 1
    for r in pageRows:
        peakStr = f"{r['peakOvr']} OVR" + (f" ({r['peakSeason']})" if r['peakSeason'] else "")
        blocks.append(f"`{rank}.` **{r['name']}** · retired {r['retiredYear']} · peaked {peakStr}")
        rank += 1
    _add_blocks(embed, blocks)
    embed.add_field(name='​', value=f"*Page {page} of {totalPages}*", inline=False)
    return embed

BADGE_NAMES = {
    'tp': 'Three-Point Shooter',
    'A': 'Athlete',
    'B': 'Ball Handler',
    'Ps': 'Passer',
    'Po': 'Post Scorer',
    'Dp': 'Perimeter Defender',
    'Di': 'Interior Defender',
    'R': 'Rebounder',
    'V': 'Volume Scorer',
}
# canonical badge code -> raw skill code stored in the export (only differs for tp)
BADGE_SKILL = {'tp': '3'}
BADGE_ALIASES = {
    'tp': 'tp', '3': 'tp', 'three': 'tp', '3pt': 'tp', 'shooting': 'tp', 'shooter': 'tp', 'shoot': 'tp',
    'a': 'A', 'ath': 'A', 'athlete': 'A', 'athleticism': 'A', 'athletic': 'A',
    'b': 'B', 'ball': 'B', 'handler': 'B', 'handle': 'B', 'handling': 'B',
    'ps': 'Ps', 'pass': 'Ps', 'passer': 'Ps', 'passing': 'Ps',
    'po': 'Po', 'post': 'Po',
    'dp': 'Dp', 'perimeter': 'Dp', 'perim': 'Dp', 'pdef': 'Dp',
    'di': 'Di', 'interior': 'Di', 'rim': 'Di', 'idef': 'Di',
    'r': 'R', 'reb': 'R', 'rebound': 'R', 'rebounder': 'R', 'rebounding': 'R', 'glass': 'R',
    'v': 'V', 'volume': 'V', 'scorer': 'V', 'scoring': 'V',
}

# 'tp' is our stand-in for the engine's '3' skill (numeric codes collide with
# page-number parsing), so spell that out wherever the code is shown.
def _badge_code_label(code):
    return 'tp, replacement for 3' if code == 'tp' else code

def _badge_lines():
    return '\n'.join(f"``{code}`` - {nm}" + (' (replacement for 3)' if code == 'tp' else '')
                     for code, nm in BADGE_NAMES.items())

def _badge_list_field(embed):
    text = ("Usage: `badge [code]` — e.g. `badge tp`, `badge po`.\n"
            "Combine with commas for players who have all of them: `badge tp, di`.\n\n")
    text += _badge_lines()
    embed.add_field(name='Find players by badge', value=text)
    return embed

def badges(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    season = export['gameAttributes']['season']
    # Parse from raw content: the router strips numeric args (e.g. the '3'
    # badge) as page numbers, so we can't trust commandInfo['text'].
    parts = commandInfo['message'].content.split(maxsplit=1)
    rest = parts[1] if len(parts) > 1 else ''
    if not rest.strip():
        return _badge_list_field(embed)
    badgeCodes = []
    page = 1
    for tok in rest.replace(',', ' ').split():
        code = BADGE_ALIASES.get(str.lower(tok))
        if code:
            if code not in badgeCodes:
                badgeCodes.append(code)
        elif tok.isdigit():
            page = int(tok)
    if not badgeCodes:
        embed.add_field(name='Unknown badge',
                        value=f"Couldn't read a badge from `{rest.strip()}`. Pick one of:\n"
                              + _badge_lines())
        return embed

    matched = []
    for p in players:
        if p['tid'] > -2:  # active players and free agents (not prospects/retired)
            skills = p['ratings'][-1].get('skills', [])
            if all(BADGE_SKILL.get(b, b) in skills for b in badgeCodes):
                matched.append(pull_info.pinfo(p))
    label = ' + '.join(f"{BADGE_NAMES[b]} ({_badge_code_label(b)})" for b in badgeCodes)
    if not matched:
        only = len(badgeCodes) == 1
        embed.add_field(name=label,
                        value="No players currently have this badge." if only
                              else "No players currently have all of these badges.")
        return embed
    content = basics.player_list_embed(matched, page, season, 'ovr')
    embed.title = label
    embed.add_field(name=f"{len(matched)} players · sorted by {content[1]}", value=content[0])
    return embed

def matchups(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    teams = export['teams']
    text = commandInfo['text']
    abbrevs = []
    teamOne = None
    teamTwo = None
    for t in teams:
        abbrevs.append(str.lower(t['abbrev']))
    if len(text) < 3:
        embed.add_field(name='Error', value='Please provide two teams to search for matchups between.')
        return embed
    else:
        if str.lower(text[1]) in abbrevs:
            teamOne = str.lower(text[1])
        if str.lower(text[2]) in abbrevs:
            teamTwo = str.lower(text[2])
    if teamOne == None or teamTwo == None:
        embed.add_field(name='Team Finding Error', value='Make sure you use current team abbreviations.')
        return embed
    else:
        for t in teams:
            if str.lower(t['abbrev']) == teamOne:
                teamOne = t['tid']
            if str.lower(t['abbrev']) == teamTwo:
                teamTwo = t['tid']
        #find matchups
        matchupsFound = 0
        try: games = export['games']
        except KeyError: 
            embed.add_field(name='Error', value='No boxscores in file.')
            return embed
        
        currentSeason = export['gameAttributes']['season']
        for g in games:
            if g.get('season') != currentSeason:
                continue
            if (g['teams'][0]['tid'] == teamOne and g['teams'][1]['tid'] == teamTwo) or (g['teams'][0]['tid'] == teamTwo and g['teams'][1]['tid'] == teamOne):
                matchupsFound += 1
                gameInfo = pull_info.game_info(g, export, commandInfo['message'])
                text = f"{gameInfo['fullScore']} \n \n **Top Performances:** \n {gameInfo['topPerformances'][0]} \n {gameInfo['topPerformances'][1]}"
                if g['clutchPlays'] != []:
                    for c in g['clutchPlays']:
                        text += '\n' + '***' + c.split('>')[1].replace('</a', '') + '** ' + c.split('>')[2] + '*'
                embed.add_field(name=f"Game {matchupsFound}", value=text)
        
        if matchupsFound == 0:
            embed.add_field(name='No Games Found', value='Those two teams have not yet faced, or no box scores of their game are saved.')
        
        return embed
    
def summary(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    teams = export['teams']
    players = export['players']
    found = False
    for s in export['awards']:
        if s['season'] == commandInfo['season']:
            found = True
            #get champion
            playoffSettings = export['gameAttributes']['numGamesPlayoffSeries']
            for t in teams:
                t = pull_info.tinfo(t, commandInfo['season'])
                result = pull_info.playoff_result(t['roundsWon'], playoffSettings, commandInfo['season'])
                if result == '**won championship**':
                    champion = f"{basics.team_mention(commandInfo['message'], t['name'], t['abbrev'])} ({t['record']})"
                #grab FMVP team
                if t['tid'] == s['finalsMvp']['tid']:
                    fmvpTeam = t['abbrev']
            fmvp = f"{s['finalsMvp']['name']} ({fmvpTeam}) - ``{round(s['finalsMvp']['pts'], 1)} pts, {round(s['finalsMvp']['trb'], 1)} reb, {round(s['finalsMvp']['ast'], 1)} ast``"
            sfMvps = ""
            try:
                for mvp in s['sfmvp']:
                    for t in teams:
                        if t['tid'] == mvp['tid']:
                            t = pull_info.tinfo(t, commandInfo['season'])
                            abbrev = t['abbrev']
                    sfMvps += f"**{mvp['name']}** ({abbrev}) - ``{round(mvp['pts'], 1)}pts , {round(mvp['trb'], 1)} reb, {round(mvp['ast'], 1)} ast``" + '\n'
            except KeyError: sfMvps = "None"
            bestRecords = ""
            for tr in s['bestRecordConfs']:
                for t in teams:
                    if t['tid'] == tr['tid']:
                        t = pull_info.tinfo(t, commandInfo['season'])
                        bestRecords += f"{basics.team_mention(commandInfo['message'], t['name'], t['abbrev'])} ({tr['won']}-{tr['lost']})" + '\n'
            embed.add_field(name='Season Summary', value=f"**Champion:** {champion}\n Finals MVP: {fmvp} \n \n Semifinals MVPs: \n {sfMvps} \n \n Best Records: \n {bestRecords}")
            #awards
            text = ""
            awards = ['mvp', 'dpoy', 'smoy', 'roy', 'mip']
            for a in awards:
                if a in s:
                    for t in teams:
                        if t['tid'] == s[a]['tid']:
                            info = pull_info.tinfo(t, commandInfo['season'])
                            teamLine = f"{info['name']} ({info['record']}, {pull_info.playoff_result(info['roundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], commandInfo['season'])})"
                    if a == 'dpoy':
                        text += f"**{str.upper(a)}: {s[a]['name']}**" + '\n' + teamLine + '\n' + f"``{round(s[a]['trb'], 1)} reb, {round(s[a]['blk'], 1)} blk, {round(s[a]['stl'], 1)} stl``" + '\n' + '\n'
                    else:
                        text += f"**{str.upper(a)}: {s[a]['name']}**" + '\n' + teamLine + '\n' + f"``{round(s[a]['pts'], 1)} pts, {round(s[a]['trb'], 1)} reb, {round(s[a]['ast'], 1)} ast``" + '\n' + '\n'
            embed.add_field(name='Awards', value=text)

            
            #retirements
            text = ""
            retiredPlayers = []
            for p in players:
                p = pull_info.pinfo(p, commandInfo['season'])
                if p['retired']:
                    if p['retiredYear'] == commandInfo['season']:
                        retiredPlayers.append([p['name'], p['peakOvr'], commandInfo['season']-p['born']])
            retiredPlayers.sort(key=lambda r: r[1], reverse=True)
            retiredPlayers = retiredPlayers[:10]
            text = ""
            for r in retiredPlayers:
                text += f"**{r[0]}** ({r[2]} yo, peaked at {r[1]} OVR) \n"

            embed.add_field(name='Retirements', value=text) 



            #all-league
            text = ""
            allLeague = s['allLeague']
            for t in allLeague:
                text += f"\n __{t['title']}__\n"
                for pl in t['players']:
                    for te in teams:
                        if te['tid'] == pl['tid']:
                            abbrev = pull_info.tinfo(te, commandInfo['season'])['abbrev']
                    text += f"{pl['name']} ({abbrev})" + '\n'
            embed.add_field(name='All-League Teams', value=text)
            
            #all-defense
            text = ""
            allDefense = s['allDefensive']
            for t in allDefense:
                text += f"\n __{t['title']}__\n"
                for pl in t['players']:
                    for te in teams:
                        if te['tid'] == pl['tid']:
                            abbrev = pull_info.tinfo(te, commandInfo['season'])['abbrev']
                    text += f"{pl['name']} ({abbrev})" + '\n'
            embed.add_field(name='All-Defensive Teams', value=text)

            #all-rookie
            text = f"\n __All-Rookie Team__\n"
            allRookie = s['allRookie']
            for pl in allRookie:
                for te in teams:
                    if te['tid'] == pl['tid']:
                        abbrev = pull_info.tinfo(te, commandInfo['season'])['abbrev']
                text += f"{pl['name']} ({abbrev})" + '\n'
            embed.add_field(name='All-Rookie Team', value=text)
        
    if found == False:
        embed.add_field(name='Error', value='No summary data for that season.')
    return embed


def mvp(embed, commandInfo):
    """Shows top 10 MVP candidates based on stats during the regular season"""
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = commandInfo['season']

    # Build team wins dictionary
    team_wins = {}
    for team in teams:
        for s in team['seasons']:
            if s['season'] == season:
                team_wins[team['tid']] = s['won']
                break

    # Calculate MVP scores
    candidates = []
    for p in players:
        # Find current season stats
        current_stats = None
        for s in p['stats']:
            if s['season'] == season and not s['playoffs']:
                current_stats = s
                break

        if current_stats and current_stats['gp'] >= 10:  # Min 10 games
            # Get team wins
            tw = team_wins.get(current_stats['tid'], 0)

            # Calculate per-game stats
            ppg = current_stats['pts'] / current_stats['gp'] if current_stats['gp'] > 0 else 0
            rpg = (current_stats['orb'] + current_stats['drb']) / current_stats['gp'] if current_stats['gp'] > 0 else 0
            apg = current_stats['ast'] / current_stats['gp'] if current_stats['gp'] > 0 else 0

            # MVP score formula
            mvp_score = (
                current_stats.get('ewa', 0) * 3.5 +  # 35% EWA
                current_stats.get('per', 0) * 2.5 +  # 25% PER
                (tw / 82) * 20 +                      # 20% team success
                (ppg / 30) * 10 +                     # 10% scoring
                ((apg + rpg) / 20) * 10               # 10% other stats
            )

            # Get team info
            team_abbrev = ""
            for t in teams:
                if t['tid'] == current_stats['tid']:
                    team_abbrev = t['abbrev']
                    break

            candidates.append({
                'name': f"{p['firstName']} {p['lastName']}",
                'team': team_abbrev,
                'score': mvp_score,
                'ppg': ppg,
                'rpg': rpg,
                'apg': apg,
                'per': current_stats.get('per', 0),
                'ewa': current_stats.get('ewa', 0),
                'team_wins': tw
            })

    # Sort by MVP score
    candidates.sort(key=lambda x: x['score'], reverse=True)

    # Format output
    embed.title = f"{season} MVP Race"
    text = ""
    for i, c in enumerate(candidates[:10], 1):
        for t in teams:
            if t['abbrev'] == c['team']:
                for s in t['seasons']:
                    if s['season'] == season:
                        c['team_losses'] = s['lost']
                        break
        text += f"**{i}. {c['name']}** ({c['team']}) - {c['ppg']:.1f} PPG, {c['rpg']:.1f} RPG, {c['apg']:.1f} APG\n"
        text += f"   {c['per']:.1f} PER | {c['ewa']:.1f} EWA | Team: {c['team_wins']}-{c['team_losses']}\n\n"

    embed.add_field(name="Top 10 MVP Candidates", value=text if text else "No eligible players found", inline=False)
    return embed



def dpoy(embed, commandInfo):
    """Shows top 10 Defensive Player of the Year candidates"""
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = commandInfo['season']

    # Calculate DPOY scores
    candidates = []
    for p in players:
        # Find current season stats
        current_stats = None
        for s in p['stats']:
            if s['season'] == season and not s['playoffs']:
                current_stats = s
                break

        if current_stats and current_stats['gp'] >= 10:  # Min 10 games
            # Calculate defensive stats
            bpg = current_stats['blk'] / current_stats['gp'] if current_stats['gp'] > 0 else 0
            spg = current_stats['stl'] / current_stats['gp'] if current_stats['gp'] > 0 else 0

            # DPOY score formula
            dpoy_score = (
                current_stats.get('dbpm', 0) * 3.5 +     # 35% Defensive BPM
                current_stats.get('dws', 0) * 3.0 +      # 30% Defensive Win Shares
                (bpg + spg) * 5.0 +                      # 20% blocks + steals
                (100 - current_stats.get('drtg', 100)) * 0.15  # 15% defensive rating (inverted)
            )

            # Get team info
            team_abbrev = ""
            for t in teams:
                if t['tid'] == current_stats['tid']:
                    team_abbrev = t['abbrev']
                    break

            candidates.append({
                'name': f"{p['firstName']} {p['lastName']}",
                'team': team_abbrev,
                'score': dpoy_score,
                'bpg': bpg,
                'spg': spg,
                'dbpm': current_stats.get('dbpm', 0),
                'dws': current_stats.get('dws', 0),
                'drtg': current_stats.get('drtg', 0)
            })

    # Sort by DPOY score
    candidates.sort(key=lambda x: x['score'], reverse=True)

    # Format output
    embed.title = f"{season} Defensive Player of the Year Race"
    text = ""
    for i, c in enumerate(candidates[:10], 1):
        text += f"**{i}. {c['name']}** ({c['team']}) - {c['bpg']:.1f} BPG, {c['spg']:.1f} SPG\n"
        text += f"   {c['dbpm']:.1f} DBPM | {c['dws']:.1f} DWS | {c['drtg']:.1f} DRTG\n\n"

    embed.add_field(name="Top 10 DPOY Candidates", value=text if text else "No eligible players found", inline=False)
    return embed


def sixmoyrace(embed, commandInfo):
    """Shows top 10 Sixth Man of the Year candidates"""
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    players = export['players']
    teams = export['teams']
    season = commandInfo['season']

    # Calculate 6MOY scores (bench players)
    candidates = []
    for p in players:
        # Find current season stats
        current_stats = None
        for s in p['stats']:
            if s['season'] == season and not s['playoffs']:
                current_stats = s
                break

        # Check if bench player (started less than 50% of games)
        if current_stats and current_stats['gp'] >= 10:
            starts_pct = current_stats['gs'] / current_stats['gp'] if current_stats['gp'] > 0 else 0
            if starts_pct < 0.5:  # Bench player
                # Calculate per-game stats
                ppg = current_stats['pts'] / current_stats['gp'] if current_stats['gp'] > 0 else 0
                rpg = (current_stats['orb'] + current_stats['drb']) / current_stats['gp'] if current_stats['gp'] > 0 else 0
                apg = current_stats['ast'] / current_stats['gp'] if current_stats['gp'] > 0 else 0
                mpg = current_stats['min'] / current_stats['gp'] if current_stats['gp'] > 0 else 0

                # 6MOY score formula
                sixmoy_score = (
                    current_stats.get('per', 0) * 3.0 +  # 30% PER
                    current_stats.get('ewa', 0) * 2.5 +  # 25% EWA
                    (ppg / 20) * 20 +                     # 20% scoring (adjusted for bench)
                    (mpg / 30) * 15 +                     # 15% minutes
                    ((apg + rpg) / 15) * 10              # 10% other stats
                )

                # Get team info
                team_abbrev = ""
                for t in teams:
                    if t['tid'] == current_stats['tid']:
                        team_abbrev = t['abbrev']
                        break

                candidates.append({
                    'name': f"{p['firstName']} {p['lastName']}",
                    'team': team_abbrev,
                    'score': sixmoy_score,
                    'ppg': ppg,
                    'rpg': rpg,
                    'apg': apg,
                    'mpg': mpg,
                    'per': current_stats.get('per', 0),
                    'starts': current_stats['gs'],
                    'games': current_stats['gp']
                })

    # Sort by 6MOY score
    candidates.sort(key=lambda x: x['score'], reverse=True)

    # Format output
    embed.title = f"{season} Sixth Man of the Year Race"
    text = ""
    for i, c in enumerate(candidates[:10], 1):
        text += f"**{i}. {c['name']}** ({c['team']}) - {c['ppg']:.1f} PPG, {c['rpg']:.1f} RPG, {c['apg']:.1f} APG\n"
        text += f"   {c['mpg']:.1f} MPG | {c['per']:.1f} PER | {c['starts']}/{c['games']} starts\n\n"

    embed.add_field(name="Top 10 6MOY Candidates", value=text if text else "No eligible bench players found", inline=False)
    return embed


def _gmoty_rankings(export, commandInfo):
    """Build GM rankings for a given season. Returns sorted list of GM dicts."""
    season = commandInfo['season']
    teams = export['teams']
    events = export.get('events', [])
    teamlist = serversList.get(str(commandInfo['serverId']), {}).get('teamlist', {})
    playoffSettings = export['gameAttributes']['numGamesPlayoffSeries']

    # Reverse teamlist: tid -> user_id
    tid_to_user = {}
    for uid, tid in teamlist.items():
        tid_to_user[tid] = uid

    # Count trades and FA signings per team this season
    trades_by_tid = {}
    fa_signings_by_tid = {}
    for e in events:
        if e.get('season') != season:
            continue
        if e.get('type') == 'trade':
            for tid in e.get('tids', []):
                trades_by_tid[tid] = trades_by_tid.get(tid, 0) + 1
        elif e.get('type') == 'freeAgent':
            for tid in e.get('tids', []):
                fa_signings_by_tid[tid] = fa_signings_by_tid.get(tid, 0) + 1

    gms = []
    for t in teams:
        tid = t['tid']
        if tid not in tid_to_user:
            continue

        current = None
        prev = None
        for s in t['seasons']:
            if s['season'] == season:
                current = s
            elif s['season'] == season - 1:
                prev = s

        if not current:
            continue

        total_games = current['won'] + current['lost']
        if total_games == 0:
            continue
        win_pct = current['won'] / total_games
        rounds_won = current['playoffRoundsWon']

        win_diff = 0
        if prev:
            prev_total = prev['won'] + prev['lost']
            if prev_total > 0:
                prev_pct = prev['won'] / prev_total
                win_diff = win_pct - prev_pct

        playoff_str = pull_info.playoff_result(rounds_won, playoffSettings, season)

        trades = trades_by_tid.get(tid, 0)
        signings = fa_signings_by_tid.get(tid, 0)

        score = 0
        score += win_pct * 40
        score += win_diff * 20
        score += trades * 1.5
        score += signings * 1

        abbrev = current.get('abbrev', t.get('abbrev', '???'))

        gms.append({
            'uid': tid_to_user[tid],
            'abbrev': abbrev,
            'record': f"{current['won']}-{current['lost']}",
            'win_pct': win_pct,
            'playoff': playoff_str,
            'win_diff': win_diff,
            'trades': trades,
            'signings': signings,
            'score': score,
        })

    gms.sort(key=lambda x: x['score'], reverse=True)
    return gms


def _format_gm_line(i, g):
    medal = ""
    if i == 1:
        medal = " :trophy:"
    elif i == 2:
        medal = " :second_place:"
    elif i == 3:
        medal = " :third_place:"

    improve_str = ""
    if g['win_diff'] > 0:
        improve_str = f" (+{g['win_diff']*100:.0f}%)"
    elif g['win_diff'] < 0:
        improve_str = f" ({g['win_diff']*100:.0f}%)"

    moves = []
    if g.get('trades', 0) > 0:
        moves.append(f"{g['trades']} trades")
    if g.get('signings', 0) > 0:
        moves.append(f"{g['signings']} signings")
    moves_str = ", ".join(moves) if moves else "no moves"

    line = f"**{i}. <@{g['uid']}>** ({g['abbrev']}){medal}\n"
    line += f"\u2003{g['record']}{improve_str} | {g['playoff']} | {moves_str}\n"
    return line


def gmoty(embed, commandInfo):
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = commandInfo['season']
    gms = _gmoty_rankings(export, commandInfo)

    if not gms:
        embed.title = f"{season} GM of the Year"
        embed.add_field(name="GM of the Year", value="No activity for this season yet.", inline=False)
        return embed

    embed.title = f"{season} GM of the Year Race"
    text = ""
    for i, g in enumerate(gms[:5], 1):
        text += _format_gm_line(i, g)

    embed.add_field(name="Top GMs", value=text, inline=False)
    embed.set_footer(text="Just for fun, not that serious. Don't get mad at Odle.")
    return embed





                

    
        
    


# ============= LEAGUE MEDIA (-media) =============

def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"


# Career milestone thresholds (regular season), lowest first. A crossing is
# announced when a player's career total passes a step during the viewed season.
MEDIA_MILESTONES = {
    'pts': ([10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000], 'career points'),
    'reb': ([5000, 7500, 10000, 12500, 15000, 17500, 20000], 'career rebounds'),
    'ast': ([3000, 5000, 7500, 10000, 12500, 15000], 'career assists'),
    'tp': ([1000, 1500, 2000, 2500, 3000, 3500, 4000], 'career threes'),
    'stl': ([1000, 1500, 2000, 2500, 3000], 'career steals'),
    'blk': ([1000, 1500, 2000, 2500, 3000], 'career blocks'),
}

# Minimum single-game value before an all-time rank is worth mentioning —
# keeps "3rd most steals all-time (4)" out of young leagues.
MEDIA_RANK_FLOORS = {'pts': 40, 'reb': 20, 'ast': 15, 'tp': 8, 'stl': 6, 'blk': 6}


def _feat_val(f, key):
    s = f.get('stats', {})
    if key == 'reb':
        return s.get('orb', 0) + s.get('drb', 0)
    return s.get(key, 0)


def media_feats(embed, commandInfo):
    """-media feats: notable single-game performances (with all-time single-game
    ranks) and career milestone crossings for the viewed season."""
    export = shared_info.serverExports[str(commandInfo['serverId'])]
    season = commandInfo['season']
    players = export['players']
    feats = export.get('playerFeats', [])
    team_abbrevs = {t['tid']: t['abbrev'] for t in export['teams']}

    embed.title = "League Media — Notable Feats & Milestones"
    embed.description = f"{season} season"

    # All-time single-game pools per stat, across every feat ever recorded
    rank_stats = [('pts', 'points'), ('reb', 'rebounds'), ('ast', 'assists'),
                  ('tp', 'threes'), ('stl', 'steals'), ('blk', 'blocks')]
    pools = {k: sorted((_feat_val(f, k) for f in feats), reverse=True) for k, _ in rank_stats}

    def alltime_rank(key, value):
        greater = 0
        for x in pools[key]:
            if x > value:
                greater += 1
            else:
                break
        return greater + 1

    # --- Notable performances this season ---
    def notability(f):
        s = f['stats']
        score = (s.get('pts', 0) + 0.7 * _feat_val(f, 'reb') + 0.8 * s.get('ast', 0)
                 + 2 * (s.get('stl', 0) + s.get('blk', 0)) + 1.2 * s.get('tp', 0))
        score += 12 * s.get('td', 0) + 40 * s.get('qd', 0) + 30 * s.get('fxf', 0)
        return score

    season_feats = sorted((f for f in feats if f.get('season') == season),
                          key=notability, reverse=True)
    feat_lines = []
    for f in season_feats[:5]:
        s = f['stats']
        reb = _feat_val(f, 'reb')
        bits = [f"{s.get('pts', 0)} pts", f"{reb} reb", f"{s.get('ast', 0)} ast"]
        if s.get('tp', 0) >= 5: bits.append(f"{s['tp']} 3PM")
        if s.get('stl', 0) >= 4: bits.append(f"{s['stl']} stl")
        if s.get('blk', 0) >= 4: bits.append(f"{s['blk']} blk")
        tags = []
        if s.get('qd'): tags.append('QUADRUPLE-DOUBLE')
        elif s.get('td'): tags.append('triple-double')
        if s.get('fxf'): tags.append('5x5')
        ranks = []
        for key, label in rank_stats:
            v = _feat_val(f, key)
            if v >= MEDIA_RANK_FLOORS[key]:
                r = alltime_rank(key, v)
                if r <= 10:
                    ranks.append(f"{_ordinal(r)} most {label} in a game all-time" if r > 1
                                 else f"most {label} in a game all-time")
        tm = team_abbrevs.get(f.get('tid'), '???')
        opp = team_abbrevs.get(f.get('oppTid'), '???')
        res = f"{f.get('result', '')} {f.get('score', '')}".strip()
        po = ' (playoffs)' if f.get('playoffs') else ''
        line = f"**{f.get('name', '?')}** ({tm} vs {opp}, {res}{po}): {', '.join(bits)}"
        extras = tags + ranks
        if extras:
            line += f" — *{'; '.join(extras)}*"
        feat_lines.append(line)

    if feat_lines:
        embed.add_field(name='Notable Performances', value='\n'.join(feat_lines), inline=False)

    # --- Career milestones crossed this season ---
    crossed = []
    for p in players:
        rows = [r for r in p.get('stats', []) if not r.get('playoffs') and r.get('season', 0) <= season]
        if not any(r.get('season') == season and r.get('gp', 0) > 0 for r in rows):
            continue
        for key, (steps, label) in MEDIA_MILESTONES.items():
            total = sum(_feat_val({'stats': r}, key) for r in rows)
            this_season = sum(_feat_val({'stats': r}, key) for r in rows if r.get('season') == season)
            before = total - this_season
            hit = None
            for m in steps:
                if before < m <= total:
                    hit = m
            if hit:
                name = f"{p.get('firstName', '')} {p.get('lastName', '')}".strip()
                crossed.append((hit / steps[0], hit, int(total), label, name))
    crossed.sort(reverse=True)
    milestone_lines = [f"**{name}** crossed **{hit:,} {label}** — now at {total:,}"
                       for _, hit, total, label, name in crossed[:5]]
    if milestone_lines:
        embed.add_field(name='Career Milestones', value='\n'.join(milestone_lines), inline=False)

    if not feat_lines and not milestone_lines:
        embed.add_field(name='League Media',
                        value=f'No notable feats or milestone crossings found for {season}.', inline=False)
    return embed


def media(embed, commandInfo):
    """-media (mod only): post the phase-appropriate AI media report in the
    channel the command was run in. -media feats: notable performances +
    career milestones instead."""
    import ai_media
    variant = str.lower(commandInfo['text'][1]) if len(commandInfo['text']) > 1 else ''
    if variant in ('feats', 'feat', 'records', 'milestones'):
        return media_feats(embed, commandInfo)

    export = shared_info.serverExports[str(commandInfo['serverId'])]
    guild_id = commandInfo['serverId']
    # Post wherever the command was run — mods pick the channel by running it there
    channel_id = commandInfo['message'].channel.id

    phase = export['gameAttributes']['phase']
    generators = {
        0: (ai_media.fire_and_forget_preseason_preview, 'season preview'),
        1: (ai_media.fire_and_forget_midseason_update, 'midseason update'),
        2: (ai_media.fire_and_forget_midseason_update, 'midseason update'),
        3: (ai_media.fire_and_forget_playoff_preview, 'playoff preview'),
        4: (ai_media.fire_and_forget_playoff_preview, 'playoff preview'),
        5: (ai_media.fire_and_forget_season_recap, 'season recap'),
        6: (ai_media.fire_and_forget_draft_lottery_preview, 'draft lottery preview'),
        7: (ai_media.fire_and_forget_draft_results_recap, 'draft results recap'),
        8: (ai_media.fire_and_forget_fa_preview, 'free agency preview'),
    }
    gen = generators.get(phase)
    if gen is None:
        embed.add_field(name='Error',
                        value='No media report is available for the current league phase.', inline=False)
        return embed
    gen[0](export, guild_id, channel_id)
    embed.add_field(name='League Media',
                    value=f"Writing a **{gen[1]}** — it will post here shortly.\n"
                          f"*Tip: `-media feats` shows notable performances and career milestones.*", inline=False)
    return embed
