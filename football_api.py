import os
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('FOOTBALL_API_KEY')

def get_next_matchday_matches():
    # Fetch all matches with relevant statuses
    response = requests.get(
        "https://api.football-data.org/v4/competitions/CL/matches",
        headers={'X-Auth-Token': API_KEY}
    )

    # Parse response
    matches = response.json().get('matches', [])
    if not matches:
        return [],[]
    
    # Group matches by stage and matchday combination
    grouped_matches = {}
    for match in matches:
        key = (match['stage'], match['matchday'])
        if key not in grouped_matches:
            grouped_matches[key] = []
        grouped_matches[key].append(match)

    # Find the current date and time in UTC
    current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
    
    for (stage, matchday), match_list in grouped_matches.items():
        # Check if any match is in 'IN_PLAY', 'SCHEDULED', or 'TIMED' status
        unplayed_matches = [
            match for match in match_list
            if match['status'] in ['SCHEDULED', 'TIMED']
        ]
        
        # Check if any match is ongoing or scheduled for a future date
        ongoing_or_future_matches = [
            match for match in match_list
            if match['status'] == 'IN_PLAY' or match['status'] == 'PAUSED'  or datetime.strptime(match['utcDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc) > current_time
        ]
        
        # If there are both played and unplayed matches in this stage and matchday, return them
        if unplayed_matches and len(unplayed_matches) < len(match_list) and len(unplayed_matches) > 0:
            print(unplayed_matches)
            return unplayed_matches, ongoing_or_future_matches

        # If no matches have been played yet and some are upcoming, return those
        if ongoing_or_future_matches:
            print(ongoing_or_future_matches)
            return unplayed_matches, ongoing_or_future_matches

    # If no ongoing or unplayed matches found, return an empty list
    return [],[]

def convert_to_belgian_time(utc_time_str):
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    belgian_time = utc_time.astimezone(pytz.timezone('Europe/Brussels'))
    return belgian_time
