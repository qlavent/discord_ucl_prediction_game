import discord
from discord.ext import commands, tasks
import os
from commands import register_commands
from game_updates import check_game_updates
from firestore_db import init_firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize Firestore
init_firestore()

# Initialize Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Register bot commands
register_commands(bot)

# Task to check for game updates regularly
@tasks.loop(minutes=5)
async def update_game_results():
    await check_game_updates(bot)

# Start checking game updates when bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    update_game_results.start()

# Run the bot
bot.run(TOKEN)
