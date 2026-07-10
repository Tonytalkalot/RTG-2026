"""Gemini AI integration for trade evaluation"""
import os
import google.generativeai as genai

# Load API key
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        with open("gemini.txt", "r") as f:
            GEMINI_API_KEY = f.read().strip()

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
except Exception as e:
    print(f"Failed to initialize Gemini: {e}")
    model = None

async def evaluate_trade(tradeData, export):
    """Generate context-aware one-line trade evaluation"""
    
    if not model:
        return None
    
    # Build rich context about the trade
    context = build_trade_context(tradeData, export)
    
    prompt = f"""You are a basketball analyst. Evaluate this trade in ONE punchy, insightful sentence (max 20 words).

TRADE DETAILS:
{context['summary']}

KEY CONTEXT:
{context['analysis']}

Create a response that:
- References specific players or team situations
- Balances wit with genuine insight
- Mentions concrete details (player ratings, age, team record, cap situation)

Examples of good responses:
- "Tanking Pistons flip 31-year-old declining vet for youth; classic timeline pivot"
- "Warriors betting 84-OVR Curry can carry them one more year while Spurs rebuild"  
- "Lakers gave up their only shooter (42% from three) for another non-spacing big"
- "Thunder adds the 3rd-best U25 player while keeping all their picks somehow"
- "Heat culture meets 22-year-old with 90 potential - perfect development situation"

ONE SENTENCE. Be specific about WHY this trade matters."""
    
    try:
        response = model.generate_content(prompt)
        # Clean up response - remove quotes if present, trim whitespace
        result = response.text.strip().strip('"').strip("'")
        # Ensure it's not too long
        if len(result) > 150:
            result = result[:147] + "..."
        return result
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

async def generate_rejection_message(tradeData, export, reason):
    """Generate a fun, in-character rejection message for autopilot trade rejections"""

    if not model:
        return None

    context = build_trade_context(tradeData, export)

    prompt = f"""You are a sassy, confident AI acting as a basketball GM. A team just proposed a trade to you that you're rejecting.

TRADE DETAILS:
{context['summary']}

REJECTION REASON: {reason}

{context['analysis']}

Write a short, fun rejection message (1-2 sentences, max 40 words) as the GM rejecting this deal. Be playful and a little cocky — like a GM who knows their team's worth. Don't be mean, just confident.

CRITICAL RULES:
- ONLY reference players, picks, and stats that appear in the TRADE DETAILS and KEY CONTEXT above
- Do NOT invent or assume any details not explicitly listed
- If you mention a pick, use the exact description from the trade details
- If you mention a player, use their exact name and stats from the trade details

ONE short response. No quotes around it."""

    try:
        response = model.generate_content(prompt)
        result = response.text.strip().strip('"').strip("'")
        if len(result) > 200:
            result = result[:197] + "..."
        return result
    except Exception as e:
        print(f"Gemini rejection message error: {e}")
        return None


def build_trade_context(tradeData, export):
    """Extract meaningful context from the trade"""
    teams = export['teams']
    players = export['players']
    season = export['gameAttributes']['season']
    
    context = {
        'summary': '', 
        'analysis': '', 
        'rosters': '',
        'standings': '',
        'player_names': []  # Track all player names to prevent hallucination
    }
    
    # Build a summary showing what each team GETS (not what they send)
    # tradeData[tid] = assets that tid is SENDING AWAY
    # We need to show the inverse for clarity
    
    # Process each team to show what they're getting
    all_tids = list(tradeData.keys())
    
    for tid_str in all_tids:
        tid = int(tid_str)
        team = next((t for t in teams if t['tid'] == tid), None)
        if not team:
            continue
            
        # Get team context
        team_name = f"{team['region']} {team['name']}"
        team_abbrev = team['abbrev']
        
        # Calculate team strength (average OVR of roster)
        roster = [p for p in players if p['tid'] == tid]
        avg_ovr = sum(p['ratings'][-1]['ovr'] for p in roster) / len(roster) if roster else 50
        
        # Get team record if in season
        wins = 0
        losses = 0
        try:
            if 'seasons' in team and team['seasons']:
                wins = team['seasons'][-1].get('won', 0)
                losses = team['seasons'][-1].get('lost', 0)
                record = f"{wins}-{losses}"
                winning_pct = wins / (wins + losses) if (wins + losses) > 0 else 0
            else:
                record = "0-0"
                winning_pct = 0
        except:
            record = "0-0"
            winning_pct = 0
        
        # Build what this team RECEIVES (from other teams)
        asset_summary = []
        best_player = None
        best_ovr = 0
        total_picks = 0
        first_round_picks = 0
        second_round_picks = 0
        pick_details = []
        
        # Get assets from OTHER teams
        receiving_assets = []
        for other_tid in all_tids:
            if other_tid != tid_str:
                receiving_assets.extend(tradeData[other_tid])
        
        for a in receiving_assets:
            if a['type'] == 'player':
                pid = int(a['id'])
                player = next((p for p in players if p['pid'] == pid), None)
                if player and player.get('ratings'):
                    ovr = player['ratings'][-1]['ovr']
                    pot = player['ratings'][-1]['pot']
                    age = season - player['born']['year']
                    
                    # Track best player
                    if ovr > best_ovr:
                        best_ovr = ovr
                        best_player = {
                            'name': a['descrip'],
                            'ovr': ovr,
                            'pot': pot,
                            'age': age
                        }
                    
                    # Get special skills/stats
                    skills = player['ratings'][-1].get('skills', [])
                    skill_str = f" [{','.join(skills)}]" if skills else ""
                    
                    # Track player name
                    context['player_names'].append(a['descrip'])
                    
                    # Get contract details
                    contract_years = player['contract']['exp'] - season if 'contract' in player else 0
                    salary = player['contract']['amount'] / 1000 if 'contract' in player else 0  # Convert to millions
                    
                    # Determine player role based on OVR
                    if ovr >= 80:
                        role = "star"
                    elif ovr >= 70:
                        role = "starter"
                    elif ovr >= 60:
                        role = "rotation player"
                    else:
                        role = "bench player"
                    
                    # Focus on key info - always include position
                    pos = player['ratings'][-1].get('pos', 'N/A')
                    if ovr >= 75:  # Star player
                        asset_summary.append(f"{a['descrip']} ({pos}, {role}, {age}yo, ${salary:.1f}M{skill_str})")
                    else:
                        asset_summary.append(f"{a['descrip']} ({pos}, {role}, {age}yo, ${salary:.1f}M)")
            elif a['type'] == 'draftPick':
                total_picks += 1
                if '1st' in a['descrip'] or 'first' in a['descrip'].lower():
                    first_round_picks += 1
                    pick_details.append(a['descrip'])
                elif '2nd' in a['descrip'] or 'second' in a['descrip'].lower():
                    second_round_picks += 1
                    pick_details.append(a['descrip'])
        
        # Add all picks to summary with proper categorization
        if first_round_picks > 0:
            if first_round_picks == 1:
                asset_summary.extend([p for p in pick_details if '1st' in p or 'first' in p.lower()])
            else:
                asset_summary.append(f"{first_round_picks} first-round picks")
        if second_round_picks > 0:
            if second_round_picks <= 2:
                asset_summary.extend([p for p in pick_details if '2nd' in p or 'second' in p.lower()])
            else:
                asset_summary.append(f"{second_round_picks} second-round picks")
        
        # Add to summary - show all assets but smartly
        if asset_summary:
            # If too many items, summarize players but always show picks
            if len(asset_summary) > 5:
                # Separate players and picks
                player_items = [a for a in asset_summary if 'pick' not in a.lower()]
                pick_items = [a for a in asset_summary if 'pick' in a.lower()]
                
                # Show first 2 players and all picks
                summary_items = player_items[:2]
                if len(player_items) > 2:
                    summary_items.append(f"+ {len(player_items) - 2} more players")
                summary_items.extend(pick_items)
                context['summary'] += f"\n{team_name} ({record}) gets: {', '.join(summary_items)}"
            else:
                context['summary'] += f"\n{team_name} ({record}) gets: {', '.join(asset_summary)}"
        else:
            context['summary'] += f"\n{team_name} ({record}) gets: salary relief"
        
        # Add key analysis points
        if winning_pct > 0.6 and (wins + losses) > 10:
            context['analysis'] += f"\n- {team_abbrev} is contending ({record}, {avg_ovr:.0f} avg OVR)"
        elif winning_pct < 0.4 and (wins + losses) > 10:
            context['analysis'] += f"\n- {team_abbrev} is rebuilding ({record})"
        
        if best_player:
            if best_player['age'] < 25 and best_player['pot'] >= 85:
                context['analysis'] += f"\n- {best_player['name']} is a future star (age {best_player['age']}, {best_player['pot']} POT)"
            elif best_player['age'] > 33:
                context['analysis'] += f"\n- {best_player['name']} is past prime (age {best_player['age']})"
            elif best_player['ovr'] >= 80:
                context['analysis'] += f"\n- {best_player['name']} is elite right now ({best_player['ovr']} OVR)"
        
        # Check if team is dumping salary
        if not assets and roster:
            context['analysis'] += f"\n- {team_abbrev} is clearing cap space"
        
        # Analyze draft capital value based on pick count
        if first_round_picks >= 4:
            context['analysis'] += f"\n- {team_abbrev} acquiring superstar-level draft capital ({first_round_picks} first-round picks)"
        elif first_round_picks == 3:
            context['analysis'] += f"\n- {team_abbrev} acquiring high-end prospect value ({first_round_picks} first-round picks)"
        elif first_round_picks == 2:
            context['analysis'] += f"\n- {team_abbrev} acquiring all-star level draft capital ({first_round_picks} first-round picks)"
        elif first_round_picks == 1:
            context['analysis'] += f"\n- {team_abbrev} acquiring starter-level draft capital (1 first-round pick)"
        elif second_round_picks >= 3:
            context['analysis'] += f"\n- {team_abbrev} acquiring role player draft capital ({second_round_picks} second-round picks)"
    
    # Add roster context for teams involved in trade
    context['rosters'] = "\n\nROSTER CONTEXT:"
    for tid, assets in tradeData.items():
        tid = int(tid)
        team = next((t for t in teams if t['tid'] == tid), None)
        if not team:
            continue
        
        team_name = f"{team['region']} {team['name']}"
        roster = [p for p in players if p['tid'] == tid]
        
        # Sort roster by OVR
        roster.sort(key=lambda p: p['ratings'][-1]['ovr'] if p.get('ratings') else 0, reverse=True)
        
        # Get top 5 players
        context['rosters'] += f"\n\n{team_name} key players:"
        for i, p in enumerate(roster[:5]):
            if p.get('ratings'):
                ovr = p['ratings'][-1]['ovr']
                pot = p['ratings'][-1]['pot']
                age = season - p['born']['year']
                name = f"{p['firstName']} {p['lastName']}"
                pos = p['ratings'][-1].get('pos', 'N/A')
                
                # Include contract info for context
                contract_years = p['contract']['exp'] - season if 'contract' in p else 0
                salary = p['contract']['amount'] / 1000 if 'contract' in p else 0  # Convert to millions
                
                context['rosters'] += f"\n- {name} ({pos}, {ovr} OVR/{pot} POT, {age}yo, ${salary:.1f}M for {contract_years}yr)"
    
    # Add standings context
    context['standings'] = "\n\nLEAGUE STANDINGS:"
    
    # Get all teams with records
    all_teams = []
    for t in teams:
        if 'seasons' in t and t['seasons']:
            last_season = t['seasons'][-1]
            wins = last_season.get('won', 0)
            losses = last_season.get('lost', 0)
            if wins + losses > 0:  # Only include teams that have played games
                all_teams.append({
                    'name': t['abbrev'],
                    'wins': wins,
                    'losses': losses,
                    'pct': wins / (wins + losses)
                })
    
    # Sort by win percentage
    all_teams.sort(key=lambda x: x['pct'], reverse=True)
    
    # Show top 8 and bottom 3
    context['standings'] += "\nTop Teams:"
    for i, t in enumerate(all_teams[:8], 1):
        context['standings'] += f"\n{i}. {t['name']} ({t['wins']}-{t['losses']})"
    
    if len(all_teams) > 11:
        context['standings'] += "\n...\nBottom Teams:"
        for t in all_teams[-3:]:
            context['standings'] += f"\n{t['name']} ({t['wins']}-{t['losses']})"
    
    return context