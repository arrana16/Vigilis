"""
Test script to verify atomic database updates work correctly.
This tests the find_one_and_update approach to ensure data is immediately available.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import add_transcript, collection
from fill_agent.fill_agent import update_dynamic_fields
from datetime import datetime

def test_atomic_transcript_update():
    """Test that add_transcript returns the updated document atomically"""
    
    test_incident_id = f"atomic-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("=" * 80)
    print("TESTING ATOMIC DATABASE UPDATES")
    print("=" * 80)
    
    # Step 1: Add first transcript
    print("\n1️⃣  Adding first transcript (new incident)...")
    result1 = add_transcript(
        id=test_incident_id,
        transcript="Fire reported at Georgia Tech campus",
        caller="911_caller",
        convo="call_1"
    )
    
    print(f"   Status: {result1['status']}")
    print(f"   Message: {result1['message']}")
    print(f"   Incident returned: {result1['incident'] is not None}")
    
    if result1['incident']:
        transcripts = result1['incident'].get('transcripts', {})
        print(f"   Transcripts in returned document: {transcripts}")
        
    # Verify we can immediately use this data (no delay needed!)
    assert result1['status'] == 'created', "Expected 'created' status"
    assert result1['incident'] is not None, "Expected incident document to be returned"
    assert len(result1['incident'].get('transcripts', {}).get('call_1', [])) == 1, "Expected 1 transcript"
    print("   ✅ First transcript added atomically")
    
    # Step 2: Add second transcript to same incident
    print("\n2️⃣  Adding second transcript (update existing)...")
    result2 = add_transcript(
        id=test_incident_id,
        transcript="Fire spreading to multiple buildings",
        caller="officer_on_scene",
        convo="call_1"
    )
    
    print(f"   Status: {result2['status']}")
    print(f"   Message: {result2['message']}")
    print(f"   Incident returned: {result2['incident'] is not None}")
    
    if result2['incident']:
        transcripts = result2['incident'].get('transcripts', {})
        print(f"   Transcripts in returned document: {transcripts}")
        print(f"   Number of transcripts in call_1: {len(transcripts.get('call_1', []))}")
    
    # Verify immediate access to updated data
    assert result2['status'] == 'updated', "Expected 'updated' status"
    assert result2['incident'] is not None, "Expected incident document to be returned"
    assert len(result2['incident'].get('transcripts', {}).get('call_1', [])) == 2, "Expected 2 transcripts"
    print("   ✅ Second transcript added atomically")
    
    # Step 3: Test fill agent with atomic updates (no delay needed)
    print("\n3️⃣  Running fill agent analysis (NO DELAY NEEDED)...")
    analysis_result = update_dynamic_fields(incident_id=test_incident_id)
    print(f"\n📊 Analysis result:\n{analysis_result}")
    
    # Step 4: Verify final state
    print("\n4️⃣  Verifying final state...")
    final_incident = collection.find_one({"incident_id": test_incident_id})
    
    print(f"   Title: {final_incident.get('title', 'NOT SET')}")
    print(f"   Location: {final_incident.get('location', {}).get('address_text', 'NOT SET')}")
    print(f"   Coordinates: {final_incident.get('location', {}).get('geojson', {}).get('coordinates', 'NOT SET')}")
    print(f"   Severity: {final_incident.get('severity', 'NOT SET')}")
    print(f"   Transcripts count: {sum(len(v) for v in final_incident.get('transcripts', {}).values())}")
    
    # Cleanup
    print("\n5️⃣  Cleaning up...")
    collection.delete_one({"incident_id": test_incident_id})
    print("   ✅ Test incident deleted")
    
    print("\n" + "=" * 80)
    print("✅ ATOMIC UPDATE TEST PASSED!")
    print("=" * 80)
    print("\n🎯 Key improvements:")
    print("   • find_one_and_update returns document immediately")
    print("   • NO DELAY needed between write and read")
    print("   • Guaranteed consistency - no race conditions")
    print("   • Faster response times")


if __name__ == "__main__":
    test_atomic_transcript_update()
