"""AI Media System - Non-blocking content generation for Basketball GM events"""
import asyncio
import shared_info
from gemini_integration import model, build_trade_context
import discord
import google.generativeai as genai

# Stronger model for recaps (flash-lite stays default for trades via gemini_integration.model)
try:
    recap_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Failed to initialize recap model: {e}")
    recap_model = None

def get_num_playoff_rounds(export):
    """Get total number of playoff rounds from export settings"""
    try:
        ps = export['gameAttributes']['numGamesPlayoffSeries']
        season = export['gameAttributes']['season']
        if len(ps) == 0:
            return 0
        if isinstance(ps[0], int):
            return len(ps)
        # It's a list of objects with start/value
        total_rounds = 4  # default
        for p in ps:
            start = p.get('start', 0) or 0
            if start <= season:
                total_rounds = len(p['value'])
        return total_rounds
    except Exception:
        return 4  # safe default

def get_team_top_players(export, tid, season, count=3):
    """Get top N players for a team with name, pos, ovr, age"""
    players = export['players']
    roster = []
    for p in players:
        if p['tid'] == tid and p.get('ratings'):
            r = p['ratings'][-1]
            for rating in p['ratings']:
                if rating['season'] == season:
                    r = rating
                    break
            age = season - p['born']['year']
            name = f"{p['firstName']} {p['lastName']}"
            roster.append((r['ovr'], name, r.get('pos', '?'), r['ovr'], r.get('pot', 0), age))
    roster.sort(key=lambda x: x[0], reverse=True)
    return [f"{name} ({pos}, {ovr}/{pot}, {age}yo)" for _, name, pos, ovr, pot, age in roster[:count]]

def get_stat_leaders(export, season, stat_name, count=5, min_gp=10):
    """Get top N players by a per-game stat for the season"""
    players = export['players']
    teams = export['teams']
    leaders = []
    per_game_stats = ['pts', 'ast', 'stl', 'blk', 'tov', 'min']

    for p in players:
        if p['tid'] < 0 or not p.get('stats'):
            continue
        for s in p['stats']:
            if s['season'] == season and not s.get('playoffs', False) and s.get('gp', 0) >= min_gp:
                gp = s['gp']
                if stat_name == 'reb':
                    value = (s.get('orb', 0) + s.get('drb', 0)) / gp
                elif stat_name in per_game_stats:
                    value = s.get(stat_name, 0) / gp
                else:
                    value = s.get(stat_name, 0)

                team = next((t for t in teams if t['tid'] == p['tid']), None)
                team_name = f"{team['region']} {team['name']}" if team else "FA"
                name = f"{p['firstName']} {p['lastName']}"
                leaders.append({
                    'name': name, 'team': team_name, 'value': round(value, 1),
                    'gp': gp, 'pos': p['ratings'][-1].get('pos', '?') if p.get('ratings') else '?'
                })
                break

    leaders.sort(key=lambda x: x['value'], reverse=True)
    return leaders[:count]

def get_team_cap_info(export, tid):
    """Get payroll and cap space for a team"""
    salary_cap = export['gameAttributes'].get('salaryCap', 90000)
    payroll = 0
    for p in export['players']:
        if p['tid'] == tid:
            payroll += p['contract']['amount']
    cap_space = (salary_cap - payroll) / 1000
    return {'payroll': round(payroll / 1000, 1), 'cap_space': round(cap_space, 1)}

def get_expiring_contracts(export, tid, season):
    """Get players on a team with expiring contracts"""
    expiring = []
    for p in export['players']:
        if p['tid'] == tid and p['contract']['exp'] == season:
            r = p['ratings'][-1] if p.get('ratings') else {}
            expiring.append({
                'name': f"{p['firstName']} {p['lastName']}",
                'pos': r.get('pos', '?'), 'ovr': r.get('ovr', 0), 'pot': r.get('pot', 0),
                'age': season - p['born']['year'],
                'salary': round(p['contract']['amount'] / 1000, 1)
            })
    expiring.sort(key=lambda x: x['ovr'], reverse=True)
    return expiring

def get_team_position_breakdown(export, tid):
    """Get roster position distribution for a team"""
    positions = {}
    for p in export['players']:
        if p['tid'] == tid and p.get('ratings'):
            pos = p['ratings'][-1].get('pos', '?')
            positions[pos] = positions.get(pos, 0) + 1
    return positions

def get_team_offensive_defensive_stats(export, tid, season):
    """Get team PPG, opponent PPG, and point differential"""
    team = next((t for t in export['teams'] if t['tid'] == tid), None)
    if not team:
        return None
    for s in team.get('stats', []):
        if s['season'] == season and not s.get('playoffs', False):
            gp = s.get('gp', 1) or 1
            return {
                'ppg': round(s.get('pts', 0) / gp, 1),
                'opp_ppg': round(s.get('oppPts', 0) / gp, 1),
                'diff': round((s.get('pts', 0) - s.get('oppPts', 0)) / gp, 1)
            }
    return None

def get_active_teams(export):
    """Filter out ghost teams (teams with zero players on roster)"""
    player_counts = {}
    for p in export['players']:
        if p['tid'] >= 0:
            player_counts[p['tid']] = player_counts.get(p['tid'], 0) + 1
    return [t for t in export['teams'] if player_counts.get(t['tid'], 0) > 0]

async def safe_recap_call(prompt, max_retries=1):
    """Wrapper for recap Gemini calls using the stronger flash model"""
    use_model = recap_model or model
    if not use_model:
        return None
    for attempt in range(max_retries):
        try:
            result = await asyncio.wait_for(
                asyncio.create_task(use_model.generate_content_async(prompt)),
                timeout=30.0
            )
            return result.text.strip()
        except asyncio.TimeoutError:
            print(f"Recap model timeout on attempt {attempt + 1}")
        except Exception as e:
            print(f"Recap model error: {e}")
    return None

def get_ai_channel(guild_id):
    """Safely get AI channel ID, return None if invalid"""
    try:
        serversList = shared_info.serversList
        channel_setting = serversList.get(str(guild_id), {}).get('aimedia', 0)
        # Check if not set or is default value
        if not channel_setting or channel_setting == 0:
            return None
        # Handle both string format <#123> and direct ID
        if isinstance(channel_setting, str):
            channel_id = int(str(channel_setting).replace('<#', '').replace('>', ''))
        else:
            channel_id = int(channel_setting)
        return channel_id
    except Exception as e:
        print(f"Error getting AI channel: {e}")
        return None

async def safe_gemini_call(prompt, attempts=2, timeout=25.0):
    """Wrapper for Gemini calls with timeout and retry.

    Defaults tuned for interactive commands (-tscout, -tnbacomp, etc.) where
    the user is waiting on the response — Gemini Flash routinely takes
    10-15s for a structured prompt, occasionally up to 20s. Background
    callers that want to fail fast can pass attempts=1, timeout=8.0.
    """
    if not model:
        return None

    for attempt in range(attempts):
        try:
            result = await asyncio.wait_for(
                asyncio.create_task(model.generate_content_async(prompt)),
                timeout=timeout
            )
            return result.text.strip()
        except asyncio.TimeoutError:
            print(f"Gemini timeout on attempt {attempt + 1}/{attempts} (timeout={timeout}s)")
        except Exception as e:
            print(f"Gemini error: {e}")
    return None

# ============= TRADE ANALYSIS =============

async def generate_trade_brief(tradeData, export):
    """Model 1: Extract clean facts from trade data - no opinions, just facts"""
    if not model:
        return None
    
    context = build_trade_context(tradeData, export)
    season = export['gameAttributes']['season']
    
    # Build structured prompt for fact extraction
    # Include actual player names from trade to prevent hallucination
    traded_player_names = context.get('player_names', [])
    
    prompt = f"""Extract facts from this Basketball GM trade data. Output ONLY factual information, no opinions.

This is year {season} in a Basketball GM simulation. 

THE ONLY PLAYERS THAT EXIST are those listed below. There are NO other players in existence.

DRAFT PICK VALUE GUIDE:
- 3-4 first-round picks = Superstar value
- 3 first-round picks = High-end prospect/All-Star value
- 2 first-round picks = All-Star value
- 1 first-round pick = Starter value
- Multiple second-round picks = Bench/role player value

TRADE DATA:
{context['summary']}

CONTEXT:
{context['analysis']}

ROSTERS:
{context.get('rosters', '')}

STANDINGS:
{context.get('standings', '')}

THESE ARE THE ONLY PLAYERS IN THIS TRADE: {', '.join(traded_player_names) if traded_player_names else 'Extract from data above'}

Create a structured brief with EXACTLY this format:

YEAR: {season}

TRADE SUMMARY:
- [Team name] sends: [List each player with position, role, age, salary] + [List all draft picks explicitly]
- [Team name] sends: [List each player with position, role, age, salary] + [List all draft picks explicitly]

TEAM SITUATIONS:
- [Team 1]: [Win-Loss record], [Standing in conference], Key players: [List top 2 with positions and roles]
- [Team 2]: [Win-Loss record], [Standing in conference], Key players: [List top 2 with positions and roles]

KEY CONTEXT:
- [3-4 bullet points about team needs, cap situation, competitive window BASED ON DATA]

PLAYER NAMES IN THIS TRADE:
[List ONLY the actual player names from the trade data above - DO NOT INVENT NAMES]

CRITICAL RULES:
- Use ONLY information from the data provided above
- DO NOT create or imagine player names
- Focus on the specific players in this trade
- Copy player names EXACTLY as shown in the data
- If you cannot find a piece of information, write "Unknown" instead of guessing"""
    
    try:
        result = await safe_gemini_call(prompt)
        return result
    except Exception as e:
        print(f"Brief generation error: {e}")
        return None

def validate_trade_brief(brief, export, tradeData):
    """Basic validation - just check brief exists and has correct year"""
    if not brief:
        return False, "No brief generated"
    
    # Check year is correct
    season = export['gameAttributes']['season']
    if str(season) not in brief:
        return False, f"Year mismatch - should be {season}"
    
    # CRITICAL: Verify player names in brief actually exist in the export
    players = export.get('players', [])
    
    # Build list of all real player names from export
    real_player_names = set()
    for p in players:
        if 'firstName' in p and 'lastName' in p:
            full_name = f"{p['firstName']} {p['lastName']}"
            real_player_names.add(full_name)
    
    # Extract player names mentioned in the brief
    import re
    # Look for the PLAYER NAMES section
    player_section = re.search(r'PLAYER NAMES IN THIS TRADE:(.*?)$', brief, re.DOTALL)
    if player_section:
        names_text = player_section.group(1)
        mentioned_names = [name.strip() for name in re.split(r'[,\n]', names_text) if name.strip() and len(name.strip()) > 3]
        
        # Verify each mentioned name exists in the export
        for name in mentioned_names:
            if name not in real_player_names:
                # Check if it might be a partial match (sometimes AI might use nicknames)
                found = False
                for real_name in real_player_names:
                    if name in real_name or real_name in name:
                        found = True
                        break
                
                if not found:
                    return False, f"Model 1 hallucinated player: {name}"
    
    # Also check the trade involves real teams
    teams = export.get('teams', [])
    team_names = set()
    for t in teams:
        team_names.add(t.get('abbrev', ''))
        team_names.add(f"{t.get('region', '')} {t.get('name', '')}")
    
    # Basic check that at least some team names appear in brief
    found_team = False
    for team in team_names:
        if team and team in brief:
            found_team = True
            break
    
    if not found_team:
        return False, "No valid team names found in brief"
    
    return True, "Valid"

async def generate_analysis_from_brief(brief, personality_style):
    """Model 2: Take clean brief and make it entertaining"""
    if not model or not brief:
        return None
    
    # Extract player names from brief to whitelist them
    import re
    player_section = re.search(r'PLAYER NAMES IN THIS TRADE:(.*?)$', brief, re.DOTALL)
    allowed_names = []
    if player_section:
        names_text = player_section.group(1)
        # Extract names (assume they're listed one per line or comma separated)
        allowed_names = [name.strip() for name in re.split(r'[,\n]', names_text) if name.strip()]
    
    prompt = f"""You are analyzing a trade in a simulated basketball league.

WRITING STYLE: {personality_style}

IMPORTANT: Use ONLY the information in the brief below. Do not add any information not explicitly stated.

BRIEF TO ANALYZE:
{brief}

Write an entertaining trade analysis (1500 characters MAX) with this structure:

**🔥 TRADE ALERT: [Team1] - [Team2]**

[Catchy opening line about the trade]

[Quick summary - who traded what, INCLUDING draft picks. Mention if significant draft capital was exchanged]

**[Team 1]: [Grade A-F]**
[Why they did it, how player fits their system. If they gave up picks, was it worth it? If they got picks, are they rebuilding? Describe playing style, NOT ratings. Use terms like "floor spacer", "rim protector", "playmaker", "defensive anchor", "scoring threat"]

**[Team 2]: [Grade A-F]**  
[Why they did it, how player fits their needs. Consider draft picks given/received. Focus on basketball skills and fit, not numbers]

[End with ONE bold prediction about how this trade impacts the teams]

REMEMBER - Draft picks matter:
- Multiple first-rounders = major asset
- Giving up 3+ firsts = going all-in
- Getting multiple firsts = rebuilding/asset accumulation

CRITICAL RULES:
- Use ONLY information from the brief above - do not invent details
- NEVER mention OVR, ratings, or overall numbers
- Describe players by their role (star, starter, rotation player)
- Focus on team fit and basketball strategy
- Keep it under 1500 characters
- Write about THIS trade with THESE specific players only"""
    
    try:
        result = await safe_gemini_call(prompt)
        return result
    except Exception as e:
        print(f"Analysis generation error: {e}")
        return None

def validate_final_output(output, allowed_names):
    """Simple validation - just check output exists"""
    return bool(output)  # Just ensure we have some output

async def generate_trade_analysis_async(export, tradeData, guild_id):
    """Generate trade analysis using two-model chain to prevent hallucinations"""
    try:
        # Get channel first - fail fast if no channel
        channel_id = get_ai_channel(guild_id)
        if not channel_id:
            print(f"No AI channel configured for guild {guild_id}")
            return
        
        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            print(f"AI channel {channel_id} not found")
            return
        
        # PHASE 1: Generate clean brief with Model 1
        print("Phase 1: Generating trade brief...")
        brief = await generate_trade_brief(tradeData, export)
        
        if not brief:
            print("Failed to generate trade brief")
            return
        
        # Validate the brief
        is_valid, message = validate_trade_brief(brief, export, tradeData)
        if not is_valid:
            print(f"Brief validation failed: {message}")
            # Try once more with stricter prompt
            brief = await generate_trade_brief(tradeData, export)
            is_valid, message = validate_trade_brief(brief, export, tradeData)
            if not is_valid:
                print(f"Brief regeneration failed: {message}")
                return
        
        print("Brief validated successfully")
        
        # Extract player names from brief for final validation
        import re
        player_section = re.search(r'PLAYER NAMES IN THIS TRADE:(.*?)$', brief, re.DOTALL)
        allowed_names = []
        if player_section:
            names_text = player_section.group(1)
            allowed_names = [name.strip() for name in re.split(r'[,\n]', names_text) if name.strip()]
        
        # Choose personality
        import random
        personalities = [
            'You are a hot take artist. Be bold and controversial. Use phrases like "highway robbery", "fleeced", "what were they thinking?", "steal of the century"',
            'You are a basketball analyst. Focus on fit and roles. Use terms like "floor spacing", "two-way player", "defensive liability", "offensive hub", "glue guy"',
            'You are a comedy writer. Use funny analogies and witty observations. Compare trades to everyday situations, use pop culture references.',
            'You are an old-school scout. Focus on intangibles. Use phrases like "high motor", "basketball IQ", "locker room presence", "winning player", "empty stats"'
        ]
        
        personality = random.choice(personalities)
        
        # PHASE 2: Generate entertaining analysis with Model 2
        print("Phase 2: Generating entertaining analysis...")
        content = await generate_analysis_from_brief(brief, personality)
        
        if not content:
            print("Failed to generate analysis")
            return
        
        # Final validation
        if allowed_names and not validate_final_output(content, allowed_names):
            print("Output validation failed - attempting regeneration")
            # Try once more with even stricter prompt
            strict_personality = personality + " CRITICAL: You previously used wrong names. Use ONLY names from the brief."
            content = await generate_analysis_from_brief(brief, strict_personality)
            
            if not content or not validate_final_output(content, allowed_names):
                print("Final regeneration failed")
                return
        
        # Ensure it fits in embed
        if content and len(content) > 4090:
            content = content[:4087] + "..."
        
        if content:
            # Create embed for better formatting
            embed = discord.Embed(
                title="📊 Trade Analysis",
                description=content,
                color=discord.Color.blue()
            )
            
            await channel.send(embed=embed)
            print(f"Successfully posted trade analysis to guild {guild_id}")
    except Exception as e:
        print(f"Trade analysis generation failed: {e}")
        # Silent fail - no user-facing error

def fire_and_forget_trade_analysis(export, tradeData, guild_id):
    """Non-blocking wrapper - returns immediately"""
    asyncio.create_task(generate_trade_analysis_async(export, tradeData, guild_id))

# ============= FA & PROGRESSIONS RECAP - REMOVED =============
# Preseason FA recap functionality has been removed per user request

# ============= SEASON/PLAYOFF RECAP =============

async def generate_season_recap_async(export, guild_id, channel_id=None):
    """Generate season recap when playoffs end"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        season = export['gameAttributes']['season']
        events = export.get('events', [])
        teams = get_active_teams(export)

        # Find champion
        champion_event = None
        for event in reversed(events):
            if event.get('type') == 'playoffs' and 'champion' in event.get('text', '').lower():
                champion_event = event
                break

        # Get awards
        awards_text = "Awards information not available"
        for event in reversed(events):
            if event.get('type') == 'awards' and event.get('season') == season:
                awards_text = event.get('text', '')
                break

        # Get team records with tid for player lookups
        team_records = []
        for t in teams:
            if 'seasons' in t and len(t['seasons']) > 0:
                last_season = t['seasons'][-1]
                team_records.append({
                    'name': f"{t['region']} {t['name']}",
                    'abbrev': t['abbrev'],
                    'tid': t['tid'],
                    'won': last_season.get('won', 0),
                    'lost': last_season.get('lost', 0),
                    'playoffs': last_season.get('playoffRoundsWon', 0)
                })

        team_records.sort(key=lambda x: x['won'], reverse=True)

        # Find the champion and the runner-up
        total_rounds = get_num_playoff_rounds(export)
        champion = None
        runner_up = None
        first_round_exits = []
        for t in team_records:
            if t['playoffs'] == total_rounds and t['won'] > 0:
                champion = t
            elif t['playoffs'] == total_rounds - 1 and t['won'] > 0:
                runner_up = t
            elif t['playoffs'] == 0 and t['won'] >= 35:
                first_round_exits.append(t)

        # Best regular season team (might not be champion = choke narrative)
        best_record = team_records[0] if team_records else None
        best_record_choked = best_record and champion and best_record['tid'] != champion['tid']

        prompt = f"""You are a dramatic sports columnist writing the definitive {season} season recap.

THE CHAMPION:
"""
        if champion:
            champ_players = get_team_top_players(export, champion['tid'], season)
            prompt += f"{champion['name']} ({champion['won']}-{champion['lost']}) — {', '.join(champ_players)}\n"
        if runner_up:
            ru_players = get_team_top_players(export, runner_up['tid'], season)
            prompt += f"Finals loser: {runner_up['name']} ({runner_up['won']}-{runner_up['lost']}) — {', '.join(ru_players)}\n"

        if champion_event:
            prompt += f"Championship event: {champion_event.get('text', 'Unknown')}\n"

        if best_record_choked:
            br_players = get_team_top_players(export, best_record['tid'], season)
            prompt += f"\nBEST RECORD BUT DIDN'T WIN IT ALL: {best_record['name']} ({best_record['won']}-{best_record['lost']}) — {', '.join(br_players)}\n"

        if first_round_exits:
            prompt += "\nFIRST ROUND EXITS (biggest disappointments):\n"
            for t in first_round_exits[:3]:
                t_players = get_team_top_players(export, t['tid'], season)
                prompt += f"- {t['name']} ({t['won']}-{t['lost']}) — {', '.join(t_players)}\n"

        prompt += f"\nAWARDS: {awards_text}\n"

        # Conference finals matchups
        conf_finals = [t for t in team_records if t['playoffs'] >= total_rounds - 2]
        if conf_finals:
            prompt += "\nCONFERENCE FINALISTS:\n"
            for t in conf_finals:
                result = "CHAMPION" if t['playoffs'] == total_rounds else "Finals" if t['playoffs'] == total_rounds - 1 else "Conf Finals"
                t_players = get_team_top_players(export, t['tid'], season)
                prompt += f"- {t['name']} ({t['won']}-{t['lost']}, {result}) — {', '.join(t_players)}\n"

        # Stat leaders
        scoring = get_stat_leaders(export, season, 'pts', count=1, min_gp=20)
        assists = get_stat_leaders(export, season, 'ast', count=1, min_gp=20)
        rebounds = get_stat_leaders(export, season, 'reb', count=1, min_gp=20)
        per_leader = get_stat_leaders(export, season, 'per', count=1, min_gp=20)

        if scoring or assists or rebounds or per_leader:
            prompt += "\nSTAT LEADERS:\n"
            if scoring:
                s = scoring[0]
                prompt += f"Scoring champion: {s['name']} ({s['team']}) — {s['value']} PPG\n"
            if assists:
                s = assists[0]
                prompt += f"Assists leader: {s['name']} ({s['team']}) — {s['value']} APG\n"
            if rebounds:
                s = rebounds[0]
                prompt += f"Rebounds leader: {s['name']} ({s['team']}) — {s['value']} RPG\n"
            if per_leader:
                s = per_leader[0]
                prompt += f"PER leader: {s['name']} ({s['team']}) — {s['value']} PER\n"

        prompt += f"""
Write an entertaining season recap column (2-3 paragraphs, under 1500 characters). NOT a standings summary. Instead:
- Tell the STORY of this season: the champion's run, who they beat, was it expected or a Cinderella?
- Call out the biggest choke job or upset if the best regular season team didn't win
- Mention award winners and whether they were deserved
- Reference the stat leaders — did the scoring champion's team win it all? Did the PER leader live up to the hype in the playoffs?
- Any first-round exits that are embarrassing given the team's record/talent
- Be dramatic and opinionated, like a real sports columnist

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} SEASON RECAP**"""

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title="🏆 Season Recap",
                description=content,
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"Season recap generation failed: {e}")

def fire_and_forget_season_recap(export, guild_id, channel_id=None):
    """Launch season recap task and return immediately"""
    asyncio.create_task(generate_season_recap_async(export, guild_id, channel_id))

# ============= PLAYOFF PREVIEW =============

async def generate_playoff_preview_async(export, guild_id, channel_id=None):
    """Generate playoff preview when playoffs start"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        teams = get_active_teams(export)
        season = export['gameAttributes']['season']

        # Build team lookup by tid
        team_lookup = {}
        for t in teams:
            if 'seasons' in t and len(t['seasons']) > 0:
                last_season = t['seasons'][-1]
                team_lookup[t['tid']] = {
                    'name': f"{t['region']} {t['name']}",
                    'abbrev': t['abbrev'],
                    'tid': t['tid'],
                    'won': last_season.get('won', 0),
                    'lost': last_season.get('lost', 0),
                    'cid': t.get('cid', 0)
                }

        # Get actual first-round matchups from playoffSeries
        all_matchups = []
        playoff_tids = set()
        playoff_series = export.get('playoffSeries', [])
        for ps in playoff_series:
            if ps['season'] == season and ps.get('series') and len(ps['series']) > 0:
                first_round = ps['series'][0]
                for matchup in first_round:
                    if 'home' in matchup and 'away' in matchup:
                        home_tid = matchup['home']['tid']
                        away_tid = matchup['away']['tid']
                        home_seed = matchup['home'].get('seed', 0)
                        away_seed = matchup['away'].get('seed', 0)
                        if home_tid in team_lookup and away_tid in team_lookup:
                            home = team_lookup[home_tid]
                            away = team_lookup[away_tid]
                            home['seed'] = home_seed
                            away['seed'] = away_seed
                            all_matchups.append((home, away))
                            playoff_tids.add(home_tid)
                            playoff_tids.add(away_tid)

        # Fallback: if no playoffSeries data, guess from records
        if not all_matchups:
            eastern = sorted([t for t in team_lookup.values() if t['cid'] == 0], key=lambda x: x['won'], reverse=True)
            western = sorted([t for t in team_lookup.values() if t['cid'] == 1], key=lambda x: x['won'], reverse=True)
            for conf in [eastern, western]:
                if len(conf) >= 8:
                    for i, seed in enumerate(conf[:8], 1):
                        seed['seed'] = i
                    all_matchups.append((conf[0], conf[7]))
                    all_matchups.append((conf[1], conf[6]))
                    all_matchups.append((conf[2], conf[5]))
                    all_matchups.append((conf[3], conf[4]))
                    for t in conf[:8]:
                        playoff_tids.add(t['tid'])

        # Sort matchups by competitiveness (win gap)
        all_matchups_with_gap = [(a, b, a['won'] - b['won']) for a, b in all_matchups]
        all_matchups_with_gap.sort(key=lambda x: x[2])
        closest_matchups = all_matchups_with_gap[:2]
        biggest_mismatches = all_matchups_with_gap[-2:]

        # Title favorites — top 4 playoff teams by record
        all_playoff = [t for t in team_lookup.values() if t['tid'] in playoff_tids]
        all_playoff.sort(key=lambda x: x['won'], reverse=True)

        players = export['players']

        # Get star player stats for top seeds
        def get_star_stats(tid):
            best_player = None
            best_ovr = 0
            for p in players:
                if p['tid'] == tid and p.get('ratings') and p['ratings'][-1]['ovr'] > best_ovr:
                    best_ovr = p['ratings'][-1]['ovr']
                    best_player = p
            if best_player:
                for s in best_player.get('stats', []):
                    if s['season'] == season and not s.get('playoffs', False) and s.get('gp', 0) > 0:
                        gp = s['gp']
                        return f"{best_player['firstName']} {best_player['lastName']} {s.get('pts',0)/gp:.1f}ppg/{(s.get('orb',0)+s.get('drb',0))/gp:.1f}rpg/{s.get('ast',0)/gp:.1f}apg"
            return None

        prompt = f"""You are a bold, opinionated sports analyst previewing the {season} playoffs.

CHAMPIONSHIP FAVORITES (top 4 overall records):
"""
        for t in all_playoff[:4]:
            top_players = get_team_top_players(export, t['tid'], season)
            od = get_team_offensive_defensive_stats(export, t['tid'], season)
            od_str = f" | {od['ppg']}ppg, {od['opp_ppg']}opp, {od['diff']:+.1f}diff" if od else ""
            star = get_star_stats(t['tid'])
            star_str = f"\n  Star: {star}" if star else ""
            prompt += f"- {t['name']} ({t['won']}-{t['lost']}{od_str}) — {', '.join(top_players)}{star_str}\n"

        prompt += "\nMOST COMPETITIVE FIRST-ROUND MATCHUPS:\n"
        for higher, lower, gap in closest_matchups:
            h_players = get_team_top_players(export, higher['tid'], season, count=2)
            l_players = get_team_top_players(export, lower['tid'], season, count=2)
            h_od = get_team_offensive_defensive_stats(export, higher['tid'], season)
            l_od = get_team_offensive_defensive_stats(export, lower['tid'], season)
            h_diff = f", {h_od['diff']:+.1f}" if h_od else ""
            l_diff = f", {l_od['diff']:+.1f}" if l_od else ""
            prompt += f"- {higher['name']} ({higher['won']}-{higher['lost']}{h_diff}) vs {lower['name']} ({lower['won']}-{lower['lost']}{l_diff}) — gap: {gap} wins\n"
            prompt += f"  {higher['name']}: {', '.join(h_players)} | {lower['name']}: {', '.join(l_players)}\n"

        prompt += "\nBIGGEST MISMATCHES:\n"
        for higher, lower, gap in biggest_mismatches:
            h_players = get_team_top_players(export, higher['tid'], season, count=2)
            l_players = get_team_top_players(export, lower['tid'], season, count=2)
            prompt += f"- {higher['name']} ({higher['won']}-{higher['lost']}) vs {lower['name']} ({lower['won']}-{lower['lost']}) — gap: {gap} wins\n"
            prompt += f"  {higher['name']}: {', '.join(h_players)} | {lower['name']}: {', '.join(l_players)}\n"

        prompt += "\nDARK HORSE / UPSET CANDIDATES (lower seeds):\n"
        lower_seeds = [t for t in all_playoff if t.get('seed', 0) >= 5]
        lower_seeds.sort(key=lambda x: x['won'], reverse=True)
        for t in lower_seeds[:4]:
            top_players = get_team_top_players(export, t['tid'], season, count=2)
            prompt += f"- {t['name']} (#{t.get('seed', '?')} seed, {t['won']}-{t['lost']}) — {', '.join(top_players)}\n"

        prompt += f"""
Write a playoff preview column (2-3 paragraphs, under 1500 characters). NOT a matchup-by-matchup breakdown. Instead:
- Pick your championship favorite and explain why — reference their point differential and star player's stats
- Analyze the most competitive matchup as a style clash: can one team's offense overwhelm the other's defense? Use the PPG/OPP data
- Call out the matchup most likely to produce an upset and why
- Name one dark horse team that could make a deep run
- Make a bold Finals prediction with a specific star player who will lead the way
- Be confident and opinionated, like a TV analyst making picks

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} PLAYOFF PREVIEW**"""

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title="🏀 Playoff Preview",
                description=content,
                color=discord.Color.purple()
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"Playoff preview generation failed: {e}")

def fire_and_forget_playoff_preview(export, guild_id, channel_id=None):
    """Launch playoff preview task and return immediately"""
    asyncio.create_task(generate_playoff_preview_async(export, guild_id, channel_id))

# ============= DRAFT LOTTERY PREVIEW =============

async def generate_draft_lottery_preview_async(export, guild_id, channel_id=None):
    """Generate draft lottery preview with prospects (fires at phase 5)"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        teams = get_active_teams(export)
        players = export['players']
        season = export['gameAttributes']['season']

        # Get draft order
        draft_picks = export.get('draftPicks', [])
        first_round = [dp for dp in draft_picks if dp['round'] == 1 and dp['season'] == season + 1]
        first_round.sort(key=lambda x: x.get('pick', 999))

        # Build rich lottery data
        lottery_teams = []
        for i, pick in enumerate(first_round[:14], 1):
            team = next((t for t in teams if t['tid'] == pick['tid']), None)
            if team:
                team_name = f"{team['region']} {team['name']}"
                record = "0-0"
                if 'seasons' in team and team['seasons']:
                    last = team['seasons'][-1]
                    record = f"{last.get('won', 0)}-{last.get('lost', 0)}"
                # Get young players (under 24) vs veterans
                young = []
                vets = []
                for p in players:
                    if p['tid'] == team['tid'] and p.get('ratings'):
                        r = p['ratings'][-1]
                        age = season - p['born']['year']
                        name = f"{p['firstName']} {p['lastName']}"
                        if age <= 23:
                            young.append(f"{name} ({r['ovr']}, {age}yo)")
                        elif r['ovr'] >= 60:
                            vets.append(f"{name} ({r['ovr']}, {age}yo)")
                young.sort(key=lambda x: x, reverse=True)
                vets.sort(key=lambda x: x, reverse=True)
                # Check if pick is traded (original team != current owner)
                original = pick.get('originalTid', pick['tid'])
                traded_pick = original != pick['tid']
                orig_team_name = ""
                if traded_pick:
                    orig = next((t for t in teams if t['tid'] == original), None)
                    if orig:
                        orig_team_name = f" (via {orig['region']})"

                lottery_teams.append({
                    'pick': i,
                    'name': team_name,
                    'record': record,
                    'young': young[:3],
                    'vets': vets[:2],
                    'traded': traded_pick,
                    'orig_note': orig_team_name
                })

        # Get top draft prospects
        draft_class = []
        for p in players:
            if p['tid'] == -2 and p.get('ratings') and p['draft'].get('year') == season + 1:
                r = p['ratings'][-1]
                age = season - p['born']['year']
                draft_class.append({
                    'name': f"{p['firstName']} {p['lastName']}",
                    'pos': r.get('pos', '?'),
                    'ovr': r['ovr'],
                    'pot': r.get('pot', 0),
                    'age': age
                })
        # Also check current season draft year (depends on phase)
        if not draft_class:
            for p in players:
                if p['tid'] == -2 and p.get('ratings') and p['draft'].get('year') == season:
                    r = p['ratings'][-1]
                    age = season - p['born']['year']
                    draft_class.append({
                        'name': f"{p['firstName']} {p['lastName']}",
                        'pos': r.get('pos', '?'),
                        'ovr': r['ovr'],
                        'pot': r.get('pot', 0),
                        'age': age
                    })
        draft_class.sort(key=lambda x: x['pot'], reverse=True)

        prompt = f"""You are a draft analyst breaking down the {season} draft lottery results.

TOP PROSPECTS AVAILABLE:
"""
        for i, prospect in enumerate(draft_class[:10], 1):
            prompt += f"{i}. {prospect['name']} ({prospect['pos']}, {prospect['ovr']} OVR / {prospect['pot']} POT, {prospect['age']}yo)\n"

        prompt += "\nLOTTERY RESULTS:\n"
        for lt in lottery_teams:
            prompt += f"Pick #{lt['pick']}: {lt['name']}{lt['orig_note']} ({lt['record']})\n"
            if lt['young']:
                prompt += f"  Young core: {', '.join(lt['young'])}\n"
            if lt['vets']:
                prompt += f"  Veterans: {', '.join(lt['vets'])}\n"
            if lt['traded']:
                prompt += f"  NOTE: This pick was traded\n"

        prompt += f"""
Write a draft lottery column (2-3 paragraphs, under 1500 characters). NOT just listing the pick order. Instead:
- Look at the top prospects and which teams are picking where — who's getting a steal? Which prospect is the perfect fit for which team?
- If there's a clear #1 prospect, who's getting them and does that team even need them?
- Which lottery team already has a young core and just needs one more piece vs which is in total rebuild mode?
- If any picks were traded, call out who fleeced whom
- Be opinionated — mock draft the top 3 picks and explain the fits

CRITICAL: You may ONLY reference team names, player names, prospect names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} DRAFT LOTTERY RECAP**"""

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title="🎰 Draft & Offseason Preview",
                description=content,
                color=discord.Color.orange()
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"Draft lottery preview generation failed: {e}")

def fire_and_forget_draft_lottery_preview(export, guild_id, channel_id=None):
    """Launch draft lottery preview task and return immediately"""
    asyncio.create_task(generate_draft_lottery_preview_async(export, guild_id, channel_id))

# ============= DRAFT RESULTS RECAP =============

async def generate_draft_results_recap_async(export, guild_id, channel_id=None):
    """Generate post-draft recap showing actual picks (fires at phase 7)"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        teams = get_active_teams(export)
        players = export['players']
        season = export['gameAttributes']['season']

        # Find all drafted players this season
        drafted = []
        for p in players:
            if p['draft'].get('year') == season and p['draft'].get('tid', -1) != -1:
                r = p['ratings'][-1]
                age = season - p['born']['year']
                draft_tid = p['draft']['tid']
                current_tid = p['tid']
                # Find team names
                draft_team = next((t for t in teams if t['tid'] == draft_tid), None)
                current_team = next((t for t in teams if t['tid'] == current_tid), None)
                draft_team_name = f"{draft_team['region']} {draft_team['name']}" if draft_team else "Unknown"
                current_team_name = f"{current_team['region']} {current_team['name']}" if current_team and current_tid >= 0 else draft_team_name
                was_traded = draft_tid != current_tid and current_tid >= 0

                drafted.append({
                    'name': f"{p['firstName']} {p['lastName']}",
                    'pos': r.get('pos', '?'),
                    'ovr': r['ovr'],
                    'pot': r.get('pot', 0),
                    'age': age,
                    'round': p['draft'].get('round', 1),
                    'pick': p['draft'].get('pick', 0),
                    'draft_team': draft_team_name,
                    'current_team': current_team_name,
                    'was_traded': was_traded
                })

        drafted.sort(key=lambda x: (x['round'], x['pick']))

        # Split into first round and notable later picks
        first_round = [d for d in drafted if d['round'] == 1]
        later_steals = [d for d in drafted if d['round'] > 1 and d['pot'] >= 55]
        later_steals.sort(key=lambda x: x['pot'], reverse=True)

        # Find the biggest "steal" — highest potential picked latest
        biggest_steal = None
        if len(drafted) > 3:
            by_value = sorted(drafted, key=lambda x: x['pot'], reverse=True)
            for prospect in by_value[:3]:
                if prospect['pick'] > 5:
                    biggest_steal = prospect
                    break

        prompt = f"""You are a draft analyst grading the {season} draft.

FIRST ROUND PICKS:
"""
        for d in first_round:
            traded_note = f" (traded to {d['current_team']})" if d['was_traded'] else ""
            prompt += f"Pick #{d['pick']}: {d['name']} ({d['pos']}, {d['ovr']} OVR / {d['pot']} POT, {d['age']}yo) → {d['draft_team']}{traded_note}\n"

        if later_steals:
            prompt += "\nLATER ROUND STEALS (high potential picks after round 1):\n"
            for d in later_steals[:5]:
                prompt += f"Round {d['round']} Pick #{d['pick']}: {d['name']} ({d['pos']}, {d['ovr']} OVR / {d['pot']} POT) → {d['draft_team']}\n"

        if biggest_steal:
            prompt += f"\nBIGGEST STEAL: {biggest_steal['name']} ({biggest_steal['pot']} POT) fell to pick #{biggest_steal['pick']}\n"

        # Show what the top picking teams' rosters look like now with their new additions
        prompt += "\nTOP 3 PICKS — TEAM CONTEXT:\n"
        for d in first_round[:3]:
            team = next((t for t in teams if t['tid'] == d['draft_team'] or f"{t['region']} {t['name']}" == d['current_team']), None)
            if team:
                existing = get_team_top_players(export, team['tid'], season, count=3)
                prompt += f"{d['current_team']}: drafted {d['name']} — existing core: {', '.join(existing)}\n"

        # Re-signing watch — teams with the biggest expiring contracts
        re_sign_watch = []
        for t in teams:
            expiring = get_expiring_contracts(export, t['tid'], season + 1)
            if expiring:
                cap_info = get_team_cap_info(export, t['tid'])
                re_sign_watch.append({
                    'team': f"{t['region']} {t['name']}",
                    'expiring': expiring[:3],
                    'cap_space': cap_info['cap_space']
                })
        re_sign_watch.sort(key=lambda x: x['expiring'][0]['ovr'] if x['expiring'] else 0, reverse=True)

        if re_sign_watch:
            prompt += "\nRE-SIGNING WATCH (biggest expiring contracts):\n"
            for rw in re_sign_watch[:8]:
                exp_str = ', '.join([f"{e['name']} ({e['pos']}, {e['ovr']} OVR, ${e['salary']}M)" for e in rw['expiring']])
                prompt += f"- {rw['team']} (${rw['cap_space']:.1f}M space): {exp_str}\n"

        prompt += f"""
Write a draft recap column (2-3 paragraphs, under 1500 characters). NOT just listing who picked who. Instead:
- Grade the top 3 picks — was it a reach, a steal, or the obvious choice? Do they fit the team's needs?
- Who won draft night? Which team got the best haul?
- Call out any steals in the later rounds — players with high potential who fell
- The draft is done but the offseason isn't — which team faces the toughest re-signing decision? Who's about to lose a key player?
- Be opinionated and entertaining, like a draft night analyst

CRITICAL: You may ONLY reference player names, team names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} DRAFT RECAP**"""

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title="📝 Draft Recap",
                description=content,
                color=discord.Color.dark_green()
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"Draft results recap generation failed: {e}")

def fire_and_forget_draft_results_recap(export, guild_id, channel_id=None):
    """Launch draft results recap task and return immediately"""
    asyncio.create_task(generate_draft_results_recap_async(export, guild_id, channel_id))

# ============= PRESEASON PREVIEW =============

async def generate_preseason_preview_async(export, guild_id, channel_id=None):
    """Generate a preseason preview when a preseason export is loaded (phase 0)"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        teams = get_active_teams(export)
        players = export['players']
        season = export['gameAttributes']['season']

        # Build team data with previous season records for comparison
        all_team_data = []
        for t in teams:
            prev_won = 0
            prev_lost = 0
            prev_playoffs = -1
            if 'seasons' in t and len(t['seasons']) > 0:
                prev = t['seasons'][-1]
                prev_won = prev.get('won', 0)
                prev_lost = prev.get('lost', 0)
                prev_playoffs = prev.get('playoffRoundsWon', -1)

            # Calculate average OVR for current roster
            roster_ovrs = []
            for p in players:
                if p['tid'] == t['tid'] and p.get('ratings'):
                    r = p['ratings'][-1]
                    roster_ovrs.append(r['ovr'])
            roster_ovrs.sort(reverse=True)
            avg_ovr = round(sum(roster_ovrs[:8]) / 8, 1) if len(roster_ovrs) >= 8 else 0

            all_team_data.append({
                'name': f"{t['region']} {t['name']}",
                'abbrev': t['abbrev'],
                'tid': t['tid'],
                'prev_won': prev_won,
                'prev_lost': prev_lost,
                'prev_playoffs': prev_playoffs,
                'avg_ovr': avg_ovr,
                'cid': t.get('cid', 0)
            })

        # Sort by roster strength (avg OVR of top 8)
        all_team_data.sort(key=lambda x: x['avg_ovr'], reverse=True)

        # Find defending champion (skip ghost teams with no real roster)
        total_rounds = get_num_playoff_rounds(export)
        champion = None
        for t in all_team_data:
            if t['prev_playoffs'] == total_rounds and t['avg_ovr'] > 0:
                champion = t
                break

        # Find teams that improved most (new signings, young players developing)
        # We approximate by comparing roster OVR rank vs last season record rank
        by_prev_wins = sorted(all_team_data, key=lambda x: x['prev_won'], reverse=True)
        for i, t in enumerate(by_prev_wins):
            t['prev_rank'] = i + 1
        for i, t in enumerate(all_team_data):
            t['ovr_rank'] = i + 1
            t['rank_jump'] = t['prev_rank'] - t['ovr_rank']  # positive = improved roster

        risers = sorted(all_team_data, key=lambda x: x['rank_jump'], reverse=True)[:3]
        fallers = sorted(all_team_data, key=lambda x: x['rank_jump'])[:3]

        prompt = f"""You are a bold preseason analyst making your {season} season predictions. The season hasn't started yet.

DATA:

STRONGEST ROSTERS (by talent, top 6):
"""
        for i, team in enumerate(all_team_data[:6], 1):
            top_players = get_team_top_players(export, team['tid'], season)
            prev_result = f"{team['prev_won']}-{team['prev_lost']} last yr"
            if team['prev_playoffs'] == total_rounds:
                prev_result += ", DEFENDING CHAMPS"
            elif team['prev_playoffs'] == total_rounds - 1:
                prev_result += ", lost in Finals"
            elif team['prev_playoffs'] >= 1:
                prev_result += ", made playoffs"
            prompt += f"{i}. {team['name']} (avg top-8 OVR: {team['avg_ovr']}, {prev_result}) — {', '.join(top_players)}\n"

        if champion:
            champ_players = get_team_top_players(export, champion['tid'], season)
            prompt += f"\nDEFENDING CHAMPION: {champion['name']} ({champion['prev_won']}-{champion['prev_lost']} last yr) — {', '.join(champ_players)}\n"

        if risers:
            prompt += "\nOFFSEASON WINNERS (biggest roster jumps vs last season's rank):\n"
            for t in risers:
                if t['rank_jump'] > 0:
                    top_players = get_team_top_players(export, t['tid'], season)
                    prompt += f"- {t['name']}: ranked #{t['prev_rank']} last yr by wins → #{t['ovr_rank']} by roster talent now — {', '.join(top_players)}\n"

        if fallers:
            prompt += "\nOFFSEASON LOSERS (roster got worse vs last season's rank):\n"
            for t in fallers:
                if t['rank_jump'] < 0:
                    top_players = get_team_top_players(export, t['tid'], season)
                    prompt += f"- {t['name']}: ranked #{t['prev_rank']} last yr by wins → #{t['ovr_rank']} by roster talent now — {', '.join(top_players)}\n"

        # Find FA signings and separate re-signings from new signings
        # Re-signing events are tagged with the previous season (phase 7 happens before season advances)
        re_signed_pids = set()
        events = export.get('events', [])
        for e in events:
            if e.get('season') in [season, season - 1] and e.get('type') == 'reSigned':
                for pid in e.get('pids', []):
                    re_signed_pids.add(pid)

        new_signings = []
        re_signings = []
        for p in players:
            if p['tid'] >= 0 and p.get('gamesUntilTradable', 0) > 0 and p.get('ratings'):
                r = p['ratings'][-1]
                age = season - p['born']['year']
                team = next((t for t in teams if t['tid'] == p['tid']), None)
                team_name = f"{team['region']} {team['name']}" if team else "Unknown"
                signing = {
                    'name': f"{p['firstName']} {p['lastName']}",
                    'pos': r.get('pos', '?'),
                    'ovr': r['ovr'],
                    'pot': r.get('pot', 0),
                    'age': age,
                    'team': team_name,
                    'salary': round(p['contract']['amount'] / 1000, 1),
                    'years': p['contract']['exp'] - season
                }
                if p['pid'] in re_signed_pids:
                    re_signings.append(signing)
                else:
                    new_signings.append(signing)
        new_signings.sort(key=lambda x: x['ovr'], reverse=True)
        re_signings.sort(key=lambda x: x['ovr'], reverse=True)

        if new_signings:
            prompt += "\nBIGGEST FREE AGENCY SIGNINGS (new team):\n"
            for s in new_signings[:6]:
                prompt += f"- {s['name']} ({s['pos']}, {s['ovr']} OVR / {s['pot']} POT, {s['age']}yo) → {s['team']} (${s['salary']}M, {s['years']}yr)\n"

        if re_signings:
            prompt += "\nKEY RE-SIGNINGS (stayed with their team):\n"
            for s in re_signings[:5]:
                prompt += f"- {s['name']} ({s['pos']}, {s['ovr']} OVR, {s['age']}yo) re-signed with {s['team']} (${s['salary']}M, {s['years']}yr)\n"

        # Offseason trades
        offseason_trades = []
        for e in events:
            if e.get('season') == season and e.get('type') == 'trade':
                offseason_trades.append(e.get('text', ''))
        if offseason_trades:
            prompt += "\nOFFSEASON TRADES:\n"
            for trade_text in offseason_trades[:5]:
                prompt += f"- {trade_text}\n"

        # Weakest rosters
        prompt += "\nWEAKEST ROSTERS (bottom 5):\n"
        for t in all_team_data[-5:]:
            top_players = get_team_top_players(export, t['tid'], season, count=2)
            prompt += f"- {t['name']} (avg top-8 OVR: {t['avg_ovr']}, {t['prev_won']}-{t['prev_lost']} last yr) — {', '.join(top_players)}\n"

        prompt += f"""
Write a preseason predictions column (2-3 paragraphs, under 1500 characters):
- Which new free agency signings are the biggest moves? Who landed the best player and which team overpaid?
- Which re-signing was the smartest move to keep their core together?
- If there were offseason trades, who won the trade?
- Can the defending champ repeat? What's their case for/against?
- Pick your championship favorite and explain why (name players)
- Make a bold prediction: a breakout team, an MVP pick, or a team that disappoints
- Be confident and entertaining, like a preseason TV segment
- ONLY discuss things you have data for — if a section above is empty, skip that topic

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} PRESEASON PREVIEW**"""

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title="🏀 Preseason Preview",
                description=content,
                color=discord.Color.teal()
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"Preseason preview generation failed: {e}")

def fire_and_forget_preseason_preview(export, guild_id, channel_id=None):
    """Launch preseason preview task and return immediately"""
    asyncio.create_task(generate_preseason_preview_async(export, guild_id, channel_id))

# ============= MIDSEASON UPDATE =============

async def generate_midseason_update_async(export, guild_id, channel_id=None):
    """Generate a midseason update during regular season (phase 1/2)"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        teams = get_active_teams(export)
        players = export['players']
        season = export['gameAttributes']['season']
        salary_cap = export['gameAttributes'].get('salaryCap', 90000) / 1000

        # Build team data with current AND previous season records
        all_team_data = []
        for t in teams:
            if 'seasons' in t and len(t['seasons']) > 0:
                last_season = t['seasons'][-1]
                prev_won = 0
                prev_lost = 0
                if len(t['seasons']) > 1:
                    prev = t['seasons'][-2]
                    prev_won = prev.get('won', 0)
                    prev_lost = prev.get('lost', 0)
                # Calculate payroll
                payroll = 0
                for p in players:
                    if p['tid'] == t['tid']:
                        payroll += p['contract']['amount']
                payroll_m = round(payroll / 1000, 1)

                all_team_data.append({
                    'name': f"{t['region']} {t['name']}",
                    'abbrev': t['abbrev'],
                    'tid': t['tid'],
                    'won': last_season.get('won', 0),
                    'lost': last_season.get('lost', 0),
                    'prev_won': prev_won,
                    'prev_lost': prev_lost,
                    'cid': t.get('cid', 0),
                    'payroll': payroll_m
                })

        all_team_data.sort(key=lambda x: x['won'], reverse=True)

        # Calculate games played — use the most common value (mode) for accuracy
        games_played_list = [t['won'] + t['lost'] for t in all_team_data]
        if games_played_list:
            avg_games = max(set(games_played_list), key=games_played_list.count)
        else:
            avg_games = 0

        # Find storylines: biggest risers and fallers vs last season (win pace comparison)
        risers = []
        fallers = []
        if avg_games > 5:
            for t in all_team_data:
                if t['prev_won'] + t['prev_lost'] > 0:
                    prev_wpct = t['prev_won'] / (t['prev_won'] + t['prev_lost'])
                    curr_wpct = t['won'] / (t['won'] + t['lost']) if (t['won'] + t['lost']) > 0 else 0
                    t['wpct_change'] = curr_wpct - prev_wpct
                    if t['wpct_change'] > 0.15:
                        risers.append(t)
                    elif t['wpct_change'] < -0.15:
                        fallers.append(t)
            risers.sort(key=lambda x: x['wpct_change'], reverse=True)
            fallers.sort(key=lambda x: x['wpct_change'])

        # Get total games in season for dynamic thresholds
        num_games = export['gameAttributes'].get('numGames', 82)
        if isinstance(num_games, list):
            num_games = num_games[-1]['value']

        # Determine stage based on games played relative to season length
        if avg_games < num_games * 0.4:
            stage = 'early'
        elif avg_games < num_games * 0.75:
            stage = 'midseason'
        else:
            stage = 'deadline'

        # Find MVP candidates — best player on a top 5 team
        mvp_candidates = []
        for t in all_team_data[:5]:
            top = get_team_top_players(export, t['tid'], season, count=1)
            if top:
                mvp_candidates.append(f"{top[0]} on the {t['name']} ({t['won']}-{t['lost']})")

        # Conference standings for bubble/playoff race
        eastern = [t for t in all_team_data if t['cid'] == 0]
        western = [t for t in all_team_data if t['cid'] == 1]
        eastern.sort(key=lambda x: x['won'], reverse=True)
        western.sort(key=lambda x: x['won'], reverse=True)

        # Bottom teams
        bottom_teams = sorted(all_team_data, key=lambda x: x['won'])[:5]

        # ============ BUILD PROMPT BASED ON STAGE ============

        if stage == 'early':
            # SIM 1: Early season — hot starts, surprises, early MVP talk
            prompt = f"""You are a sports columnist reacting to the early {season} season. Only {avg_games} games in.

DATA:

HOT STARTS (top 5 records):
"""
            for i, team in enumerate(all_team_data[:5], 1):
                top_players = get_team_top_players(export, team['tid'], season)
                prompt += f"{i}. {team['name']} ({team['won']}-{team['lost']}, last yr {team['prev_won']}-{team['prev_lost']}) — {', '.join(top_players)}\n"

            if risers:
                prompt += "\nBIGGEST SURPRISES vs last season:\n"
                for t in risers[:3]:
                    top_players = get_team_top_players(export, t['tid'], season)
                    prompt += f"- {t['name']}: {t['prev_won']}-{t['prev_lost']} last yr → on pace for {t['won']}-{t['lost']} now — {', '.join(top_players)}\n"

            if fallers:
                prompt += "\nALARM BELLS (falling off vs last year):\n"
                for t in fallers[:3]:
                    top_players = get_team_top_players(export, t['tid'], season)
                    prompt += f"- {t['name']}: {t['prev_won']}-{t['prev_lost']} last yr → {t['won']}-{t['lost']} now — {', '.join(top_players)}\n"

            prompt += "\nWORST STARTS:\n"
            for t in bottom_teams:
                top_players = get_team_top_players(export, t['tid'], season, count=2)
                prompt += f"- {t['name']} ({t['won']}-{t['lost']}, last yr {t['prev_won']}-{t['prev_lost']}) — {', '.join(top_players)}\n"

            if mvp_candidates:
                prompt += f"\nEARLY MVP WATCH: {'; '.join(mvp_candidates[:3])}\n"

            # Stat leaders
            min_gp_early = max(3, avg_games // 5)
            scoring = get_stat_leaders(export, season, 'pts', count=3, min_gp=min_gp_early)
            assists = get_stat_leaders(export, season, 'ast', count=3, min_gp=min_gp_early)
            rebounds = get_stat_leaders(export, season, 'reb', count=3, min_gp=min_gp_early)
            if scoring:
                prompt += "\nSTAT LEADERS:\n"
                prompt += "Scoring: " + ', '.join([f"{s['name']} ({s['team']}) {s['value']}ppg" for s in scoring]) + "\n"
                prompt += "Assists: " + ', '.join([f"{s['name']} ({s['team']}) {s['value']}apg" for s in assists]) + "\n"
                prompt += "Rebounds: " + ', '.join([f"{s['name']} ({s['team']}) {s['value']}rpg" for s in rebounds]) + "\n"

            # Rookie watch
            rookies = []
            for p in players:
                if p['tid'] >= 0 and p.get('draft', {}).get('year') == season and p.get('stats'):
                    for s in p['stats']:
                        if s['season'] == season and not s.get('playoffs', False) and s.get('gp', 0) >= 2:
                            gp = s['gp']
                            team = next((t for t in teams if t['tid'] == p['tid']), None)
                            team_name = f"{team['region']}" if team else "?"
                            rookies.append({
                                'name': f"{p['firstName']} {p['lastName']}",
                                'team': team_name,
                                'ppg': round(s.get('pts', 0) / gp, 1),
                                'rpg': round((s.get('orb', 0) + s.get('drb', 0)) / gp, 1),
                                'apg': round(s.get('ast', 0) / gp, 1)
                            })
                            break
            rookies.sort(key=lambda x: x['ppg'], reverse=True)
            if rookies:
                prompt += "\nROOKIE WATCH:\n"
                for r in rookies[:3]:
                    prompt += f"- {r['name']} ({r['team']}) — {r['ppg']}ppg/{r['rpg']}rpg/{r['apg']}apg\n"

            prompt += f"""
Write a short, punchy early season column (2-3 paragraphs, under 1500 characters). It's only {avg_games} games in, so:
- Which hot starts are real and which are fool's gold? Be skeptical of small samples
- Which team's slow start should fans be worried about?
- Early MVP candidate — who's leading the scoring race?
- Which rookie is making the most noise?
- Be bold and fun. It's early so take some risks with your takes

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} EARLY SEASON CHECK-IN**"""

            embed_title = "🔥 Early Season Check-In"
            embed_color = discord.Color.green()

        elif stage == 'midseason':
            # SIM 2: Midseason — MVP race, playoff picture, risers/fallers
            prompt = f"""You are a sports columnist writing a midseason column. {avg_games} games into the {season} season — the picture is getting clearer.

DATA:

TOP 5 OVERALL:
"""
            for i, team in enumerate(all_team_data[:5], 1):
                top_players = get_team_top_players(export, team['tid'], season)
                prompt += f"{i}. {team['name']} ({team['won']}-{team['lost']}, last yr {team['prev_won']}-{team['prev_lost']}) — {', '.join(top_players)}\n"

            if mvp_candidates:
                prompt += f"\nMVP RACE: {'; '.join(mvp_candidates[:3])}\n"

            if risers:
                prompt += "\nBIGGEST RISERS vs last season:\n"
                for t in risers[:3]:
                    top_players = get_team_top_players(export, t['tid'], season)
                    prompt += f"- {t['name']}: {t['prev_won']}-{t['prev_lost']} last yr → {t['won']}-{t['lost']} now — {', '.join(top_players)}\n"

            if fallers:
                prompt += "\nBIGGEST FALLERS vs last season:\n"
                for t in fallers[:3]:
                    top_players = get_team_top_players(export, t['tid'], season)
                    prompt += f"- {t['name']}: {t['prev_won']}-{t['prev_lost']} last yr → {t['won']}-{t['lost']} now — {', '.join(top_players)}\n"

            bubble = eastern[6:10] + western[6:10]
            if bubble:
                prompt += "\nPLAYOFF BUBBLE:\n"
                for t in bubble:
                    top_players = get_team_top_players(export, t['tid'], season, count=1)
                    prompt += f"- {t['name']} ({t['won']}-{t['lost']}) — {', '.join(top_players)}\n"

            # Stat leaders
            scoring = get_stat_leaders(export, season, 'pts', count=5)
            per_leaders = get_stat_leaders(export, season, 'per', count=3)
            if scoring:
                prompt += "\nSCORING RACE:\n"
                for s in scoring:
                    prompt += f"- {s['name']} ({s['team']}) — {s['value']}ppg\n"
            if per_leaders:
                prompt += "\nPER LEADERS: " + ', '.join([f"{s['name']} ({s['value']})" for s in per_leaders]) + "\n"

            # Best offenses and defenses
            team_stats_list = []
            for t in all_team_data:
                od = get_team_offensive_defensive_stats(export, t['tid'], season)
                if od:
                    team_stats_list.append({**t, **od})
            if team_stats_list:
                best_off = sorted(team_stats_list, key=lambda x: x.get('ppg', 0), reverse=True)[:3]
                best_def = sorted(team_stats_list, key=lambda x: x.get('opp_ppg', 0))[:3]
                prompt += "\nBEST OFFENSES: " + ', '.join([f"{t['name']} ({t['ppg']}ppg)" for t in best_off]) + "\n"
                prompt += "BEST DEFENSES: " + ', '.join([f"{t['name']} ({t['opp_ppg']}opp ppg)" for t in best_def]) + "\n"

            # MIP candidates
            mip_candidates = []
            for p in players:
                if p['tid'] >= 0 and p.get('ratings') and len(p['ratings']) >= 2:
                    curr_ovr = p['ratings'][-1]['ovr']
                    prev_ovr = p['ratings'][-2]['ovr']
                    if curr_ovr - prev_ovr >= 5:
                        team = next((t for t in teams if t['tid'] == p['tid']), None)
                        team_name = f"{team['region']}" if team else "?"
                        mip_candidates.append({
                            'name': f"{p['firstName']} {p['lastName']}",
                            'team': team_name,
                            'jump': curr_ovr - prev_ovr,
                            'ovr': curr_ovr
                        })
            mip_candidates.sort(key=lambda x: x['jump'], reverse=True)
            if mip_candidates:
                prompt += "\nMIP CANDIDATES (biggest OVR jump):\n"
                for m in mip_candidates[:3]:
                    prompt += f"- {m['name']} ({m['team']}) — +{m['jump']} OVR (now {m['ovr']})\n"

            prompt += f"""
Write a midseason column (2-3 paragraphs, under 1500 characters). The season is taking shape:
- Who's the MVP frontrunner and why? Reference the scoring race
- Which team's rise or fall is the best story of the season?
- Who's winning MIP? Which team has the best offense or defense?
- The playoff race — who's comfortably in, who's sweating?
- Be opinionated. Have real takes, not just observations

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} MIDSEASON REPORT**"""

            embed_title = "📋 Midseason Report"
            embed_color = discord.Color.blue()

        else:
            # TRADE DEADLINE: Buyers, sellers, trade fits, urgency
            prompt = f"""You are a trade deadline insider. {avg_games} games into the {season} season — the deadline is approaching and GMs are working the phones.

DATA:

CONTENDERS (likely buyers):
"""
            for i, team in enumerate(all_team_data[:6], 1):
                top_players = get_team_top_players(export, team['tid'], season)
                prompt += f"{i}. {team['name']} ({team['won']}-{team['lost']}, payroll ${team['payroll']}M) — {', '.join(top_players)}\n"

            prompt += f"\nSELLERS (bottom teams with tradeable assets):\n"
            for t in bottom_teams:
                top_players = get_team_top_players(export, t['tid'], season, count=3)
                prompt += f"- {t['name']} ({t['won']}-{t['lost']}, payroll ${t['payroll']}M, cap ${salary_cap}M) — assets: {', '.join(top_players)}\n"

            # Bubble teams who might be buyers or sellers
            bubble = eastern[6:10] + western[6:10]
            if bubble:
                prompt += "\nON THE BUBBLE (buy or sell?):\n"
                for t in bubble:
                    top_players = get_team_top_players(export, t['tid'], season, count=2)
                    prompt += f"- {t['name']} ({t['won']}-{t['lost']}, payroll ${t['payroll']}M) — {', '.join(top_players)}\n"

            if mvp_candidates:
                prompt += f"\nMVP FRONTRUNNERS: {'; '.join(mvp_candidates[:3])}\n"

            # Expiring contracts on sellers = trade targets
            prompt += "\nEXPIRING CONTRACTS ON SELLERS:\n"
            for t in bottom_teams:
                expiring = get_expiring_contracts(export, t['tid'], season + 1)
                if expiring:
                    exp_str = ', '.join([f"{e['name']} ({e['pos']}, {e['ovr']} OVR, ${e['salary']}M)" for e in expiring[:3]])
                    prompt += f"- {t['name']}: {exp_str}\n"

            # Contender positional needs
            prompt += "\nCONTENDER NEEDS:\n"
            for t in all_team_data[:6]:
                pos = get_team_position_breakdown(export, t['tid'])
                all_pos = ['PG', 'SG', 'SF', 'PF', 'C']
                weak = [p for p in all_pos if pos.get(p, 0) < 2]
                if weak:
                    prompt += f"- {t['name']}: thin at {', '.join(weak)}\n"

            # Best players on bad teams
            trade_targets = []
            for t in bottom_teams:
                for p in players:
                    if p['tid'] == t['tid'] and p.get('ratings') and p['ratings'][-1]['ovr'] >= 60:
                        r = p['ratings'][-1]
                        trade_targets.append({
                            'name': f"{p['firstName']} {p['lastName']}",
                            'pos': r.get('pos', '?'), 'ovr': r['ovr'],
                            'team': t['name'],
                            'salary': round(p['contract']['amount'] / 1000, 1)
                        })
            trade_targets.sort(key=lambda x: x['ovr'], reverse=True)
            if trade_targets:
                prompt += "\nTOP TRADE TARGETS (best players on bad teams):\n"
                for tt in trade_targets[:5]:
                    prompt += f"- {tt['name']} ({tt['pos']}, {tt['ovr']} OVR, ${tt['salary']}M) on {tt['team']}\n"

            prompt += f"""
Write a trade deadline column (2-3 paragraphs, under 1500 characters). This is about TRADES and MOVES:
- Suggest a specific Player X → Team Y trade that makes sense based on the needs and available targets above
- Which contender has the most obvious hole and which seller has the piece to fill it?
- Which bubble team should go all-in vs blow it up?
- Which seller's best player would be the most coveted trade target?
- Create urgency — the deadline is NOW, GMs need to act
- Be a trade insider with specific opinions on what should happen

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} TRADE DEADLINE BUZZ**"""

            embed_title = "🔔 Trade Deadline Buzz"
            embed_color = discord.Color.red()

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title=embed_title,
                description=content,
                color=embed_color
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"Midseason update generation failed: {e}")

def fire_and_forget_midseason_update(export, guild_id, channel_id=None):
    """Launch midseason update task and return immediately"""
    asyncio.create_task(generate_midseason_update_async(export, guild_id, channel_id))

# ============= FREE AGENCY PREVIEW =============

async def generate_fa_preview_async(export, guild_id, channel_id=None):
    """Generate free agency preview showing top FAs and team needs (phase 8)"""
    try:
        channel_id = channel_id or get_ai_channel(guild_id)
        if not channel_id:
            return

        channel = shared_info.bot.get_channel(channel_id)
        if not channel:
            return

        teams = get_active_teams(export)
        players = export['players']
        season = export['gameAttributes']['season']

        # Get all free agents sorted by OVR
        free_agents = []
        for p in players:
            if p['tid'] == -1 and p.get('ratings'):
                r = p['ratings'][-1]
                age = season - p['born']['year']
                # Get last season stats
                last_stats = None
                for s in reversed(p.get('stats', [])):
                    if s.get('season') in [season, season - 1] and s.get('gp', 0) > 0 and not s.get('playoffs', False):
                        gp = s['gp']
                        ppg = round(s.get('pts', 0) / gp, 1)
                        rpg = round((s.get('orb', 0) + s.get('drb', 0)) / gp, 1)
                        apg = round(s.get('ast', 0) / gp, 1)
                        last_stats = f"{ppg}ppg/{rpg}rpg/{apg}apg"
                        break
                free_agents.append({
                    'name': f"{p['firstName']} {p['lastName']}",
                    'pos': r.get('pos', '?'),
                    'ovr': r['ovr'],
                    'pot': r.get('pot', 0),
                    'age': age,
                    'asking': round(p['contract']['amount'] / 1000, 1),
                    'stats': last_stats
                })
        free_agents.sort(key=lambda x: x['ovr'], reverse=True)

        if not free_agents:
            return

        # Get team cap space and needs
        team_needs = []
        for t in teams:
            cap_info = get_team_cap_info(export, t['tid'])
            pos_breakdown = get_team_position_breakdown(export, t['tid'])
            record = "0-0"
            if t.get('seasons') and t['seasons']:
                last = t['seasons'][-1]
                record = f"{last.get('won', 0)}-{last.get('lost', 0)}"

            all_pos = ['PG', 'SG', 'SF', 'PF', 'C']
            needs = [pos for pos in all_pos if pos_breakdown.get(pos, 0) < 2]

            team_needs.append({
                'name': f"{t['region']} {t['name']}",
                'tid': t['tid'],
                'cap_space': cap_info['cap_space'],
                'payroll': cap_info['payroll'],
                'record': record,
                'needs': needs
            })

        teams_with_space = sorted([t for t in team_needs if t['cap_space'] > 5],
                                  key=lambda x: x['cap_space'], reverse=True)
        no_space = sorted([t for t in team_needs if t['cap_space'] <= 2],
                          key=lambda x: x['cap_space'])

        prompt = f"""You are an NBA free agency insider breaking down the {season} free agent class. Re-signings are done — now the real fun begins.

TOP FREE AGENTS:
"""
        for i, fa in enumerate(free_agents[:12], 1):
            stats_str = f" | Last season: {fa['stats']}" if fa['stats'] else ""
            prompt += f"{i}. {fa['name']} ({fa['pos']}, {fa['ovr']} OVR / {fa['pot']} POT, {fa['age']}yo, asking ${fa['asking']}M){stats_str}\n"

        prompt += "\nTEAMS WITH MOST CAP SPACE:\n"
        for t in teams_with_space[:8]:
            top_players = get_team_top_players(export, t['tid'], season, count=2)
            needs_str = f", needs: {', '.join(t['needs'])}" if t['needs'] else ""
            prompt += f"- {t['name']} (${t['cap_space']:.1f}M space, {t['record']}{needs_str}) — {', '.join(top_players)}\n"

        if no_space:
            prompt += "\nTEAMS WITH NO CAP SPACE (locked in):\n"
            for t in no_space[:5]:
                top_players = get_team_top_players(export, t['tid'], season, count=2)
                prompt += f"- {t['name']} (${t['cap_space']:.1f}M space, {t['record']}) — {', '.join(top_players)}\n"

        prompt += f"""
Write a free agency preview column (2-3 paragraphs, under 1500 characters). NOT just listing who's available. Instead:
- Who is THE marquee free agent and which teams are best positioned to land them? Consider cap space AND team fit
- Which team with cap space is most likely to make a splash and what player should they target?
- Name one under-the-radar free agent who could be a steal on a bargain deal
- Which contender is stuck with no cap space and might miss out?
- Be an insider making predictions: "I expect [Player] to sign with [Team] because..."

CRITICAL: You may ONLY reference team names, player names, and facts from the data above.
Do NOT invent any names, events, stats, or storylines not supported by the data above. If a section above is empty, skip that topic entirely.
NEVER mention OVR, POT, ratings, or overall numbers in your output — write like a real sports journalist.
Format for Discord with **bold** headers. Start with **{season} FREE AGENCY PREVIEW**"""

        content = await safe_recap_call(prompt)

        if content and len(content) > 4090:
            content = content[:4087] + "..."

        if content:
            embed = discord.Embed(
                title="🏷️ Free Agency Preview",
                description=content,
                color=discord.Color.dark_gold()
            )
            await channel.send(embed=embed)

    except Exception as e:
        print(f"FA preview generation failed: {e}")

def fire_and_forget_fa_preview(export, guild_id, channel_id=None):
    """Launch FA preview task and return immediately"""
    asyncio.create_task(generate_fa_preview_async(export, guild_id, channel_id))