import shared_info
exports = shared_info.serverExports
serversList = shared_info.serversList
import pull_info
import coach_commands
import discord

commandFuncs = {
    'coaches': coach_commands.coaches,
    'hirecoach': coach_commands.hirecoach,
    'firecoach': coach_commands.firecoach,
}


async def process_text(text, message):
    export = shared_info.serverExports[str(message.guild.id)]
    season = export['gameAttributes']['season']
    teams = export['teams']
    try:
        userTid = serversList[str(message.guild.id)]['teamlist'][str(message.author.id)]
    except Exception:
        userTid = -1000

    t = None
    for team in teams:
        if team['tid'] == userTid:
            t = pull_info.tinfo(team)
    if t is None:
        t = pull_info.tgeneric(-1)

    command = str.lower(text[0])
    embed = discord.Embed(title='Coaches', description=f"{season} season", color=t['color'])

    commandInfo = {
        "userTid": userTid,
        "serverId": str(message.guild.id),
        "userId": str(message.author.id),
        "message": message
    }

    embed = await commandFuncs[command](embed, text, commandInfo)
    if embed is None:
        embed = discord.Embed(title='Coaches', description=f"{season} season", color=t['color'])
        embed.add_field(name='No output', value=f'The `{command}` command did not return a result.', inline=False)

    embed.set_footer(text=shared_info.embedFooter(message.guild))
    await message.channel.send(embed=embed)
