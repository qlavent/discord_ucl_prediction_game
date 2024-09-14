import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
from firestore_db import get_past_predictions
from datetime import datetime

class DateSelectionView(View):
    def __init__(self, interaction: discord.Interaction, user_id: str, bot: commands.Bot):
        super().__init__()
        self.interaction = interaction
        self.user_id = user_id
        self.bot = bot
        self.begin_date = None
        self.end_date = None
        self.message = None  # To store the original message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("You are not allowed to interact with these buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Set Begin Date', style=discord.ButtonStyle.primary)
    async def set_begin_date(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.send_message("Please enter the begin date in dd/mm/yyyy format.", ephemeral=True)

        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=60.0,
                check=lambda m: m.author == interaction.user and m.channel == interaction.channel
            )
            self.begin_date = datetime.strptime(msg.content, "%d/%m/%Y").date()
            await msg.delete()
            await interaction.followup.send(f"Begin date set to {self.begin_date}.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("Invalid date format. Please use dd/mm/yyyy.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond.", ephemeral=True)
            if self.message:
                await self.message.delete()
            return

    @discord.ui.button(label='Set End Date', style=discord.ButtonStyle.primary)
    async def set_end_date(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.interaction_check(interaction):
            return
        await interaction.response.send_message("Please enter the end date in dd/mm/yyyy format.", ephemeral=True)

        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=60.0,
                check=lambda m: m.author == interaction.user and m.channel == interaction.channel
            )
            self.end_date = datetime.strptime(msg.content, "%d/%m/%Y").date()
            await msg.delete()
            await interaction.followup.send(f"End date set to {self.end_date}.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("Invalid date format. Please use dd/mm/yyyy.", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond.", ephemeral=True)
            if self.message:
                await self.message.delete()
            return

    @discord.ui.button(label='Get History', style=discord.ButtonStyle.green)
    async def get_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.begin_date and self.end_date:
            user = await self.bot.fetch_user(self.user_id)
            past_predictions = get_past_predictions(self.user_id, self.begin_date.strftime("%d/%m/%Y"), self.end_date.strftime("%d/%m/%Y"))
            if not past_predictions:
                await interaction.response.send_message(f"{user.display_name}, you have no past predictions in the specified time range.", ephemeral=True)
                for item in self.children:
                    item.disabled = True
                if self.message:
                    await self.message.edit(view=self)
                    await self.message.delete()
                return

            response = f"{user.display_name}, your Past Predictions:\n"
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
            await interaction.response.send_message(response, ephemeral=False)

            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(view=self)  # Edit the original UI message
                await self.message.delete()
        else:
            await interaction.response.send_message("Please set both begin and end dates before getting the history.", ephemeral=True)

async def register_history_command(interaction: discord.Interaction, bot: commands.Bot):
    user_id = str(interaction.user.id)

    view = DateSelectionView(interaction, user_id, bot)
    
    # Send the initial message to acknowledge the interaction
    await interaction.response.send_message(
        "Click the buttons below to set your dates and get your history.",
        ephemeral=True  # Make this response ephemeral
    )
    
    # Send the actual message with the buttons and store it in `view.message`
    view.message = await interaction.followup.send(
        "Click the buttons below to set your dates and get your history.",
        view=view,
        ephemeral=True
    )
