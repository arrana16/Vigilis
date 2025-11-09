import os
import pymongo
import requests
import time  # Import the time module for sleeping
from dotenv import load_dotenv
from bson.objectid import ObjectId

def process_change(change):
    """
    This function processes a single change event.
    """
    print(f"\n--- CHANGE DETECTED (Type: {change['operationType']}) ---")
    
    incident_id_obj = change['documentKey']['_id']
    incident_id_str = str(incident_id_obj)
    
    print(f"Incident ID: {incident_id_str}")

    payload = {"incident_id": incident_id_str}
    
    # Load API endpoints from environment
    NEW_INCIDENT_API_URL = os.getenv("NEW_INCIDENT_API_URL", "http://localhost:8000/internal/notify-clients")
    UPDATE_INCIDENT_API_URL = os.getenv("UPDATE_INCIDENT_API_URL", "http://localhost:8000/internal/notify-clients")
    
    # Headers with secret
    headers = {
        "x-trigger-secret": "vigilis_secret_2024"
    }

    # --- Handle 'insert' (New Document) ---
    if change['operationType'] == 'insert':
        print(f"New incident created. Calling: {NEW_INCIDENT_API_URL}")
        try:
            requests.post(NEW_INCIDENT_API_URL, json=payload, headers=headers)
        except Exception as e:
            print(f"Error calling new incident endpoint: {e}")
        return # Go to the next change

    # --- Handle 'update' (Existing Document) ---
    if change['operationType'] == 'update':
        # Prevent the infinite loop
        updated_fields = change['updateDescription']['updatedFields'].keys()
        
        is_self_update = all(
            key.startswith('generated_suggestions') or 
            key == 'last_suggestion_update_at' 
            for key in updated_fields
        )

        if is_self_update:
            print("Change was from the agent itself. Ignoring.")
            return

        # It's a real update! Call the update endpoint.
        print(f"Incident updated. Calling: {UPDATE_INCIDENT_API_URL}")
        try:
            requests.post(UPDATE_INCIDENT_API_URL, json=payload, headers=headers)
        except Exception as e:
            print(f"Error calling update incident endpoint: {e}")

def main_watcher():
    """
    Connects to MongoDB and watches for ANY updates OR inserts
    in the active_incidents collection.
    
    This function will run forever until you stop it with C_c.
    """
    print("Starting local watcher...")
    load_dotenv()
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

    if not MONGO_PASSWORD:
        raise EnvironmentError("MONGO_PASSWORD not found in .env file")

    # Build MongoDB URI
    MONGO_URI = f"mongodb+srv://cyrus:{MONGO_PASSWORD}@cluster0.rznqb.mongodb.net/?appName=Cluster0"
    
    client = pymongo.MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client["dispatch_db"]
    collection = db["active_incidents"]

    print("Successfully connected to MongoDB.")
    print(f"Watching for 'insert' and 'update' operations...")
    print("Press C_c to stop.")

    pipeline = [
        {'$match': {
            'operationType': {'$in': ['insert', 'update']}
        }}
    ]

    try:
        while True:  # <-- This makes the watcher run forever
            print("Opening new change stream...")
            print(f"Pipeline: {pipeline}")
            try:
                with collection.watch(pipeline) as stream:
                    print("Change stream is now active and waiting for events...")
                    for change in stream:
                        process_change(change) # Process the change
                        
            except pymongo.errors.PyMongoError as e:
                print(f"Change stream error: {e}. Reconnecting in 5 seconds...")
                time.sleep(5) # Wait 5 seconds before retrying
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Restarting loop...")
                time.sleep(5)

    except KeyboardInterrupt:
        print("Watcher stopped by user.")
    finally:
        client.close()
        print("Watcher connection closed.")

if __name__ == "__main__":
    main_watcher()