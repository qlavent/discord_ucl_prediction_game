import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button, Select
from firestore_db import (
    save_prediction,
    get_leaderboard,
    get_predictions_user_match,
    get_past_predictions
)
from football_api import get_next_matchday_matches, convert_to_belgian_time
from datetime import datetime


def register_commands(bot):

    @bot.command(name='leaderboard')
    async def leaderboard(ctx):
        leaderboard_data = get_leaderboard()
        sorted_leaderboard = sorted(leaderboard_data.items(), key=lambda x: x[1], reverse=True)
        leaderboard_message = "Updated Leaderboard:\n"
        
        for i, (user_id, points) in enumerate(sorted_leaderboard):
            user = await bot.fetch_user(user_id)
            if i < 3:
                symbols = ["🥇", "🥈", "🥉"]
                leaderboard_message += f"{symbols[i]} {user.display_name}: {points}pts\n"
            else:
                leaderboard_message += f"{i + 1}) {user.display_name}: {points}pts\n"
        await ctx.send(leaderboard_message)

    @bot.command(name='uclhelp')
    async def uclhelp(ctx):
        response = (
            "!predict - Show games available for prediction.\n"
            "!leaderboard - View the current leaderboard.\n"
            "!history - Interactively select a date range to view your past predictions.\n"
            "!uclhelp - Show available commands.\n"
        )
        await ctx.send(response)

async def register_leaderboard_command(ctx, bot):
    leaderboard_data = get_leaderboard()
    sorted_leaderboard = sorted(leaderboard_data.items(), key=lambda x: x[1], reverse=True)
    leaderboard_message = "Updated Leaderboard:\n"
    
    for i, (user_id, points) in enumerate(sorted_leaderboard):
        user = await bot.fetch_user(user_id)
        if i < 3:
            symbols = ["🥇", "🥈", "🥉"]
            leaderboard_message += f"{symbols[i]} {user.display_name}: {points}pts\n"
        else:
            leaderboard_message += f"{i + 1}) {user.display_name}: {points}pts\n"
    await ctx.response.send_message(leaderboard_message)

async def register_uclhelp_command(ctx, bot):
    response = (
        "/predict - Show games available for prediction.\n"
        "/leaderboard - View the current leaderboard.\n"
        "/history - Interactively select a date range to view your past predictions.\n"
        "/help - Show available commands.\n"
    )
    await ctx.response.send_message(response)

