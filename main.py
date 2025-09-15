import discord
from discord.ext import commands, tasks
import os
import asyncio
import logging
from commands import register_leaderboard_command, register_uclhelp_command
from predict_commands import register_predict_command
from history_commands import register_history_command
from game_updates import check_game_updates
from firestore_db import (
    init_firestore, get_users_without_predictions, enable_reminder,
    disable_reminder, check_reminder_messages
)
from football_api import get_next_matchday_matches, convert_to_belgian_time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pytz import utc
from keep_alive import keep_alive

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Firestore
init_firestore()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True  # Adjust based on your bot's needs

# Initialize the bot
bot = commands.Bot(command_prefix="command is", intents=intents)
tree = bot.tree  # This handles slash commands

# Task to check for game updates regularly
@tasks.loop(minutes=5)
async def update_game_results():
    try:
        await check_game_updates(bot)
        logger.info("Game updates check completed successfully")
    except Exception as e:
        logger.error(f"Error in update_game_results: {e}")


# Task to send reminders for games that are between 23 and 24 hours away
@tasks.loop(hours=1)
async def send_prediction_reminders():
    try:
        logger.info('Running prediction reminders loop')
        now = datetime.utcnow().replace(tzinfo=utc)
        next_matchday_matches, ongoing_matches = get_next_matchday_matches()

        for match in next_matchday_matches:
            match_time = convert_to_belgian_time(match['utcDate'])
            time_difference = match_time - now

            # Check if the match is between 23 and 24 hours away
            if timedelta(hours=23) <= time_difference <= timedelta(hours=24):
                match_id = str(match['id'])
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']

                # Get users without predictions for this match
                users_without_predictions = get_users_without_predictions(
                    match_id
                )

                # Send reminder message to each user
                for user_id in users_without_predictions:
                    try:
                        send_reminder = check_reminder_messages(user_id)
                        if send_reminder:
                            user = await bot.fetch_user(int(user_id))
                            await user.send(
                                f"Reminder: The match between {home_team} "
                                f"and {away_team} is in less than 24 hours. "
                                "Please make sure to submit your prediction!"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error sending reminder to user {user_id}: {e}"
                        )
    except Exception as e:
        logger.error(f"Error in send_prediction_reminders: {e}")


# Start checking game updates when bot is ready
@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        await tree.sync()  # Sync slash commands with Discord
        logger.info("Slash commands synced successfully")

        # Start background tasks
        if not update_game_results.is_running():
            update_game_results.start()
            logger.info("Game updates task started")

        if not send_prediction_reminders.is_running():
            send_prediction_reminders.start()
            logger.info("Prediction reminders task started")
    except Exception as e:
        logger.error(f"Error in on_ready: {e}")


# Handle disconnections and reconnections
@bot.event
async def on_disconnect():
    logger.warning("Bot disconnected from Discord")


@bot.event
async def on_resumed():
    logger.info("Bot reconnected to Discord")


# Define slash commands using app_commands.command decorator
@tree.command(
    name="predict",
    description="Predict the Champions League match results."
)
async def predict(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    enable_reminder(user_id)
    await register_predict_command(interaction, bot)


@tree.command(
    name="history",
    description="Interactively select a date range to view your past "
               "predictions."
)
async def history(interaction: discord.Interaction):
    await register_history_command(interaction, bot)


@tree.command(name="leaderboard", description="View the current leaderboard.")
async def leaderboard(interaction: discord.Interaction):
    await register_leaderboard_command(interaction, bot)


@tree.command(name="help", description="Show available commands.")
async def uclhelp(interaction: discord.Interaction):
    await register_uclhelp_command(interaction, bot)


@tree.command(
    name="enable_messages",
    description="Enable reminder messages for the prediction."
)
async def enable_discord_reminder(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    enable_reminder(user_id)
    message = "The bot is now enabled to send reminder messages."
    await interaction.response.send_message(message, ephemeral=True)


@tree.command(
    name="disable_messages",
    description="Disable reminder messages for the prediction."
)
async def disable_discord_reminder(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    disable_reminder(user_id)
    message = "The bot is now disabled to send reminder messages."
    await interaction.response.send_message(message, ephemeral=True)


@tree.command(
    name="register",
    description="Register to be part of the prediction game."
)
async def register(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    enable_reminder(user_id)
    message = ("You are now registered in the UCL prediction game. "
               "Your reminder messages are currently enabled.")
    await interaction.response.send_message(message, ephemeral=True)


# Bot restart mechanism
async def run_bot():
    while True:
        try:
            logger.info("Starting Discord bot...")
            await bot.start(TOKEN)
        except discord.LoginFailure:
            logger.error(
                "Invalid Discord token. Please check your DISCORD_TOKEN "
                "environment variable."
            )
            break
        except Exception as e:
            logger.error(f"Bot crashed with error: {e}")
            logger.info("Restarting bot in 30 seconds...")
            await asyncio.sleep(30)
        else:
            logger.info("Bot stopped normally")
            break


# Main execution
if __name__ == "__main__":
    # Start keep-alive server
    keep_alive()

    # Run the bot with restart capability
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
