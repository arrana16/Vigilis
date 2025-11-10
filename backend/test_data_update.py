"""
Test script to verify data update flow works end-to-end.
This simulates the entire process:
1. Add transcript to database
2. Wait for write to propagate
3. Run fill agent analysis
4. Verify updates were made
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import add_transcript, collection
from fill_agent.fill_agent import update_dynamic_fields
import time
from datetime import datetime

def test_data_update_flow():
    """Test the complete data update flow"""
    
    # Test incident ID
    test_incident_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("=" * 80)
    print("TESTING DATA UPDATE FLOW")
    print("=" * 80)
    
    # Step 1: Create new incident with initial transcript
    print("\n1️⃣  Creating new incident with transcript...")
    add_transcript(
        id=test_incident_id,
        transcript="There's a fire at Mercedes-Benz Stadium in downtown Atlanta. Flames visible from the street.",
        caller="911_caller",
        convo="initial_call"
    )
    print(f"✅ Incident {test_incident_id} created")
    
    # Step 2: Verify transcript was written
    print("\n2️⃣  Verifying transcript was written to database...")
    time.sleep(1)  # Wait for write propagation
    incident = collection.find_one({"incident_id": test_incident_id})
    if incident:
        print(f"✅ Found incident in database")
        print(f"   Transcripts: {incident.get('transcripts', {})}")
    else:
        print(f"❌ ERROR: Incident not found in database!")
        return
    
    # Step 3: Run fill agent analysis
    print("\n3️⃣  Running fill agent analysis...")
    result = update_dynamic_fields(incident_id=test_incident_id)
    print(f"\n📊 Fill agent result:\n{result}")
    
    # Step 4: Verify updates were made
    print("\n4️⃣  Verifying updates were made to database...")
    time.sleep(0.5)  # Wait for write propagation
    updated_incident = collection.find_one({"incident_id": test_incident_id})
    
    if updated_incident:
        print(f"✅ Found updated incident in database")
        print(f"\n📋 Updated fields:")
        print(f"   Title: {updated_incident.get('title', 'NOT SET')}")
        print(f"   Location: {updated_incident.get('location', {}).get('address_text', 'NOT SET')}")
        print(f"   Coordinates: {updated_incident.get('location', {}).get('geojson', {}).get('coordinates', 'NOT SET')}")
        print(f"   Severity: {updated_incident.get('severity', 'NOT SET')}")
        print(f"   Summary: {updated_incident.get('current_summary', 'NOT SET')[:100]}...")
        print(f"   Last Updated: {updated_incident.get('last_summary_update_at', 'NOT SET')}")
        
        # Check if fields were actually updated
        issues = []
        if not updated_incident.get('title'):
            issues.append("Title is empty")
        if not updated_incident.get('location', {}).get('address_text'):
            issues.append("Location is empty")
        if not updated_incident.get('severity'):
            issues.append("Severity is empty")
        if not updated_incident.get('current_summary'):
            issues.append("Summary is empty")
        
        if issues:
            print(f"\n⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ ALL FIELDS WERE SUCCESSFULLY UPDATED!")
    else:
        print(f"❌ ERROR: Updated incident not found in database!")
    
    # Step 5: Cleanup
    print("\n5️⃣  Cleaning up test incident...")
    collection.delete_one({"incident_id": test_incident_id})
    print(f"✅ Test incident deleted")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_data_update_flow()
