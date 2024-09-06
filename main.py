import discord
from discord.ext import commands, tasks
import os
from commands import register_commands, register_leaderboard_command, register_uclhelp_command
from predict_commands import register_predict_command
from history_commands import register_history_command
from game_updates import check_game_updates
from firestore_db import init_firestore, get_users_without_predictions, enable_reminder, disable_reminder, check_reminder_messages
from football_api import get_next_matchday_matches, convert_to_belgian_time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pytz import utc

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Firestore
init_firestore()

# Set up intents (adjust if needed)
intents = discord.Intents.default()
intents.message_content = True  # Adjust based on your bot's needs

# Initialize the bot with slash command support
bot = commands.Bot(command_prefix="", intents=intents)

# Task to check for game updates regularly
@tasks.loop(minutes=5)
async def update_game_results():
    await check_game_updates(bot)

# Task to send reminders for games that are between 23 and 24 hours away
@tasks.loop(hours=1)
async def send_prediction_reminders():
    print('running loop')
    now = datetime.utcnow().replace(tzinfo=utc)
    next_matchday_matches = get_next_matchday_matches()

    for match in next_matchday_matches:
        match_time = convert_to_belgian_time(match['utcDate'])
        time_difference = match_time - now

        # Check if the match is between 23 and 24 hours away
        if timedelta(hours=23) <= time_difference <= timedelta(hours=24):
            match_id = str(match['id'])
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']

            # Get users without predictions for this match
            users_without_predictions = get_users_without_predictions(match_id)

            # Send reminder message to each user
            for user_id in users_without_predictions:
                send_reminder = check_reminder_messages(user_id)
                if send_reminder:
                    user = await bot.fetch_user(int(user_id))
                    await user.send(
                        f"Reminder: The match between {home_team} and {away_team} is in less than 24 hours. "
                        "Please make sure to submit your prediction!"
                    )

# Start checking game updates when bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    update_game_results.start()
    send_prediction_reminders.start()

@bot.slash_command(name="predict", description="Predict the Champions League match results.")
async def predict(ctx: discord.Interaction):
    user_id = str(ctx.author.id)
    enable_reminder(user_id)
    await register_predict_command(ctx,bot)

@bot.slash_command(name="history", description="Interactively select a date range to view your past predictions.")
async def history(ctx: discord.Interaction):
    await register_history_command(ctx,bot)

@bot.slash_command(name="leaderboard", description=" View the current leaderboard.")
async def leaderboard(ctx: discord.Interaction):
    await register_leaderboard_command(ctx,bot)

@bot.slash_command(name="help", description="Show available commands.")
async def uclhelp(ctx: discord.Interaction):
    await register_uclhelp_command(ctx,bot)

@bot.slash_command(name="enable_messages", description="Enable to send reminder messages for the prediction.")
async def enable_discord_reminder(ctx: discord.Interaction):
    user_id = str(ctx.author.id)
    enable_reminder(user_id)
    message = "The bot is now enabled to send reminder messages"
    await ctx.response.send_message(message,ephemeral=True)

@bot.slash_command(name="disable_messages", description="Disable to send reminder messages for the prediction.")
async def disable_discord_reminder(ctx: discord.Interaction):
    user_id = str(ctx.author.id)
    disable_reminder(user_id)
    message = "The bot is now disabled to send reminder messages"
    await ctx.response.send_message(message,ephemeral=True)

@bot.slash_command(name="register", description="Register to be part of the prediction game.")
async def register(ctx: discord.Interaction):
    user_id = str(ctx.author.id)
    enable_reminder(user_id)
    message = "You are now registered in the UCL prediction game. Your reminder messages are currently enabled"
    await ctx.response.send_message(message,ephemeral=True)

# Run the bot
bot.run(TOKEN)
