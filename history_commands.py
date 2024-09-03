import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
from firestore_db import get_past_predictions
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

def register_history_command(bot):
    @bot.command(name='history')
    async def history(ctx):
        user_id = str(ctx.author.id)
        view = DateSelectionView(ctx, user_id, bot)
        await ctx.send("Click the buttons below to set your dates and get your history.", view=view)
