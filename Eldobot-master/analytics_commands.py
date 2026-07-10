import commandmaster
import commands
import shared_info
import os
from data_dir import data_path

def calls(embed, author, commandInfo):

    commandaliases = {
        "r": "ratings",
        "s": "stats",
        "b": "bio",
        "setgm": "addgm",
        'phs':'hstats',
        'phstats':'hstats',
        "ts": "tstats",
        "tsp": 'ptstats',
        "rs": "resignings",
        "runrs": "runresignings",
        "ppr":"playoffpredict",
        "cs": "cstats",
        "hs": "hstats",
        'updateexport': 'updatexport',
        'mostuniform':'mostaverage',
        'update':'updatexport'
    }
    if len(commandInfo['message'].split(" ")) < 2:
        embed.add_field(name = "ERROR", value = "Please specify if you want to view stats by servers or users. Like: -calls user stats")
        return embed
    i = commandInfo['message'].split(" ")[1]
    if i.lower() == "user" or i.lower() == 'users':
        mode = "u"
    elif i.lower() == 'server' or i.lower() == 'servers':
        mode = "s"
    else:
        embed.add_field(name = "ERROR", value = "Please specify if you want to view stats by servers or users")
        return embed
    date = None
    cmd = None
    tracks = commandmaster.tracks
    for item in commandInfo['message'].split(" ")[2:]:
        if item.count("-") == 2:
            for element in tracks:
                if item in tracks[element]:
                        date = item
        if item.lower() in commands.commandsRaw:
            cmd = item.lower()
        if item.lower() in commandaliases:
            cmd =commandaliases.get(item.lower())
    if cmd is None:
        embed.add_field(name = "ERROR", value = "Command not found. use -mostused to see list of command names.")
        return embed
    dictionary = dict()
    for server in tracks:
        s2 = tracks[server]
        for d in s2:
            if date is None or date == d:
                d2 = s2[d]
                if not isinstance(d2, dict):
                    continue
                for u in d2:
                    u2 = d2[u]
                    if not isinstance(u2, dict):
                        continue
                    for cmdname in u2:
                        if cmdname == cmd:
                            value = u2[cmdname]
                            if mode == 's':
                                if not server in dictionary:
                                    dictionary.update({server:value})
                                else:
                                    dictionary.update({server:dictionary[server]+value})
                            if mode == 'u':
                                if not u in dictionary:
                                    dictionary.update({u:value})
                                else:
                                    dictionary.update({u:dictionary[u]+value})
    print(dictionary)
    cmdstring = cmd+" "
    if date is None:
        datestr = "all days"
    else:
        datestr = date
    if mode == 's':
        servers2 = dict()
        for g in shared_info.bot.guilds:
            if str(g.id) in dictionary:
                servers2.update({g.name:dictionary[str(g.id)]})
        ls = list(servers2.keys())
        ls = sorted(ls, key = lambda x: servers2[x], reverse = True)

        ranks = ""
        for i in range(0,min(100, len(ls))):
            ranks += str(i+1)+". **" + ls[i]+"**: "+str(servers2[ls[i]])+"\n"
            if len(ranks) > 900:
                embed.add_field(name = "Ranking for server usage of command "+cmdstring+datestr, value = ranks)
                ranks = ""
        if len(ranks) > 0:
            embed.add_field(name = "Ranking for server usage of command "+cmdstring+datestr, value = ranks)
        return embed
    if mode == 'u':
        outside = 0
        dict2 = dict()
        for item, value in dictionary.items():
            if commandInfo["guild"].get_member(int(item)) is not None:
                dict2.update({"<@"+item+">":value})
            else:
                outside += value
        if outside > 0:
            dict2.update({"Users not in server":outside})
        ls = list(dict2.keys())
        ls = sorted(ls, key = lambda x: dict2[x], reverse = True)
        ranks = ""
        for i in range(0,min(120, len(ls))):
            ranks += str(i+1)+". **" + ls[i]+"**: "+str(dict2[ls[i]])+"\n"
            if i %20== 19:
                embed.add_field(name = "Ranking for users in usage of command "+cmdstring+datestr, value = ranks)
                ranks = ""
        if len(ranks) > 0:
            embed.add_field(name = "Ranking for users in usage of command "+cmdstring+datestr, value = ranks)
        return embed

def leastusedcommands(embed, author, commandInfo):
    return mostusedcommands(embed, author, commandInfo, False)

def mostusedcommands(embed, author, commandInfo,ismost = True):
    tracks = commandmaster.tracks
    user = None
    date = None
    ss = None
    for item in commandInfo['message'].split(" "):
        if "@" in item:
            try:
                user = int(item.replace("@","").replace("!","").replace("<","").replace(">",""))
                user = str(user)
            except ValueError:
                pass
        if item == "here":
            ss = str(commandInfo['guild'].id)
        if item.count("-") == 2:
            for element in tracks:
                if item in tracks[element]:
                        date = item
    commanddict = dict()
    for server in tracks:
        if ss is None or ss == server:
            s2 = tracks[server]

            for d in s2:
                if date is None or date == d:
                    d2 = s2[d]
                    if not isinstance(d2, dict):
                        continue
                    for u in d2:
                        if user is None or u == user:
                            u2 = d2[u]
                            if not isinstance(u2, dict):
                                continue
                            for cmdname in u2:
                                if cmdname in commanddict:
                                    commanddict.update({cmdname:commanddict[cmdname]+u2[cmdname]})
                                else:
                                    commanddict.update({cmdname:u2[cmdname]})

    ls = list(commanddict.keys())
    ls = sorted(ls, key = lambda x: commanddict[x], reverse = True)
    if not ismost:
        ls = sorted(ls, key = lambda x: commanddict[x], reverse = False)
    if user is None:
        usstr = "everyone"
    else:
        usstr = "this guy"
    if date is None:
        dtstr = "all days"
    else:
        dtstr = date
    title = "Commands for "+usstr + " on "+dtstr
    ranks = ""
    for i in range(0,min(120, len(ls))):
        ranks += str(i+1)+". **" + ls[i]+"**: "+str(commanddict[ls[i]])+"\n"
        if (i % 20) == 19:
            embed.add_field(name =title, value = ranks, inline = True)
            ranks = ""
    if len(ranks) > 0:
        embed.add_field(name = title,value = ranks, inline = True)
    return embed

def mostactiveusers(embed, author, commandInfo):
    tracks = commandmaster.tracks
    for server in tracks:
        if server == str(commandInfo['guild'].id):
            s = tracks[server]
            userdict = dict()
            for d in s:
                d2 = s[d]
                if not isinstance(d2, dict):
                    continue
                for u in d2:
                    if not u in userdict:
                        userdict.update({u:0})
                    udict = d2[u]
                    if not isinstance(udict, dict):
                        continue
                    for item, value in udict.items():
                        userdict.update({u:userdict[u]+value})
    ls = list(userdict.keys())
    ls = sorted(ls, key = lambda x: userdict[x], reverse = True)
    title = "Most active users in this server"
    ranks = ""
    for i in range(0,min(120, len(ls))):
        ranks += str(i+1)+". <@" + ls[i]+">: "+str(userdict[ls[i]])+"\n"
        if (i % 20) == 19:
            embed.add_field(name =title, value = ranks, inline = True)
            ranks = ""
    if len(ranks) > 0:
        embed.add_field(name = title,value = ranks, inline = True)
    return embed

def servers(embed, author, commandInfo):
    tracks = commandmaster.tracks
    date = None
    for item in commandInfo['message'].split(" "):
        if item.count("-") == 2:
            for element in tracks:
                if item in tracks[element]:
                        date = item

    serverusages = dict()
    lastactive = dict()
    for server in tracks:
        serverusages.update({server:0})
        s2 = tracks[server]
        for d in s2:
            # date keys are stored as YYYY-MM-DD; the newest one a server has
            # any activity on is its "last active" day.
            if isinstance(s2[d], dict) and len(d) == 10 and d.count("-") == 2:
                if server not in lastactive or d > lastactive[server]:
                    lastactive.update({server: d})
            if date is None or d == date:
                d2 = s2[d]
                if not isinstance(d2, dict):
                    continue
                for u in d2:

                    u2 = d2[u]
                    if not isinstance(u2, dict):
                        continue
                    for cmdname in u2:
                        serverusages.update({server:serverusages[server]+u2[cmdname]})
    newserverusages = dict()
    for i in range(20):
        newdate = '2025-06-'+str(i)

        for server in tracks:

            s2 = tracks[server]
            for d in s2:
                if  d == newdate:

                    d2 = s2[d]
                    if not isinstance(d2, dict):
                        continue
                    for u in d2:

                        u2 = d2[u]
                        if not isinstance(u2, dict):
                            continue
                        for cmdname in u2:
                            if not server in newserverusages:
                                newserverusages.update({server:0})
                            newserverusages.update({server:newserverusages[server]+u2[cmdname]})


    servers2 = dict()
    serverslast = dict()
    toleave = []
    guildids = []
    for g in shared_info.bot.guilds:
        guildids.append(g.id)
        servers2.update({g.name: serverusages.get(str(g.id), 0)})
        serverslast.update({g.name: lastactive.get(str(g.id), "never")})
        if str(g.id) in newserverusages:
            if newserverusages[str(g.id)] == 0:
                toleave.append(g)

        if str(g.id) not in newserverusages:
            toleave.append(g)
    for x in os.listdir(data_path('exports')):
        gid = x.replace('-export.json','').replace('-export.gz','')
        try:
            if not int(gid) in guildids:
                print(x)
                os.remove(data_path('exports/'+x))
        except ValueError:
            pass
    ls = list(servers2.keys())
    ls = sorted(ls, key = lambda x: servers2[x], reverse = True)
    if date is None:
        datestr = "all days"
    else:
        datestr = date
    ranks = ""
    for i in range(0,min(100, len(ls))):
        ranks += str(i+1)+". **" + ls[i]+"**: "+str(servers2[ls[i]])+" _(last active: "+serverslast[ls[i]]+")_\n"
        if len(ranks) > 900:
            embed.add_field(name = "Ranking for "+datestr, value = ranks)
            ranks = ""
    if len(ranks) > 0:
        embed.add_field(name = "Ranking for "+datestr, value = ranks)
    return embed
