import shared_info
import discord
import analytics_commands as ac

commandFuncs = {
    'calls': ac.calls,
    'mostused': ac.mostusedcommands,
    'leastused': ac.leastusedcommands,
    'mostactive': ac.mostactiveusers,
    'servers': ac.servers
}

async def process_text(text, message):
    command = str.lower(text[0])

    if command == 'echo':
        echo_text = " ".join(message.content.split(" ")[1:])
        try:
            prefix = shared_info.serversList[str(message.guild.id)]['prefix']
        except:
            prefix = '-'
        blocked_prefixes = ['-', '!', '/', '.', '?', '$', '%', '>', '<', '`']
        blocked_prefixes.append(prefix)
        for blocked in blocked_prefixes:
            if echo_text.strip().startswith(blocked):
                await message.channel.send("Error: Cannot echo text that looks like a command.")
                return
        echo_text = echo_text.replace("@", "")
        await message.channel.send(echo_text)
        return

    commandInfo = {"message": message.content, "guild": message.guild}

    embed = discord.Embed(title="Analytics:")
    embed = commandFuncs[command](embed, message.author, commandInfo)
    embed.set_footer(text=shared_info.embedFooter(message.guild))
    await message.channel.send(embed=embed)
