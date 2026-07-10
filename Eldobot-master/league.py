import shared_info
exports = shared_info.serverExports
import basics
import os
import pull_info
from data_dir import data_path
from pull_info import pinfo
from pull_info import tinfo
import discord
import league_commands

##LEAGUE COMMANDS

commandFuncs = {
    'fa': league_commands.fa,
    'draftorder':league_commands.draftorder,
    'specialists':league_commands.specialists,
    'po':league_commands.po,
    'playoffpredict':league_commands.standingspredict,
    'sadprogs':league_commands.sadprogs,
    'godprogs':league_commands.godprogs,
    'draft': league_commands.draft,
    'pr': league_commands.pr,
    'pickvalue':league_commands.pickvalue,
    'matchups': league_commands.matchups,
    'top': league_commands.top,
    'injuries': league_commands.injuries,
    'deaths': league_commands.deaths,
    'leaders': league_commands.leaders,
    'combine': league_commands.combine,
    'combineall': league_commands.combine,
    'retired': league_commands.retired,
    'badge': league_commands.badges,
    'mvp': league_commands.mvp,

    'dpoy': league_commands.dpoy,
    'summary': league_commands.summary,
    'leaguegraph':league_commands.leaguegraph,
    'mostunbalanced':league_commands.mostunbalanced,
    'lgoptions':league_commands.lgoptions,
    'topall':league_commands.topall,
    'standings':league_commands.standings,
    'playoffs':league_commands.playoffs,
    'to':league_commands.to,
    'mostaverage':league_commands.mostaverage,
    'reprog':league_commands.reprog,
    'stripnames':league_commands.stripnames,
    'gmoty':league_commands.gmoty,
    'leaguesynergy':league_commands.leaguesynergy,
    'leaguebuilds':league_commands.leaguebuilds,
    'cola':league_commands.cola,
    'media':league_commands.media,
}
    
async def process_text(text, message):
    export = shared_info.serverExports[str(message.guild.id)]
    season = export['gameAttributes']['season']
    players = export['players']
    teams = export['teams']
    commandSeason = season
    pageNumber = 1
    command = str.lower(text[0])
    for m in text:
        try:
            m = int(m)
            if m > 1500:
                commandSeason = m
            else:
                pageNumber = m
            text.remove(str(commandSeason))
        except:
            pass
    descripLine = str(commandSeason) + ' season'
    if command == 'fa' and season != commandSeason:
        descripLine = f"Page {commandSeason}"
    embed = discord.Embed(title=message.guild.name, description=descripLine)
    commandInfo = {
        'serverId': message.guild.id,
        'message': message,
        'season': commandSeason,
        'pageNumber': pageNumber,
        'text': text
    }
    embed = commandFuncs[command](embed, commandInfo)

    if command != 'gmoty':
        embed.set_footer(text=shared_info.embedFooter(message.guild))
    gc = ["leaguegraph",'pickvalue']
    if command == "reprog" or command == 'stripnames':
        path_to_file = data_path(f'exports/{commandInfo["serverId"]}-export.json')
        await basics.save_db(export, path_to_file)
    await message.channel.send(embed=embed)
    if command in gc:
        waswrong = False
        for field in embed.fields:
            if field.name == "Error":
                waswrong = True
        if not waswrong:
            try:
                f = open("third_figure.png",'rb')
                await message.channel.send("Your graph", file = discord.File(f))
                f.close()
            except Exception:
                 await message.channel.send("There was some kind of mistake")
        
