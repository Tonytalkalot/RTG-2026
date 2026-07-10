import discord
import basics
import commands
import shared_info
serversList = shared_info.serversList


#SETTINGS
async def process_text(text, message):
    if text[0] == 'settings':
        if len(text) == 1:
            await main_prompt(message)
        else:
            if text[1] == 'fa': 
                await fa_prompt(message)
            elif text[1] == 'fa2': 
                await fa_prompt2(message)
            elif text[1] == 'channels': 
                await channels_prompt(message)
            elif text[1] == 'trade': 
                await trade_prompt(message)
            elif text[1] == 'league': 
                await league_prompt(message)
            elif text[1] == 'draft': 
                await draft_prompt(message)
            else:
                await message.channel.send(f"Unknown settings category: {text[1]}. Valid categories are: channels, draft, fa, fa2, league, and trade.")

    if text[0] == 'editprefix':
        if len(text) == 2:
            await edit_setting(['edit', 'prefix', text[1]], message)
        else:
            await message.channel.send('Please supply a new prefix. Usage: ``-editprefix [new prefix]``')

    if text[0] == 'edit':
        if len(text) == 1:
            await message.channel.send('Please supply a value to edit.')
        else:
            if len(text) == 3:
                await edit_setting(text, message)
            else:
                await message.channel.send('When editing messages, please use the format ``-edit [setting] [new value]``. It looks like you supplied too many values.')

async def main_prompt(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings", description=f"Settings for server {serverName}." + "\n \n" + '**Categories:** `channels`, `draft`, `fa`, `fa2`, `league`, `trade`')
    
    embed.add_field(name='General', value='**Prefix:** ' + serverSettings['prefix'] + '\n' + f'*Edit with {prefix}editprefix [new prefix] or {prefix}edit prefix [new prefix]*', inline=False)
    
    embed.add_field(name='Main Channels', value=f"**Trade Confirmation:** {serverSettings['tradechannel']}" + '\n' + '*Where trade confirmations are sent*' + '\n \n'
                    + f"**FA Channel:** {serverSettings['fachannel']}" + '\n' + '*Where FA signings are posted*' + '\n \n'
                    + f"**Draft Channel:** {serverSettings['draftchannel']}" + '\n' + '*Where draft picks are announced*', inline=False)
    
    embed.add_field(name='Quick Links', value=f'`{prefix}settings channels` - View all channel settings\n'
                    + f'`{prefix}settings fa` - Free agency settings\n'
                    + f'`{prefix}settings trade` - Trade settings\n'
                    + f'`{prefix}settings league` - League settings', inline=False)
    
    embed.set_footer(text=f"Use {prefix}settings [category] to see more settings")
    await message.channel.send(embed=embed)

async def channels_prompt(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings - Channels", description=f"Channel settings for server {serverName}")
    
    embed.add_field(name='Transaction Channels', value=f"**Trade Confirmation:** {serverSettings['tradechannel']}" + '\n' 
                    + f'*Edit with {prefix}edit tradechannel [#channel]*' + '\n \n'
                    + f"**Trade Announcement:** {serverSettings['tradeannouncechannel']}" + '\n' 
                    + f'*Edit with {prefix}edit tradeannouncechannel [#channel]*', inline=False)
    
    embed.add_field(name='Free Agency Channels', value=f"**FA Signings:** {serverSettings['fachannel']}" + '\n' 
                    + f'*Edit with {prefix}edit fachannel [#channel]*' + '\n \n'
                    + f"**Player Releases:** {serverSettings['releasechannel']}" + '\n' 
                    + f'*Edit with {prefix}edit releasechannel [#channel]*', inline=False)
    
    embed.add_field(name='Draft & Other Channels', value=f"**Draft Picks:** {serverSettings['draftchannel']}" + '\n' 
                    + f'*Edit with {prefix}edit draftchannel [#channel]*', inline=False)
    
    embed.add_field(name='Optional Features', value=f"**AI Media:** {serverSettings.get('aimedia', 0) if serverSettings.get('aimedia', 0) != 0 else 'Not set'}" + '\n' 
                    + f'*AI-generated content channel*\n'
                    + f'*Edit with {prefix}edit aimedia [#channel]*', inline=False)
    
    embed.set_footer(text=f"Use {prefix}settings to return to main settings")
    await message.channel.send(embed=embed)

async def fa_prompt(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings - Free Agency (Page 1/2)", description=f"FA Settings for server {serverName}" + '\n' + f"*Use `{prefix}settings fa2` for page 2*")
    
    embed.add_field(name='Basic FA Settings', value=('***Note:** Some settings are pulled directly from the server export file, such as the minimum roster, the salary cap, and the hard cap.*' + '\n' + '\n'
                    + f"**Max Roster:** ``{serverSettings['maxroster']}``" + '\n' + f"*Edit with {prefix}edit maxroster [value]*" + '\n' + '\n'
                    + f"**Holdout %:** ``{serverSettings['holdout']}%``" + '\n' + f"*Minimum % of asking price. Edit with {prefix}edit holdout [%]*" + '\n' + '\n'
                    + f"**Tuodloh %:** ``{serverSettings['tuodloh']}%``" + '\n' + f"*Maximum % of asking price. Edit with {prefix}edit tuodloh [%]*" + '\n' + '\n'
                    + f"**Rookies Count:** ``{serverSettings['rookiescount']}``" + '\n' + f'*Count rookies for max roster. Edit with {prefix}edit rookiescount [on/off]*'))
    
    embed.add_field(name='Market Settings', value=f"**Player/Team Options:** ``{serverSettings['options']}``" + '\n' + f"*Edit with {prefix}edit options [on/off]*" + '\n' + '\n'
                    + f"**Rookie Options:** ``{serverSettings['rookieoptions']}``" + '\n' + f"*Edit with {prefix}edit rookieoptions [on/off]*" + '\n' + '\n'
                    + f"**Open Market:** ``{serverSettings['openmarket']}``" + '\n' + f"*Public bidding wars. Edit with {prefix}edit openmarket [on/off]*" + '\n' + '\n'
                    + f"**Semiopen Market:** ``{serverSettings['semiopenmarket']}``" + '\n' + f"*Show interest levels. Edit with {prefix}edit semiopenmarket [on/off]*" + '\n' + '\n'
                    + f"**Bird Rights:** ``{serverSettings['birdrights']}``" + '\n' + f"*Go over soft cap for own players. Edit with {prefix}edit birdrights [on/off]*")
    
    embed.set_footer(text=f"Page 1 of 2 • Use {prefix}settings fa2 for mood traits and formula settings")
    await message.channel.send(embed=embed)

async def fa_prompt2(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings - Free Agency (Page 2/2)", description=f"FA Settings for server {serverName}" + '\n' + f"*Use `{prefix}settings fa` for page 1*")
    
    embed.add_field(name='Mood Trait Weights', value='*Base weights for FA decisions. Default is 0.1, trait adds 1.0*' + '\n' + '\n'
                    + f"**Winning:** ``{serverSettings['winning']}``" + '\n'
                    + f"**Fame:** ``{serverSettings['fame']}``" + '\n'
                    + f"**Loyalty:** ``{serverSettings['loyalty']}``" + '\n'
                    + f"**Money:** ``{serverSettings['money']}``" + '\n'
                    + f"**Idiosyncratic:** ``{serverSettings['idiosyncratic']}``" + '\n' + '\n'
                    + f"*Edit with {prefix}edit [trait] [weight]*")
    
    embed.add_field(name='Special Rules', value=f"**Restricted FA:** ``{serverSettings['rfa']}``" + '\n'
                    + f"**RFA Multiplier:** ``{serverSettings['rfamultiplier']}``" + '\n' + '\n'
                    + f"**3+ Year Rule:** ``{serverSettings['threeyearrule']}``" + '\n'
                    + f"*3+ year offers need 250% of min salary*" + '\n'
                    + f"*Edit with {prefix}edit threeyearrule [on/off]*")
    
    embed.add_field(name='FA Formula', value=f"**Dynamic FA Formula:** ``{serverSettings.get('dynamicfa', 'off')}``" + '\n' + '\n'
                    + '*When ON:*' + '\n'
                    + '• Prevents 1-year max deal spam' + '\n'
                    + '• Age-based preferences (young want flexibility)' + '\n'
                    + '• Old players value security over money' + '\n'
                    + '• Superstars reject lowballs' + '\n'
                    + '• NPV calculation for contract value' + '\n' + '\n'
                    + f"*Edit with {prefix}edit dynamicfa [on/off]*", inline=False)
    
    embed.set_footer(text=f"Page 2 of 2 • Use {prefix}settings fa for basic settings")
    await message.channel.send(embed=embed)

async def trade_prompt(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings - Trades", description=f"Trade Settings for server {serverName}")
    embed.add_field(name='Trade Settings', value=f"**__Trade Channel:__** {serverSettings['tradechannel']}" + '\n' + f"*This channel will be scanned constantly for trades - all trades should be sent here.. Regular commands will not run in this channel. Edit with {prefix}edit tradechannel [#new channel].*" + '\n'
                    + f"**__Team Can Trade for Player Back Within the Same Season:__** ``{serverSettings['tradeback']}``" + '\n' + f'*If off, teams can not trade for a player who they traded away earlier in the same season. Resets at preseason. Edit with {prefix}edit tradeback [on/off].*' + '\n'
                    + f"**__# of Games Before Trading Signed FA:__** ``{serverSettings['tradefa']}``" + '\n' + f"*Signed FAs must spend this number of days with their team before being eligible for trade. Edit with {prefix}edit tradefa [new number].*" + '\n'
                    + f"**__Mod Approval Required:__** ``{serverSettings.get('tradeapproval', 'off')}``" + '\n' + f"*When on, trades require a mod to confirm in addition to both GMs. Edit with {prefix}edit tradeapproval [on/off].*" + '\n')
    await message.channel.send(embed=embed)

async def league_prompt(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings - League", description=f"General league settings, mostly relating to finances. **Many of these values are fixed according to what is in your export file. Some, however, can be edited.**")
    if str(message.guild.id) in shared_info.serverExports:
        
        embed.add_field(name='Finance Settings', value=f"**Salary Cap:** ${shared_info.serverExports[str(message.guild.id)]['gameAttributes']['salaryCap']/1000}M" + '\n' + '\n'
                        + f"**Hard Cap:** ${serverSettings['hardcap']}M" + '\n' + f'*Teams cannot surpass this payroll for any reason other than draft picks. Edit with {prefix}edit hardcap [new value].*' + '\n' + '\n'
                        + f"**Minimum Contract:** ${shared_info.serverExports[str(message.guild.id)]['gameAttributes']['minContract']/1000}M" + '\n' + f"**Maximum Contract:** ${shared_info.serverExports[str(message.guild.id)]['gameAttributes']['maxContract']/1000}M" + '\n' + '\n'
                        + f"**Minimum Contract Years:** {shared_info.serverExports[str(message.guild.id)]['gameAttributes']['minContractLength']}" + '\n' + f"**Minimum Contract Years:** {shared_info.serverExports[str(message.guild.id)]['gameAttributes']['maxContractLength']}")
    else:
        embed.add_field(name='Finance Settings', value = "Finance settings are based on export values, but export is not in database. To fix this, run a generic command like 'ratings' to force bot database to load your server's export, then run this again.")
    embed.add_field(name='Lineup Settings', value=f"**Max OVR Difference: Starter vs Bench:** {serverSettings['lineupovrlimit']}" + '\n' + f"*A team cannot set a lineup where a bench player is this much OVR higher than a starter. Edit with {prefix}edit lineupovrlimit [new limit].*" + '\n' + '\n'
                    + f"**Max PT Modificiations:** {serverSettings['maxptmod']}" + '\n' + f'*The maximum number of allowed playing time modifications. Edit with {prefix}edit maxptmod [new value].*' + '\n' + '\n'
                    + f"**Max PT Modifier:** {serverSettings['maxptlimit']}" + '\n' + f"**Min PT Modifier:** {serverSettings['minptlimit']}" + '\n' + f"*This regulates the maximum and minimum amounts of modification a GM can do to playing time. With current settings, they cannot increase a player's playing time OVR by more than {(float(serverSettings['maxptlimit'])-1)}% or decrease it to less than {float(serverSettings['minptlimit'])}%. + minutes corresponds to a 25% increase, so 1.25, whereas - corresponds to 75%, so 0.75. Adjust with {prefix}edit maxptlimit or {prefix}edit minptlimit [new max/min modifier].*" + '\n' + '\n'
                    + f"**Max OVR that can be released:** {serverSettings['maxovrrelease']}" + '\n' + f"*Players higher than this rating can not be released. Edit with {prefix}edit maxovrrelease [new OVR].*" + '\n' + '\n'
                    + f"**Position Changes:** {serverSettings.get('poschanges', 'on')}" + '\n' + f"*When off, GMs cannot use {prefix}changepos. Edit with {prefix}edit poschanges [on/off].*")
    await message.channel.send(embed=embed)

async def draft_prompt(message):
    prefix = serversList[str(message.guild.id)]['prefix']
    serverName = message.guild.name
    serverSettings = shared_info.serversList[str(message.guild.id)]
    embed = discord.Embed(title="Odle Settings - Draft", description=f"Settings relating to the draft.")
    embed.add_field(name='Clock Settings', value='Your clock times are set as:' + '\n' + f"``{serverSettings['draftclock']}``" + '\n' + f"Adjust this by using {prefix}edit draftclock [new value]. **You should provide a list of numbers separated by commas, and each number represents the number of seconds of the clock in that round.** Some examples:" + '\n' + f"• ``300,200,0`` - this sets the round one clock to 300 seconds, round two to 200 seconds, and the third round will be autopicked." + '\n' + f"• ``300,0`` - this sets the first round to 300 seconds, and the second round will be auto-picked." + '\n' + '\n' + 'If a value is not specified for a round, it defaults to a 3 minute clock, which is 180 seconds. Setting the time to 0 is perfectly fine and will use boards or formulas to make each pick.')
    await message.channel.send(embed=embed)

async def edit_setting(text, message):
    toEdit = str.lower(text[1])
    newValue = text[2]
    server = str(message.guild.id)
    if toEdit in commands.settingsDirectory:
        valid = commands.settingsDirectory[toEdit](newValue)
        if valid:
            serversList[server][toEdit] = newValue
            await basics.save_db(serversList)
            text = '**Success!** New ' + toEdit + ' set to ' + str(newValue) + '!'
            await message.channel.send(text)
        else:
            text = 'Value ``' + str(newValue) + '`` is invalid.'
            await message.channel.send(text)

    else:
        await message.channel.send('Invalid setting provided. Please check the -settings pages to confirm the setting you are dying to edit.')
