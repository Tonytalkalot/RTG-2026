import shared_info
exports = shared_info.serverExports
serversList = shared_info.serversList
import basics
import pull_info
from pull_info import tinfo
import discord
import team_commands as tc
import asyncio
import os

##TEAM COMMANDS

commandFuncs = {
    'roster': tc.roster,
    'tcompare':tc.teamcompare,
    'penalties':tc.penalties,
    'sroster': tc.roster,
    'psroster': tc.roster,
    'progster': tc.roster,
    'proster': tc.roster,
    'lineup': tc.lineup,
    'penalty':tc.penalty,
    'picks': tc.picks,
    'ownspicks': tc.ownspicks,
    'history': tc.history,
    'finances': tc.finances,
    'seasons': tc.seasons,
    'tstats': tc.tstats,
    'ptstats': tc.tstats,
    'sos': tc.sos,
    'schedule': tc.schedule,
    'gamelog': tc.gamelog,
    'game': tc.game,
    'boxscore': tc.boxscore,
    'capspace':tc.capspace,
    'rostergraph':tc.rostergraph,
    'rgoptions':tc.rgoptions,
    'testprog':tc.simprogs,
    'synergylineups':tc.synergylineups,
    'tscout':tc.tscout,
    'tnbacomp':tc.tnbacomp
}

async def process_text(text, message):
    export = shared_info.serverExports[str(message.guild.id)]
    season = export['gameAttributes']['season']
    players = export['players']
    teams = export['teams']
    commandSeason = season
    command = str.lower(text[0])
    for m in text:
        try:
            m = int(m)
            commandSeason = m
            text.remove(str(commandSeason))
        except:
            pass

    #default the command team to the user team, then search if a team was specified
    try: commandTid = serversList[str(message.guild.id)]['teamlist'][str(message.author.id)]
    except KeyError: commandTid = -1
    practicalSeason = commandSeason
    if command in ['game', 'boxscore']:
        practicalSeason = season
    if practicalSeason != season:
        for t in teams:
            seasons = t['seasons']
            for s in seasons:
                if s['season'] == practicalSeason:
                    teamNames = [s['abbrev'], s['region'], s['name'], s['region'] + ' ' + s['name']]
                    for name in teamNames:
                        if str.lower(name.strip()) in [str(m).lower() for m in text]:
                            commandTid = t['tid']
        if commandTid == -1:
            for t in teams:
                teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
                for name in teamNames:
                    if str.lower(name.strip()) in [str(m).lower() for m in text]:
                        commandTid = t['tid']
    else:
        for t in teams:
            teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
            for name in teamNames:
                if str.lower(name.strip()) in [str(m).lower() for m in text]:
                    commandTid = t['tid']
    found = False
    for team in teams:
        if team['tid'] == int(commandTid):
            found = True
            t = pull_info.tinfo(team, practicalSeason)

    if found == False:
        await message.channel.send('No team found. Please specify a team.')
    else:

        descriptionLine = f"{practicalSeason}: {t['record']} record, {pull_info.playoff_result(t['roundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], commandSeason, True)}"
        if descriptionLine[-2:] == ', ':
            descriptionLine = descriptionLine[:-2]
        embed = discord.Embed(title=t['name'], description=descriptionLine, color=t['color'])

        #pull together some essential command info to pass along to the command funcs
        commandInfo = {"serverId": message.guild.id,
                    "season": commandSeason,
                    "command": command,
                    "message": message}
        #uncomment to get a full error message in console
        #embed = commandFuncs[command](embed, t, commandInfo)
        result = commandFuncs[command](embed, t, commandInfo) #fill the embed with the specified function
        if asyncio.iscoroutine(result):
            embed = await result
        else:
            embed = result

        #embed.add_field(name='Error', value="An error occured. Command may not be specified.", inline=False)


        embed.set_footer(text=shared_info.embedFooter(message.guild))
        gc = ["rostergraph"]
        if command in gc:
            waswrong = False
            for field in embed.fields:
                if field.name == "Error":
                    waswrong = True
            if not waswrong:
                try:
                    f = open("second_figure.png",'rb')
                    await message.channel.send("Roster graph", file = discord.File(f))
                    f.close()
                except Exception:
                     await message.channel.send("There was some kind of mistake")
        backupembed = embed.copy()
        logo_file = None
        if command in ['roster','sroster','lineup','progster','penalty','history','ownspicks','picks','tstats','ptstats','schedule','seasons','gamelog']:
            # image
            for team in teams:
                if team['tid'] == int(commandTid):
                    u = team['imgURL']
                    if u[0:4] == '/img':
                        filename = u.split("/")[-1].replace("svg","png")
                        local_path = os.path.join(os.path.dirname(__file__), 'img', filename)
                        if os.path.exists(local_path):
                            logo_file = discord.File(local_path, filename=filename)
                            embed.set_thumbnail(url=f"attachment://{filename}")
                        print(f"local img: {local_path}")
                    else:
                        embed.set_thumbnail(url=u)
                        print(u)

        if logo_file:
            await message.channel.send(embed=embed, file=logo_file)
        else:
            await message.channel.send(embed=embed)
        #except Exception:
          #  print("no image found")
          #  await message.channel.send(embed=backupembed)
