import discord
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta
from data_fetch import fetch_prem_today
from keep_alive import keep_alive

# Load environment variables from the .env file
load_dotenv()


class MyClient(discord.Client):

  async def on_ready(self):
    print('Logged on as', self.user)

  async def on_message(self, message):
    # don't respond to ourselves
    if message.author == self.user:
      return

    if message.content.lower() == 'ping':
      await message.channel.send('pong')

    if message.content.lower() == 'prem':
      prem_games = fetch_prem_today()
      await message.channel.send(prem_games)


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
DISCORD_TOKEN = os.getenv('TOKEN')
client.run(str(DISCORD_TOKEN))
