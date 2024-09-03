import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
from firestore_db import (
    save_prediction,
    get_leaderboard,
    get_predictions_user_match,
    get_past_predictions
)
from game_updates import calculate_points
from football_api import get_next_matchday_matches, convert_to_belgian_time
from datetime import datetime

class DateSelectionView(View):
    def __init__(self, ctx, user_id, bot):
        super().__init__()
        self.ctx = ctx
        self.user_id = user_id
        self.bot = bot
        self.begin_date = None
        self.end_date = None

    @discord.ui.button(label='Set Begin Date', style=discord.ButtonStyle.primary)
    async def set_begin_date(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please enter the begin date in dd/mm/yyyy format.")
        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=60.0,
                check=lambda m: m.author == self.ctx.author
            )
            self.begin_date = datetime.strptime(msg.content, "%d/%m/%Y").date()
            await msg.delete()
            await interaction.followup.send(f"Begin date set to {self.begin_date}.")
        except ValueError:
            await interaction.followup.send("Invalid date format. Please use dd/mm/yyyy.")
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond.")

    @discord.ui.button(label='Set End Date', style=discord.ButtonStyle.primary)
    async def set_end_date(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please enter the end date in dd/mm/yyyy format.")
        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=60.0,
                check=lambda m: m.author == self.ctx.author
            )
            self.end_date = datetime.strptime(msg.content, "%d/%m/%Y").date()
            await msg.delete()
            await interaction.followup.send(f"End date set to {self.end_date}.")
        except ValueError:
            await interaction.followup.send("Invalid date format. Please use dd/mm/yyyy.")
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond.")

    @discord.ui.button(label='Get History', style=discord.ButtonStyle.green)
    async def get_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.begin_date and self.end_date:
            past_predictions = get_past_predictions(self.user_id, self.begin_date.strftime("%d/%m/%Y"), self.end_date.strftime("%d/%m/%Y"))
            if not past_predictions:
                await interaction.response.send_message("You have no past predictions in the specified time range.")
                return

            response = "Your Past Predictions:\n"
            for date, times in past_predictions.items():
                response += f"{date}:\n"
                for time, games in times.items():
                    response += f"{time}:\n"
                    for game in games:
                        home_team = game['home_team']
                        away_team = game['away_team']
                        actual_score = f"{game['actual_home_goals']}-{game['actual_away_goals']}"
                        predicted_score = f"{game['predicted_home_goals']}-{game['predicted_away_goals']}"
                        points = game['points']
                        response += f"    {home_team} vs {away_team}: Predicted {predicted_score}, Actual {actual_score}, Points: {points}\n"
            await interaction.response.send_message(response)
        else:
            await interaction.response.send_message("Please set both begin and end dates before getting the history.")

def register_commands(bot):
    @bot.command(name='predict')
    async def predict(ctx):
        user_id = str(ctx.author.id)
        next_matchday_matches = get_next_matchday_matches()
        if not next_matchday_matches:
            await ctx.send("No upcoming or ongoing matches found.")
            return

        response = "Upcoming Champions League Matches:\n"
        current_date = None

        for match in next_matchday_matches:
            match_id = str(match['id'])
            prediction = get_predictions_user_match(user_id=user_id, match_id=match_id)
            match_date = convert_to_belgian_time(match['utcDate']).strftime("%Y-%m-%d")
            match_time = convert_to_belgian_time(match['utcDate']).strftime("%H:%M")
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']

            if match_date != current_date:
                current_date = match_date
                response += f"\n{match_date}:\n"
            if prediction is None:
                response += f"{match_time}: {home_team}     _-_     {away_team}           match ID: {str(match['id'])}\n"
            else: 
                response += f"{match_time}: {home_team}     **{prediction['home_goals']}-{prediction['away_goals']}**     {away_team}           match ID: {str(match['id'])}\n"

        await ctx.send(response)

    @bot.command(name='setpredict')
    async def setpredict(ctx, match_id: str, home_goals: int, away_goals: int):
        user_id = str(ctx.author.id)
        save_prediction(user_id, match_id, home_goals, away_goals)
        await ctx.send(f'Prediction saved for match {match_id}.')

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
            "!setpredict <match_id> <home_goals> <away_goals> - Enter your prediction for a specific match.\n"
            "!leaderboard - View the current leaderboard.\n"
            "!history - Interactively select a date range to view your past predictions.\n"
            "!uclhelp - Show available commands.\n"
        )
        await ctx.send(response)

    @bot.command(name='history')
    async def history(ctx):
        user_id = str(ctx.author.id)
        view = DateSelectionView(ctx, user_id, bot)
        await ctx.send("Click the buttons below to set your dates and get your history.", view=view)