import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta
import pytz


def fetch_prem_today():
  api_token = os.getenv('FOOTBALL_API')
  headers = {'X-Auth-Token': api_token}
  # Define timezone for Belgium
  belgium_tz = pytz.timezone('Europe/Brussels')

  # Define the endpoint for matches
  url = 'https://api.football-data.org/v4/matches'

  # Get today's date
  today = datetime.today()

  # Calculate tomorrow's date by adding one day
  tomorrow = today + timedelta(days=1)

  # Format the date as a string if needed
  tomorrow_str = tomorrow.strftime('%Y-%m-%d')
  # Get today's date in the required format (YYYY-MM-DD)
  today_str = today.strftime('%Y-%m-%d')

  # Define query parameters
  params = {
      'competitions': 'PL',  # PL is the competition code for Premier League
      'dateFrom': today_str,
      'dateTo': tomorrow_str
  }

  result = ''
  # Make the GET request to fetch today's Premier League matches
  response = requests.get(url, headers=headers, params=params)

  if response.status_code == 200:
    print("Data fetched successfully!")
    result += 'Premier league matches of today:\n\n'
    for match in response.json()['matches']:
      # Parse the UTC datetime
      utc_datetime = datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ')

      # Localize the datetime to UTC
      utc_datetime = pytz.utc.localize(utc_datetime)

      # Convert to Belgium timezone
      belgium_datetime = utc_datetime.astimezone(belgium_tz)

      # Format the time in HH:MM
      match_time = belgium_datetime.strftime('%H:%M')
      result += f"{match_time}| {match['homeTeam']['name']} vs {match['awayTeam']['name']} \n"
      #print(match['homeTeam']['name'], 'vs', match['awayTeam']['name'])
  elif response.status_code == 401:
    print("Unauthorized access: Check your API key.")
  elif response.status_code == 403:
    print(
        "Forbidden access: Your account may not have permission for this data. Consider checking your plan."
    )
  elif response.status_code == 429:
    print(
        "Rate limit exceeded: You have made too many requests. Please try again later."
    )
  else:
    print(f"Failed to fetch data: {response.status_code}, {response.text}")

  return result
