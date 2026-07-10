import shared_info
exports = shared_info.serverExports
import basics
import pull_info
from pull_info import pinfo
from pull_info import tinfo
import discord
import player_commands as pc
import asyncio
import os
from data_dir import data_path
##PLAYER COMMANDS

commandFuncs = {
    'stats': pc.stats,
    'progspredict':pc.progspredict,
    'series':pc.series,
    'pratings':pc.pratings,
    'pcompare':pc.pcompare,
    'bio': pc.bio,
    'padv': pc.adv,
    'ratings': pc.ratings,
    'pshots':pc.shots,
    'shots':pc.shots,
    'adv': pc.adv,
    'progs': pc.progs,
    'hstats': pc.hstats,
    'cstats': pc.stats,
    'pstats': pc.stats,
    'awards': pc.awards,
    'pgamelog': pc.pgamelog,
    'compare': pc.compare,
    'nbacompare': 'players',
    'proggraph':pc.progschart,
    'trivia':pc.trivia,
    'hint':pc.hint,
    'whoidolizes':pc.whoidolizes,
    'cschart':pc.progressionchart,
    'schart':pc.progressionchart,
    'composites':pc.composites,
    'synergy':pc.synergy,
    'lcomplete':pc.lineupcompletion,
    'addrating':pc.addrating,
    'contracthistory':pc.contracthistory,
    'nbacomp':pc.nbacomp,
    'scout':pc.scout,
    'mood':pc.mood,
    'answer':pc.answer,
}


async def process_text(text, message):
    export =shared_info.serverExports[str(message.guild.id)]
    season = export['gameAttributes']['season']
    players = export['players']
    teams = export['teams']
    commandSeason = season
    command = str.lower(text[0])

    # Handle nickname command specially — it uses subcommands, not a player name
    if command == 'nickname':
        await pc.nickname(text, message)
        return

    # Handle answer command specially — it takes free-text, not a player name
    if command == 'answer':
        from shared_info import trivias
        channel = message.channel
        guess_text = ' '.join(text[1:]).strip().lower()
        embed = discord.Embed(title="Trivia", description="Guess who")
        if channel not in trivias:
            embed.add_field(name='No trivia active', value="There's no trivia running in this channel. Use -trivia to start one!")
        elif not guess_text:
            prefix = shared_info.serversList[str(message.guild.id)].get('prefix', '-')
            embed.add_field(name='Usage', value=f"Use **{prefix}answer [player name]** to submit your guess!")
        else:
            correct_name = trivias[channel]['name'].lower()
            if guess_text in correct_name or correct_name.split()[-1] == guess_text:
                embed = discord.Embed(title="Trivia - Correct!", description=f"The answer was **{trivias[channel]['name']}**!", color=0x00ff00)
                del trivias[channel]
            else:
                embed.add_field(name='Nope!', value="That's not right, try again! Use -hint for a clue.")
        embed.set_footer(text=shared_info.embedFooter(message.guild))
        await message.channel.send(embed=embed)
        return
    for m in text:
        try:
            m = int(m)
            if command != 'addrating':
                commandSeason = m
            text.remove(str(commandSeason))
        except:
            pass
    
    playerToFind = ' '.join(text[1:])
    playerPid = basics.find_match(playerToFind, export,settings =  shared_info.serversList[str(message.guild.id)])
    fullplayer = None
    for player in players:
        if player['pid'] == playerPid:
            p = player
            fullplayer = player
    if commandSeason == season:
        p = pinfo(p)
        
    else:
        p = pinfo(p, commandSeason)
    t = None
    for team in teams:
        if team['tid'] == p['tid']:
            if commandSeason == season:
                t = tinfo(team)
            else:
                t = tinfo(team, commandSeason)
    if t == None:
        t = pull_info.tgeneric(p['tid'], p)
    
    descriptionLine = f"{p['position']}, {p['ovr']}/{p['pot']}, {commandSeason - p['born']} years | #{p['jerseyNumber']}, {t['name']} ({t['record']})"
    if p['skills'] != '': descriptionLine += '\n' + f"*Skills: {p['skills']}*"
    embed = discord.Embed(title=p['name'], description=descriptionLine, color=t['color'])

    #pull together some essential command info to pass along to the command funcs
    commandInfo = {"id": message.guild.id,
                   "season": commandSeason,
                   "commandName": command,
                   "message": message,
                   'fullplayer':fullplayer}
    #uncomment to get a full error message in console
    #print(commandFuncs)
    result = commandFuncs[command](embed, p, commandInfo)
    if asyncio.iscoroutine(result):
        embed = await result
    else:
        embed = result

    #add the bottom parts
    if not command=="trivia" and not command == 'hint' and not command == 'answer':
        if commandSeason == season:
            if p['retired']:
                titles = 0
                for a in p['awards']:
                    if a['type'] == 'Won Championship':
                        titles += 1
                embed.add_field(name=f'Championships: {titles}', value='', inline=False)
            else:
                expText = str(p['contractExp'])
                roEnabled = shared_info.serversList.get(str(message.guild.id), {}).get('rookieoptions') == 'on'
                if roEnabled and fullplayer and fullplayer.get('contract', {}).get('rookie') and fullplayer.get('draft', {}).get('round') == 1:
                    expText += '+RO'
                contract = f"${p['contractAmount']}M/{expText}"
                injury = p['injury'][0]
                if p['injury'][0] != "Healthy":
                    injury += f" (out {p['injury'][1]} more games)"
                embed.add_field(name=f"Contract: {contract}", value=injury, inline=False)
        else:
            embed.add_field(name=f"Playoffs: {pull_info.playoff_result(t['roundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], commandSeason)}", value=p['awards'], inline=False)

    embed.set_footer(text=shared_info.embedFooter(message.guild))

    gc = ["proggraph","progspredict",'cschart','schart']
    if command in gc:
        do = True
        for fi in embed.fields:
            if fi.name.startswith("Error"):
                do = False
        if do:
            if command == "progspredict":
                embed.set_footer(text="Based on a sample of over 220 years worth of player progressions")
            f = open("first_figure.png",'rb')
            await message.channel.send("Your graph", file = discord.File(f))
            f.close()
    save = ['addrating']
    if command in save:
        path_to_file = data_path(f'exports/{commandInfo["id"]}-export.json')
        await basics.save_db(exports[str(commandInfo['id'])],path_to_file)
        for player in players:
            if player['pid'] == playerPid:
                p = player
        p = pinfo(p)
        descriptionLine = f"{p['position']}, {p['ovr']}/{p['pot']}, {commandSeason - p['born']} years | #{p['jerseyNumber']}, {t['name']} ({t['record']})"
        embed.description = descriptionLine
    await message.channel.send(embed=embed)



