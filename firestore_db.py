from collections import defaultdict
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pytz  # Importing pytz for timezone conversion

# Initialize Firestore
db = None

def init_firestore():
    global db
    cred = credentials.Certificate("discord-ucl-prediction-game-firebase-adminsdk-a7j85-104cd7d712.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()

def save_prediction(user_id, match_id, home_goals, away_goals):
    # Reference to the 'predictions' collection
    predictions_ref = db.collection('predictions')
    
    # Query to find if there's already a prediction for this user and match
    query = predictions_ref.where('user_id', '==', user_id).where('match_id', '==', match_id).limit(1).get()
    
    if query:
        # Update the existing prediction
        for doc in query:
            doc_ref = doc.reference
            doc_ref.update({
                'home_goals': home_goals,
                'away_goals': away_goals,
                'points': 1  # You might want to adjust this based on your points logic
            })
    else:
        # Add a new prediction
        predictions_ref.add({
            'user_id': user_id,
            'match_id': match_id,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'points': 1  # You might want to adjust this based on your points logic
        })

def get_leaderboard():
    users_ref = db.collection('users')
    leaderboard = {}
    for user in users_ref.stream():
        user_data = user.to_dict()
        user_id = user_data.get('user_id', 'unknown user')
        leaderboard[user_id] = user_data.get('points', 0)
    return leaderboard

def get_predictions_match(match_id):
    predictions_ref = db.collection('predictions').where('match_id', '==', match_id)
    predictions = {}
    for prediction in predictions_ref.stream():
        predictions[prediction.id] = prediction.to_dict()
    return predictions

def get_predictions_user_match(user_id, match_id):
    predictions_ref = db.collection('predictions').where('user_id', '==', user_id).where('match_id', '==', match_id)
    prediction = None
    for prediction in predictions_ref.stream():
        prediction = prediction.to_dict()
    return prediction

def update_prediction_points(prediction_id, points):
    prediciton_ref = db.collection('predictions').document(prediction_id)
    prediciton_ref.update({
        'points': points
    })

def update_game_result(match_id, home_score, away_score, match_date, home_team, away_team):
    game_ref = db.collection('games').document(match_id)

    try:
        # Fetch the document
        doc = game_ref.get()
        
        if doc.exists:
            game_data = doc.to_dict()
            # Check if the 'finished' field exists
            if 'status' in game_data:
                status = game_data.get('status')
                if status == 'finished':
                    return True

    
    except Exception as e:
        print(f"An error occurred: {e}")


    game_ref.set({
        'home_score': home_score,
        'away_score': away_score,
        'status': 'finished',
        'date': match_date, 
        'home_team': home_team,
        'away_team': away_team
    })
    return False

def update_user_points(user_id, points):
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    if user.exists:
        user_data = user.to_dict()
        new_points = user_data.get('points', 0) + points
        user_ref.update({'points': new_points})
    else:
        user_ref.set({'points': points, 'user_id': user_id})

def get_past_predictions(user_id, begin_date, end_date):
    # Parse the date strings into datetime objects
    begin_date = datetime.strptime(begin_date, "%d/%m/%Y").date()
    end_date = datetime.strptime(end_date, "%d/%m/%Y").date()

    # Fetch all predictions for the given user_id
    predictions_ref = db.collection('predictions').where('user_id', '==', user_id)
    predictions = predictions_ref.stream()

    # Use a dictionary to group games by date and time
    result = defaultdict(lambda: defaultdict(list))

    # Define timezones
    utc = pytz.UTC
    belgian_tz = pytz.timezone('Europe/Brussels')

    for prediction in predictions:
        pred_data = prediction.to_dict()
        match_id = pred_data.get('match_id')

        # Fetch the actual game result from the 'games' collection
        game_ref = db.collection('games').document(match_id)
        game = game_ref.get()
        game_data = game.to_dict()

        # Check if the game has finished and is within the date range
        if game_data and game_data.get('status') == 'finished':
            # Parse the full UTC date-time string
            game_date_utc_str = game_data.get('date')
            game_date_utc = datetime.strptime(game_date_utc_str, "%Y-%m-%dT%H:%M:%SZ")
            game_date_utc = utc.localize(game_date_utc)  # Localize to UTC

            # Convert to Belgian time
            game_date_belgian = game_date_utc.astimezone(belgian_tz)

            # Extract date and time separately
            game_date = game_date_belgian.date()  # This is now a date object
            game_time = game_date_belgian.strftime("%H:%M")

            # Only consider games within the specified date range
            if begin_date <= game_date <= end_date:
                # Collect game information
                home_team = game_data.get('home_team')
                away_team = game_data.get('away_team')
                actual_home_goals = game_data.get('home_score')
                actual_away_goals = game_data.get('away_score')

                # Prediction data
                predicted_home_goals = pred_data.get('home_goals')
                predicted_away_goals = pred_data.get('away_goals')
                points = pred_data.get('points', 0)

                # Store the results grouped by date and time
                result[game_date.strftime("%d/%m/%Y")][game_time].append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'actual_home_goals': actual_home_goals,
                    'actual_away_goals': actual_away_goals,
                    'predicted_home_goals': predicted_home_goals,
                    'predicted_away_goals': predicted_away_goals,
                    'points': points
                })

    return result

def get_users_without_predictions(match_id):
    # Replace with actual Firestore logic to get user predictions
    all_users = get_all_registered_users()  # Assume this function returns a list of user IDs
    users_with_predictions = get_users_with_prediction_for_match(match_id)  # Assume this returns a list of user IDs who have predicted
    
    users_without_predictions = [user for user in all_users if user not in users_with_predictions]
    
    return users_without_predictions

def get_all_registered_users():
    # Reference to the 'users' collection
    users_collection_ref = db.collection('users')

    # Get all documents from the 'users' collection
    user_documents = users_collection_ref.stream()

    # List to store user IDs
    user_ids = []

    # Iterate through each document
    for user_doc in user_documents:
        user_data = user_doc.to_dict()
        
        # Check if the 'user_id' key exists in the document
        if 'user_id' in user_data:
            user_ids.append(user_data['user_id'])

    return user_ids

def get_users_with_prediction_for_match(match_id):
    # Reference to the 'predictions' collection
    predictions_collection_ref = db.collection('predictions')

    # Query to find documents where 'match_id' equals the provided match_id
    query = predictions_collection_ref.where('match_id', '==', match_id)

    # Execute the query and get matching documents
    prediction_documents = query.stream()

    # List to store user IDs
    user_ids = []

    # Iterate through each document
    for prediction_doc in prediction_documents:
        prediction_data = prediction_doc.to_dict()
        
        # Check if the 'user_id' key exists in the document
        if 'user_id' in prediction_data:
            user_ids.append(prediction_data['user_id'])

    return user_ids
