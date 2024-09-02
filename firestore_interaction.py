import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("discord-ucl-prediction-game-firebase-adminsdk-a7j85-104cd7d712.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()

def store_data():
    # Reference to the 'users' collection
    users_ref = db.collection('users')

    # Adding a document with a specific ID
    users_ref.document('user1').set({
        'name': 'John Doe',
        'email': 'john.doe@example.com'
    })

    # Adding a document with an auto-generated ID
    new_user_ref = users_ref.add({
        'name': 'Jane Doe',
        'email': 'jane.doe@example.com'
    })

    print(f'Added document with ID: {new_user_ref[1].id}')
