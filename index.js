// app.js
const { connectToDatabase } = require("./db");
const { ObjectId } = require("mongodb"); // We need this to query by _id

/**
 * Creates a new incident when a 911 call comes in.
 */
async function createNewIncident(db) {
  console.log("Creating new incident...");
  const collection = db.collection("active_incidents");

  const newIncident = {
    incident_id: "F251107-0124", // You'd generate this dynamically
    title: "Aniketh Getting Beaten Up",
    severity: "low", // Can be: "low", "medium", "high"
    status: "active",
    created_at: new Date().toISOString(),
    location: {
      address_text: "67 Oak Ave, Atlanta, GA, 30303",
      geojson: { type: "Point", coordinates: [-84.3880, 33.7490] }
    },
    transcripts: {
      "911_call": "Operator: 911, what's your emergency?\nCaller: My friend Aniketh is getting beat up by a thug!",
      // Other feeds are empty to start
      "Patrol_12_comm": "",
      "Engine_01_comm": ""
    },
    current_summary: "Initial report of a house fire at 456 Oak Ave.",
    last_summary_update_at: new Date().toISOString()
  };

  try {
    const result = await collection.insertOne(newIncident);
    console.log(`New incident created with _id: ${result.insertedId}`);
    return result.insertedId; // Return the new ID so we can use it
  } catch (error) {
    console.error("Error creating incident:", error);
  }
}

/*
/**
 * Appends a new line of text to a specific transcript feed
 * inside an existing incident document.
 */
/*
async function appendToTranscript(db, incidentId, transcriptKey, newText) {
  console.log(`Appending to ${transcriptKey} for incident ${incidentId}...`);
  const collection = db.collection("active_incidents");

  // We must convert the string ID to a MongoDB ObjectId
  const query = { _id: new ObjectId(incidentId) };

  try {
    // 1. FIND the document
    const incident = await collection.findOne(query);

    if (!incident) {
      console.log("Incident not found.");
      return;
    }
    
    // 2. MODIFY the string in our code
    const oldText = incident.transcripts[transcriptKey];
    const updatedText = oldText + "\n" + newText; // The "append" logic

    // 3. UPDATE the document with the new string
    const updateResult = await collection.updateOne(
      query,
      { $set: { [`transcripts.${transcriptKey}`]: updatedText } }
    );

    console.log(`Successfully appended. ${updateResult.modifiedCount} document(s) updated.`);

  } catch (error) {
    console.error("Error appending to transcript:", error);
  }
}
*/

// --- NEW CODE: Simple update to specific incident ---
async function appendToTranscript(db, incidentId, transcriptKey, newText) {
  console.log(`Appending to ${transcriptKey} for incident ${incidentId}...`);
  const collection = db.collection("active_incidents");

  // We must convert the string ID to a MongoDB ObjectId
  const query = { _id: new ObjectId(incidentId) };

  try {
    // 1. FIND the document
    const incident = await collection.findOne(query);

    if (!incident) {
      console.log("Incident not found.");
      return;
    }
    
    // 2. MODIFY the string in our code
    const oldText = incident.transcripts[transcriptKey];
    const updatedText = oldText + "\n" + newText; // The "append" logic

    // 3. UPDATE the document with the new string
    const updateResult = await collection.updateOne(
      query,
      { $set: { [`transcripts.${transcriptKey}`]: updatedText } }
    );

    console.log(`Successfully appended. ${updateResult.modifiedCount} document(s) updated.`);

  } catch (error) {
    console.error("Error appending to transcript:", error);
  }
}

async function main() {
  const db = await connectToDatabase();

  // Create a new incident
  await createNewIncident(db);
}

main();