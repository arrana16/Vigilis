// db.js
const { MongoClient, ServerApiVersion } = require("mongodb");
require('dotenv').config();

// -------------------------------------------------------------------
// Connection string using environment variables
const uri = `mongodb+srv://cyrus:${process.env.MONGO_PASSWORD}@cluster0.rznqb.mongodb.net/?appName=Cluster0`;
// -------------------------------------------------------------------

// Create a MongoClient with a MongoClientOptions object to set the Stable API version
const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  }
});

// This function connects to the DB and returns the "dispatch_db" database object
async function connectToDatabase() {
  try {
    await client.connect();
    console.log("Successfully connected to MongoDB Atlas!");
    
    const database = client.db("dispatch_db"); // Our database name
    return database;

  } catch (error) {
    console.error("Error connecting to MongoDB:", error);
    await client.close();
    process.exit(1); // Exit the app if connection fails
  }
}

module.exports = { connectToDatabase };