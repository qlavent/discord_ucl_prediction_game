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
        "https://api.football-data.org/v4/competitions/PL/matches",
        headers={'X-Auth-Token': API_KEY}
    )
    # Parse response
    matches = response.json().get('matches', [])
    if not matches:
        return []

    # Sort matches by stage and matchday to find the next matchday
    matches.sort(key=lambda match: (match['stage'], match['matchday']))
    
    # Group matches by stage and matchday combination
    grouped_matches = {}
    for match in matches:
        key = (match['stage'], match['matchday'])
        if key not in grouped_matches:
            grouped_matches[key] = []
        grouped_matches[key].append(match)
    # Find the current date and time in UTC
    current_time = datetime.utcnow().replace(tzinfo=pytz.utc)
    
    # Iterate through sorted matchdays to find the next set of unplayed matches
    for (stage, matchday), match_list in grouped_matches.items():
        unplayed_matches = [
            match for match in match_list
            if match['status'] in ['SCHEDULED', 'TIMED']
        ]
        if unplayed_matches:
            # If there are unplayed matches in this stage and matchday, return them
            return unplayed_matches
        
        # If we are still in an ongoing matchday with partially played games, show remaining
        ongoing_matches = [
            match for match in match_list
            if match['status'] == 'IN_PLAY' or match['utcDate'] > current_time.isoformat()
        ]
        if ongoing_matches:
            return ongoing_matches

    # If no ongoing or unplayed matches found, return an empty list
    return []

def convert_to_belgian_time(utc_time_str):
    utc_time = datetime.strptime(utc_time_str, '%Y-%m-%dT%H:%M:%SZ')
    utc_time = utc_time.replace(tzinfo=pytz.utc)
    belgian_time = utc_time.astimezone(pytz.timezone('Europe/Brussels'))
    return belgian_time
