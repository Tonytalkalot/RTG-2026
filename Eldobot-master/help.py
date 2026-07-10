import shared_info
exports = shared_info.serverExports
import basics
import pull_info
import discord
import commands


#HELP SCREENS

quickstartScreen = {
    'load [URL]': 'Load a BBGM export file to the bot',
    'roster': 'View your team roster',
    'standings': 'League standings',
    'stats [player]': 'Player season stats',
    'bio [player]': 'Player biography and info',
    'offer [player] [amount]/[years]': 'Offer a contract to a free agent',
    'lineup': 'View your current lineup',
    'lmove [player] [spot]': 'Move a player in the lineup',
    'help [category]': 'Browse commands by category'
}

playerScreen = {
    'stats': 'Season stats',
    'bio': 'Biography and basic info',
    'ratings': 'Current ratings breakdown',
    'adv': 'Advanced statistics (PER, VORP, BPM, etc.)',
    'hstats': 'Historical statlines for each season',
    'cstats': 'Total career stats',
    'progs': 'Progression charts by season',
    'awards': 'Awards and accolades',
    'pgamelog': 'Game-by-game log',
    'shots': 'Shot profile and percentages',
    'nbacomp': 'AI comparison to real NBA players',
    'scout': 'AI scouting report',
    'synergy': 'Player synergy ratings with teammates',
    'composites': 'Composite rating breakdowns',
    'lcomplete': 'Lineup completion value',
    'whoidolizes': 'Players who idolize this player',
    'contracthistory': 'Contract history across seasons',
    'compare': 'Find statistical comparisons',
    'pcompare': 'Side-by-side player comparison',
    'series': 'Head-to-head playoff series stats',
    'trivia': 'Trivia question about a player for fun',
    'answer [name]': 'Submit your trivia guess',
    'hint': 'Get a hint for the current trivia'
}

teamScreen = {
    'roster': 'Team roster with contracts',
    'sroster': 'Roster with stats instead of contracts',
    'psroster': 'Roster with playoff stats',
    'proster': 'Roster with progression ratings',
    'lineup': 'Current lineup and rotations',
    'picks': 'Draft picks owned',
    'ownspicks': 'Who owns this team\'s original picks',
    'history': 'Franchise history',
    'finances': 'Contracts, cap space, and hype',
    'seasons': 'Season-by-season team history',
    'tstats': 'Team stats for current season',
    'ptstats': 'Team playoff stats',
    'schedule': 'Upcoming schedule',
    'sos': 'Future strength of schedule',
    'gamelog': 'Game results this season',
    'game [#]': 'Game summary and top performers',
    'boxscore [#]': 'Full box score for a game',
    'capspace': 'Cap space breakdown',
    'penalties': 'Trade penalty history',
    'synergylineups [team]': 'Top 5 synergy lineup combos from top 8 players',
    'tscout [team]': 'AI scouting report on a team',
    'tnbacomp [team]': 'Find similar real NBA team-seasons'
}

leagueScreen = {
    'standings': 'Conference standings by win percentage',
    'fa [page]': 'Browse free agents',
    'pr [season]': 'Power rankings',
    'playoffs': 'Playoff bracket for any season',
    'playoffpredict': 'Projected standings and playoff probabilities',
    'matchups [team] [team]': 'Head-to-head matchup comparison',
    'top [rating]': 'League leaders by a specific rating',
    'topall': 'Top players across all ratings',
    'leaders [stat]': 'Statistical leaders for current season',
    'combine [stat]': "This year's draft class combine results (vert, sprint, lane, bench, wonderlic, wingspan, reach, height, weight, fat)",
    'combineall [stat]': 'All-time draft combine records',
    'badge [code]': 'Find players by badge (tp, A, B, Ps, Po, Dp, Di, R, V). Comma-separate for players with all of them',
    'retired [team] [page]': 'Retired players, most recently retired first, with their peak rating. Add a team to show only players who played there',
    'mvp': 'Top 10 MVP candidates',
    'dpoy': 'Top 10 DPOY candidates',
    'injuries': 'Current league injuries',
    'deaths': 'Players who have passed away',
    'summary [season]': 'Full season summary',
    'media': 'Post the phase-appropriate AI media report in this channel (mod only)',
    'media feats [season]': 'Notable performances, all-time single-game ranks, and career milestones (mod only)',
    'draftorder': 'Draft order during draft phase',
    'draft': 'Current draft class overview',
    'specialists': 'Players with extreme rating profiles',
    'mostaverage': 'Most well-rounded players',
    'mostunbalanced': 'Most lopsided rating profiles',
    'sadprogs': 'Biggest progression declines',
    'godprogs': 'Biggest progression jumps',
    'pickvalue': 'Draft pick trade value chart',
    'po': 'Player options league-wide',
    'to': 'Team options league-wide',
    'leaguesynergy [off/def/reb]': 'Starting lineup synergy for every team',
    'leaguebuilds': 'Playstyle distribution across the league'
}

freeAgencyScreen = {
    'offer [player] [amount]/[years]': 'Make an offer to a free agent',
    'bulkoffer': 'Offer multiple players at once',
    'bulkoffermins [pot]': 'Auto-offer mins to top 10 eligible FAs by rating (or potential)',
    'offers': 'View your current offers',
    'deloffer [player]': 'Delete an offer',
    'clearoffers': 'Clear all your offers',
    'viewalloffers': 'View all offers from all teams (mod)',
    'move [player] [priority]': 'Adjust your signing priority list',
    'tosign [number]': 'Set max number of players to sign',
    'resignings': 'View your re-signings',
    'qo': 'Extend qualifying offers for RFA-eligible players',
    'match': 'Match an RFA offer sheet from another team',
    'contractrules': 'View the server\'s contract rules',
    'addrule': 'Add a contract rule (mod)',
    'deleterule': 'Remove a contract rule (mod)'
}

draftScreen = {
    'board': 'View your draft board',
    'add [player]': 'Add a player to your board',
    'remove [player]': 'Remove a player from your board',
    'dmove [player] [spot]': 'Reorder your draft board',
    'clearboard': 'Clear your entire board',
    'bulkadd': 'Add multiple players at once (one per line)',
    'auto': 'Set up an autodraft formula',
    'pick [player]': 'Select a player when on the clock',
    'draft': 'View the current draft class',
    'pausedraft': 'Pause a running draft (mod)'
}

rosterScreen = {
    'lineup': 'View your lineup',
    'lmove [player] [spot]': 'Move a player in the lineup',
    'pt [player] [value]': 'Adjust playing time (use +/- or set a target OVR)',
    'autosort': 'Auto-sort your roster by rating',
    'synergysort': 'Sort roster to maximize synergy',
    'findsynergy': 'Find best synergy combinations',
    'resetpt': 'Reset all playing time adjustments',
    'changepos [player] [pos]': 'Change a player\'s position',
    'release [player]': 'Release a player from the roster'
}

chartScreen = {
    'proggraph [player] [rating]': 'Plot a player\'s rating over their career. Rating is optional (ovr, pot, spd, tp, fg, ft, ins, dnk, stre, jmp, pss, drb, oiq, diq, endu). Example: proggraph LeBron James spd',
    'progspredict [player] [rating] [next]': 'Predict career peak for a player based on similar players. Add "next" to predict next season instead. Example: progspredict Giannis tp',
    'schart [stat] [player1, player2, ...]': 'Plot a stat over time for one or more players (comma-separated). Stats: pts, reb, ast, blk, stl, tp, tov, gp. Add "season" or "year" to change x-axis. Example: schart pts LeBron James, Michael Jordan',
    'cschart [stat] [player1, player2, ...]': 'Cumulative version of schart — tracks all-time totals. Example: cschart pts LeBron James, Kareem',
    'leaguegraph [xstat] [ystat] [season]': 'Scatter plot of all teams by two stats. Defaults to ptdiff vs win%. Use lgoptions to see all stat choices. Example: leaguegraph pts win%',
    'lgoptions': 'List all valid stat options for leaguegraph axes (pts, fg%, tp%, win%, ptdiff, ast, etc.)',
    'rostergraph [xstat] [ystat] [season] [playoff]': 'Scatter plot of all players on a roster by two stats. Defaults to ortg vs drtg. Add "playoff" for playoff stats. Use rgoptions for all choices. Example: rostergraph ppg reb',
    'rgoptions': 'List all valid stat options for rostergraph axes (ppg, reb, ast, ortg, drtg, per, vorp, bpm, etc.)',
    'compare [player] [season]': 'Find the 5 most statistically similar players in league history at the same age. Example: compare Victor Wembanyama',
    'tcompare [team1], [team2]': 'Compare two teams side by side with full stats and roster. Optionally include season years. Example: tcompare Lakers 2016, Celtics 2016',
    'playoffpredict': 'Projected standings and win probabilities'
}

coachesScreen = {
    'coaches': 'List all coaches with their records (hired coaches and anyone with a record)',
    'coaches hired': 'Teams that currently have a coach, with each coach\'s record',
    'coaches available': 'Coaches with a record who are not currently on a team',
    'hirecoach [player]': 'Appoint a retired player as your team\'s coach (GM only)',
    'firecoach': 'Remove your team\'s coach (GM only); their record is kept'
}

modScreen = {
    'settings': 'View and edit all server settings',
    'edit [setting] [value]': 'Change a specific setting',
    'load [URL]': 'Load a BBGM export file',
    'updatexport': 'Upload export to Dropbox',
    'teamlist': 'List teams and assigned GMs',
    'addgm [team] [@user]': 'Assign a GM to a team',
    'removegm [team or @user]': 'Remove a GM assignment',
    'assigngm': 'Auto-assign GMs based on Discord roles',
    'startdraft': 'Begin the automated draft',
    'pausedraft': 'Pause a running draft',
    'runfa': 'Run free agency',
    'autofa': 'Auto-create offers for teams at min roster',
    'runresignings': 'Process all re-signings',
    'autosign': 'Auto-sign for AI-controlled teams',
    'autors': 'Auto re-sign for AI-controlled teams',
    'autocut': 'Auto-release over-roster-limit teams',
    'addrating [player] [amount]': 'Add or subtract rating points',
    'removereleasedplayer': 'Remove a released player\'s contract',
    'removetradepen': 'Remove trade penalty from a team',
    'resetgamestrade': 'Make all players tradeable immediately',
    'reprog': 'Re-run progressions',
    'stripnames': 'Strip real names from export',
    'addredirect': 'Add a command redirect',
    'removeredirect': 'Remove a command redirect',
    'echo [text]': 'Bot echoes your message'
}

helpScreens = {
    'quickstart': {'commands': quickstartScreen, 'description': 'Essential commands to get started as a GM.'},
    'players': {'commands': playerScreen, 'description': 'Look up any player. Provide a name, and optionally a season.'},
    'teams': {'commands': teamScreen, 'description': 'Team info. Defaults to your team, or specify any. Most support a past season.'},
    'league': {'commands': leagueScreen, 'description': 'League-wide standings, leaders, awards, and projections.'},
    'freeagency': {'commands': freeAgencyScreen, 'description': 'Make offers, manage priorities, and handle re-signings.'},
    'fa': {'commands': freeAgencyScreen, 'description': 'Make offers, manage priorities, and handle re-signings.'},
    'draft': {'commands': draftScreen, 'description': 'Build your draft board and make picks.'},
    'roster': {'commands': rosterScreen, 'description': 'Manage your lineup, playing time, and roster moves.'},
    'coaches': {'commands': coachesScreen, 'description': 'Optional, just-for-fun coaches who take on their team\'s record.'},
    'charts': {'commands': chartScreen, 'description': 'Graphs, charts, and data visualization tools.'},
    'mods': {'commands': modScreen, 'description': 'Admin commands. Requires "Manage Messages" permission.'}
}

def build_help_context(prefix):
    """Build full command documentation string for Gemini context."""
    lines = []
    for cat, info in helpScreens.items():
        lines.append(f"\n[{cat.upper()}] - {info['description']}")
        for cmd, desc in info['commands'].items():
            lines.append(f"  {prefix}{cmd} - {desc}")
    # Include aliases so Gemini knows about shortcuts
    alias_lines = [f"{prefix}{alias} → {prefix}{target}" for alias, target in shared_info.commandAliases.items()]
    lines.append(f"\nShortcut aliases: {', '.join(alias_lines)}")
    # Extra context about how the bot works
    lines.append(f"\nKey info:")
    lines.append(f"- Most player commands accept a player name after the command, e.g. {prefix}stats LeBron James")
    lines.append(f"- Most team commands default to your own team, or you can specify a team name")
    lines.append(f"- Many commands accept an optional season number to look up past seasons")
    lines.append(f"- Trades happen in a designated trade channel by typing trade offers directly")
    lines.append(f"- Free agency requires an export to be loaded first with {prefix}load")
    lines.append(f"- Use {prefix}help [category] to browse commands by category")
    lines.append(f"- Chart commands: {prefix}schart needs a stat then player name(s) separated by commas, e.g. {prefix}schart pts LeBron James, Giannis")
    lines.append(f"- Chart commands: {prefix}leaguegraph and {prefix}rostergraph take two stat names as axes, e.g. {prefix}leaguegraph pts win%")
    lines.append(f"- Use {prefix}lgoptions to see valid stats for {prefix}leaguegraph, and {prefix}rgoptions for {prefix}rostergraph")
    lines.append(f"- {prefix}proggraph takes a player name and optional rating abbreviation, e.g. {prefix}proggraph LeBron James spd")
    lines.append(f"- {prefix}tcompare takes two team names separated by a comma, e.g. {prefix}tcompare Lakers, Celtics or {prefix}tcompare Warriors 2016, Warriors 2017")
    return '\n'.join(lines)

async def process_text(text, message):
    prefix = shared_info.serversList[str(message.guild.id)].get('prefix', '-')
    command = str.lower(text[0])

    if len(text) == 1:
        # Show quickstart + category listing
        embed = discord.Embed(
            title='Odle Help',
            description='Here are the essential commands to get you started:'
        )

        # Quickstart commands
        qs_lines = []
        for cmd, desc in quickstartScreen.items():
            qs_lines.append(f"**{prefix}{cmd}** - {desc}")
        embed.add_field(name='Quick Start', value='\n'.join(qs_lines), inline=False)

        # Category listing
        categories = []
        for cat, info in helpScreens.items():
            if cat == 'quickstart':
                continue
            categories.append(f"**{prefix}help {cat}** - {info['description']}")
        embed.add_field(name='All Categories', value='\n'.join(categories), inline=False)

        embed.set_footer(text=shared_info.embedFooter(message.guild))
        await message.channel.send(embed=embed)
    else:
        screen = str.lower(text[1])
        if screen not in helpScreens:
            # Fuzzy match suggestion
            embed = discord.Embed(
                title='Category not found',
                description=f'Try one of: {", ".join(helpScreens.keys())}'
            )
            embed.set_footer(text=shared_info.embedFooter(message.guild))
            await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f'{screen.capitalize()} Commands',
                description=helpScreens[screen]['description']
            )
            lines = []
            for command, descripLine in helpScreens[screen]['commands'].items():
                line = f"**{prefix}{command}**"
                if descripLine != "":
                    line += f" - {descripLine}"
                lines.append(line)
            # Split into fields, keeping each under Discord's 1024 char limit
            current_chunk = []
            current_len = 0
            for line in lines:
                # +1 for the newline separator
                if current_chunk and current_len + len(line) + 1 > 1024:
                    embed.add_field(name='\u200b', value='\n'.join(current_chunk), inline=False)
                    current_chunk = []
                    current_len = 0
                current_chunk.append(line)
                current_len += len(line) + 1
            if current_chunk:
                embed.add_field(name='\u200b', value='\n'.join(current_chunk), inline=False)
            embed.set_footer(text=shared_info.embedFooter(message.guild))
            await message.channel.send(embed=embed)
