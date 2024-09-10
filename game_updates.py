import os
import requests
import discord
from firestore_db import update_game_result, get_predictions_match, update_user_points, get_leaderboard, update_prediction_points
from football_api import convert_to_belgian_time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('FOOTBALL_API_KEY')
channel_id = int(os.getenv('DISCORD_CHANNEL_ID'))

async def check_game_updates(bot):
    # Fetch UCL games that have finished
    response = requests.get(
        "https://api.football-data.org/v4/competitions/PL/matches?status=FINISHED",
        headers={'X-Auth-Token': API_KEY}
    )
    matches = response.json().get('matches', [])
    for match in matches:
        match_id = str(match['id'])
        home_team = match['homeTeam']['name']
        away_team = match['awayTeam']['name']
        home_score = match['score']['fullTime']['home']
        away_score = match['score']['fullTime']['away']
        match_date = match['utcDate']

        # Update the game result in Firestore
        already_returned = update_game_result(match_id, home_score, away_score, match_date, home_team, away_team)
        if already_returned: 
            continue
        # Get predictions for this match
        predictions = get_predictions_match(match_id)

        # Calculate points and update leaderboard
        result_message = f"Result: {home_team} {home_score} - {away_score} {away_team}\n"
        for prediction_id, pred in predictions.items():
            predicted_home = pred['home_goals']
            predicted_away = pred['away_goals']
            user_id = pred['user_id']
            points = calculate_points(home_score, away_score, predicted_home, predicted_away)
            update_prediction_points(prediction_id, points)
            update_user_points(user_id, points)
            result_message += f"<@{user_id}> predicted {predicted_home}-{predicted_away}, earned {points} points\n"

        # Send result and updated leaderboard to a specific channel
        print(channel_id)
        channel = bot.get_channel(channel_id)
        print(channel)
        await channel.send(result_message)
        await send_leaderboard(bot)

async def send_leaderboard(bot):
    # Fetch and sort leaderboard data
    leaderboard_data = get_leaderboard()
    sorted_leaderboard = sorted(leaderboard_data.items(), key=lambda x: x[1], reverse=True)

    # Initialize leaderboard message
    leaderboard_message = "Updated Leaderboard:\n"
    
    # Fetch the users' display names
    for i, (user_id, points) in enumerate(sorted_leaderboard):
        user = await bot.fetch_user(user_id)
        if i < 3:
            # Format top 3 users with special symbols
            symbols = ["🥇", "🥈", "🥉"]
            leaderboard_message += f"{symbols[i]} {user.display_name}: {points}pts\n"
        else:
            # Format for 4th place and beyond
            leaderboard_message += f"{i + 1}) {user.display_name}: {points}pts\n"

    # Send the formatted leaderboard message to a specific channel
    channel = bot.get_channel(channel_id)
    await channel.send(leaderboard_message)

def calculate_points(actual_home, actual_away, predicted_home, predicted_away):
    if actual_home == predicted_home and actual_away == predicted_away:
        return 10
    elif (actual_home - actual_away) == (predicted_home - predicted_away):
        return 7
    elif (actual_home > actual_away and predicted_home > predicted_away) or (actual_home < actual_away and predicted_home < predicted_away):
        return 5
    return 1
