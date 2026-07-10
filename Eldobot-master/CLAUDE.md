# Claude's Guide to Eldobot Development

## What is Eldobot?

Eldobot is a Discord bot for managing Basketball GM (BBGM) multiplayer leagues. It's a hobby project built for fun to facilitate league management, including drafts, trades, free agency, and statistics tracking. The bot is used by Basketball GM Discord communities to automate and enhance their league experience.

**Tech Stack:**
- Python 3.9.2
- discord.py for Discord integration  
- Plotly for graph generation
- Dropbox API for file sharing
- JSON files for data persistence

**Key Features:**
- League management (import/export BBGM files)
- Automated free agency with bidding system
- Live draft system with autopick
- Trade processing and validation
- Player/team statistics and predictions
- Analytics and usage tracking

## Your Role

You're helping maintain and improve a hobbyist Discord bot. This is a "hacky" project built for fun - code quality varies and perfect isn't the goal. The bot serves trusted Basketball GM communities where security isn't critical.

**What you can do:**
- Fix bugs and add features
- Improve existing functionality
- Help with Discord/BBGM integration issues
- Suggest improvements while respecting the project's casual nature

**What you should know:**
- The codebase has technical debt and that's okay
- Some security issues are known and accepted (eval(), hardcoded tokens)
- Backwards compatibility matters - don't break existing leagues
- User is running this on a Plox deployment with Python 3.9.2

## Workflow

Since this is a hobby project, the workflow is informal:

1. **Understanding requests**: User will describe issues or features needed
2. **Making changes**: Edit files directly, test logic mentally
3. **Committing**: User will test and commit changes when ready
4. **Deployment**: Changes deploy to Plox server running the bot

**Important**: Always consider that this bot is actively used by Basketball GM communities. Don't break existing functionality.

## Project Structure

### Core Files
- `main.py` - Bot entry point, message router, command handler
- `shared_info.py` - Global state, shared variables, command lists
- `basics.py` - Utilities, Dropbox integration, file I/O, eval() formula parser

### Command Modules
- `fa_commands.py` - Free agency (offer, withdraw, match, runfa)
- `draft_commands.py` - Draft system (startdraft, pick, autopick)
- `player_commands.py` - Player info (stats, bio, progressions, ratings)
- `team_commands.py` - Team management (roster, lineup, history)
- `league_commands.py` - League-wide (standings, playoffs, power rankings)
- `trade_functions.py` - Trade processing in trade channels
- `analytics_commands.py` - Analytics/usage tracking commands
- `analytics.py` - Analytics command router

### Data Files
- `servers.json` - Per-server settings and configuration
- `daily.json` - Daily claim tracking
- `/exports/` - BBGM export files

### Config Files
- `token.txt` - Discord bot token
- `dropbox.txt` - Dropbox refresh token
- `openaikey.txt` - OpenAI API key

## Known Issues & Quirks

### Security (Accepted Risks)
- **eval() vulnerability** (basics.py:435) - Used for draft formulas, risk accepted
- **Hardcoded credentials** - Dropbox CLIENT_ID/SECRET in code
- **Plaintext tokens** - Stored in .txt files, no env vars

### Technical Debt
- Inconsistent code style across modules
- Global state in shared_info can cause issues
- Dropbox integration is fragile
- Memory management issues with large exports

### Recent Fixes
- Removed hardcoded admin backdoor
- Fixed semi-open FA to show only offer counts
- Fixed Kaleido to v0.2.1 for graph generation
- Fixed dailyclaim KeyError for missing bot ID

## Common Tasks

### Adding a New Command
1. Add to `commands.commands` dictionary in commands.py
2. Implement function in appropriate `*_commands.py` file
3. Function signature: `async def command_name(text, message)`
4. Use Discord embeds for responses

### Fixing Export Loading Issues
1. Check `shared_info.serverExports[str(guild_id)]`
2. Verify JSON structure matches BBGM export format
3. Look for KeyErrors in player/team data access

### Debugging Free Agency
1. Check `servers.json` for FA settings
2. Verify phase in export (must be correct phase)
3. Check offer priorities and team caps

### Handling Dropbox Errors
1. Verify refresh token in dropbox.txt
2. Check CLIENT_ID/SECRET match your app
3. Use OAuth flow to get new refresh token if needed

## Testing & Deployment

### Local Testing
```bash
python3.9 main.py
```

### Required Files
- `token.txt` - Discord bot token
- `dropbox.txt` - Dropbox refresh token (optional)
- `openaikey.txt` - OpenAI key (optional)
- `servers.json` - Initialize as `{}`

### Common Test Commands
- `-load [export_url]` - Load BBGM export
- `-roster [team]` - Check team roster
- `-standings` - View standings
- `-offer [player] [years] [amount]` - Test FA
- `-servers` - Check analytics/server usage

### Deployment Notes
- Currently on Plox with Python 3.9.2
- Requires packages in requirements.txt
- Chrome not available (affects graph generation)
- File persistence in working directory

## Important Context

This bot serves Basketball GM Discord communities for fun. It's intentionally hacky and that's fine. The communities using it are trusted, so security issues are lower priority than functionality. The bot has evolved organically with features added as needed.

Key principles:
- Fun and functionality over perfect code
- Don't break existing leagues
- Security issues are known and accepted
- It's okay to have technical debt
- The community enjoys the bot despite its quirks