import discord
from discord.ui import View, Button, Select
from firestore_db import save_prediction, get_predictions_user_match
from football_api import get_next_matchday_matches, convert_to_belgian_time

class MatchSelectView(View):
    def __init__(self, ctx, user_id, bot, matches):
        super().__init__()
        self.ctx = ctx
        self.user_id = user_id
        self.bot = bot
        self.matches = matches
        self.selected_match_id = None
        self.message = None  # To store the original message

        options = [discord.SelectOption(label=f"{match['homeTeam']['name']} vs {match['awayTeam']['name']}", value=str(match['id'])) for match in matches]
        id_to_home_team = {str(match['id']): match['homeTeam']['name'] for match in matches}
        id_to_away_team = {str(match['id']): match['awayTeam']['name'] for match in matches}
        self.add_item(SelectMatch(options, user_id, id_to_home_team, id_to_away_team))

class SelectMatch(Select):
    def __init__(self, options, user_id, id_to_home_team, id_to_away_team):
        super().__init__(placeholder="Select a match...", options=options)
        self.user_id = user_id
        self.id_to_home_team = id_to_home_team
        self.id_to_away_team = id_to_away_team

    async def callback(self, interaction: discord.Interaction):
        selected_match_id = self.values[0]
        # Prompt for home goals
        view = HomeGoalsSelectView(interaction.channel, self.user_id, selected_match_id, self.id_to_home_team, self.id_to_away_team)
        await interaction.response.edit_message(
            content=f"Match **{self.id_to_home_team[selected_match_id]} vs {self.id_to_away_team[selected_match_id]}** selected. Please select {self.id_to_home_team[selected_match_id]}'s goals.",
            view=view
        )

class HomeGoalsSelectView(View):
    def __init__(self, channel, user_id, match_id, id_to_home_team, id_to_away_team):
        super().__init__()
        self.channel = channel
        self.user_id = user_id
        self.match_id = match_id
        self.id_to_home_team = id_to_home_team
        self.id_to_away_team = id_to_away_team
        self.home_goals = None

        self.add_item(SelectGoals(f"{self.id_to_home_team[match_id]}", [str(i) for i in range(20)], self))

class AwayGoalsSelectView(View):
    def __init__(self, channel, user_id, match_id, home_goals, id_to_home_team, id_to_away_team):
        super().__init__()
        self.channel = channel
        self.user_id = user_id
        self.match_id = match_id
        self.id_to_home_team = id_to_home_team
        self.id_to_away_team = id_to_away_team
        self.home_goals = home_goals

        self.add_item(SelectGoals(f"{self.id_to_away_team[match_id]}", [str(i) for i in range(20)], self))

class SelectGoals(Select):
    def __init__(self, placeholder, options, parent_view):
        super().__init__(placeholder=placeholder, options=[discord.SelectOption(label=option, value=option) for option in options])
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.placeholder == f"{self.parent_view.id_to_home_team[self.parent_view.match_id]}":
            home_goals = self.values[0]
            # Move to selecting away goals
            view = AwayGoalsSelectView(interaction.channel, self.parent_view.user_id, self.parent_view.match_id, home_goals, self.parent_view.id_to_home_team, self.parent_view.id_to_away_team)
            await interaction.response.edit_message(
                content=f"{self.parent_view.id_to_home_team[self.parent_view.match_id]} goals set to {home_goals}. Now select the {self.parent_view.id_to_away_team[self.parent_view.match_id]}'s goals.",
                view=view
            )

        elif self.placeholder == f"{self.parent_view.id_to_away_team[self.parent_view.match_id]}":
            away_goals = self.values[0]
            home_goals = self.parent_view.home_goals
            match_id = self.parent_view.match_id
            # Save the prediction
            save_prediction(self.parent_view.user_id, match_id, int(home_goals), int(away_goals))
            await interaction.response.edit_message(
                content=f"Prediction saved: {self.parent_view.id_to_home_team[self.parent_view.match_id]} {home_goals} - {away_goals} {self.parent_view.id_to_away_team[self.parent_view.match_id]}.",
                view=None
            )

def show_upcoming_matches(next_matchday_matches, user_id):
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
            response += f"{match_time}: {home_team}     _-_     {away_team}\n"
        else:
            response += f"{match_time}: {home_team}     **{prediction['home_goals']}-{prediction['away_goals']}**     {away_team}\n"

    return response

async def register_predict_command(ctx,bot):
    user_id = str(ctx.author.id)
    next_matchday_matches = get_next_matchday_matches()
    if not next_matchday_matches:
        await ctx.respond("No upcoming or ongoing matches found.")
        return
    
    matches_message = show_upcoming_matches(next_matchday_matches, user_id)

    # Send the message with the match list and then add the dropdown
    view = MatchSelectView(ctx, user_id, bot, next_matchday_matches)
    view.message = await ctx.response.send_message(matches_message, view=view, ephemeral=True)
    
    # Optionally, you can delete the user's command message if needed
    # await ctx.message.delete()

