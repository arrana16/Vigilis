# MongoDB SSL Certificate Error - Troubleshooting Guide

## Problem

You're seeing an SSL certificate verification error when trying to connect to MongoDB Atlas:

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

## What Causes This?

This error occurs because Python can't verify the SSL certificate presented by MongoDB Atlas. This is common on macOS, especially when:

-   Python is installed from python.org
-   SSL certificates aren't properly configured
-   The certifi package isn't installed

## Solutions (Try in Order)

### ✅ Solution 1: Use Certifi (IMPLEMENTED)

We've updated `db.py` to use the `certifi` package which provides a trusted SSL certificate bundle.

**What we changed:**

```python
import certifi

client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()  # Use certifi's certificate bundle
)
```

**To apply:**

```bash
pip install certifi
# Or if using the virtual environment:
source venv/bin/activate
pip install -r requirements.txt
```

Then restart your FastAPI server.

### Solution 2: Install macOS SSL Certificates

If you're on macOS and Solution 1 doesn't work, install Python's SSL certificates:

```bash
# Find your Python version
ls /Applications/ | grep Python

# Run the certificate installer (adjust version number)
/Applications/Python\ 3.11/Install\ Certificates.command
# or
/Applications/Python\ 3.12/Install\ Certificates.command
```

### Solution 3: Update pip and certifi

Make sure you have the latest versions:

```bash
pip install --upgrade pip certifi
```

### Solution 4: Check Your Connection String

Verify your MongoDB connection string in `.env`:

```env
# Should look like this:
MONGO_URI=mongodb+srv://username:password@cluster0.rznqb.mongodb.net/?retryWrites=true&w=majority

# NOT like this (mongodb:// instead of mongodb+srv://):
MONGO_URI=mongodb://username:password@cluster0.rznqb.mongodb.net/
```

### Solution 5: Disable SSL Verification (DEVELOPMENT ONLY)

**⚠️ Only use this for local development, NEVER in production!**

If you need a quick workaround for development:

```python
# In db.py
client = MongoClient(
    MONGO_URI,
    server_api=ServerApi('1'),
    tls=True,
    tlsAllowInvalidCertificates=True  # DEVELOPMENT ONLY!
)
```

### Solution 6: Network/Firewall Issues

Check if your network is blocking MongoDB Atlas:

1. **Whitelist your IP in MongoDB Atlas:**

    - Go to MongoDB Atlas dashboard
    - Navigate to Network Access
    - Add your current IP address or use `0.0.0.0/0` (for development)

2. **Test connectivity:**
    ```bash
    ping cluster0-shard-00-00.rznqb.mongodb.net
    ```

## Verify the Fix

After applying a solution, test the connection:

```python
# test_connection.py
from backend.db import client

try:
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

Run it:

```bash
python test_connection.py
```

Or test via the API:

```bash
# Start the server
uvicorn backend.api:app --reload

# In another terminal, test an endpoint
curl http://localhost:8000/police/cars
```

## Additional Tips

### If Using Virtual Environment

Always activate it first:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### If Using System Python

You might need to use `pip3` or `python3`:

```bash
python3 -m pip install certifi
```

### Check Python Location

```bash
which python
# or
which python3
```

Make sure you're using the Python from your virtual environment.

## What We Recommend

For most users, **Solution 1 (using certifi)** is the best approach because:

-   ✅ Works across platforms (macOS, Linux, Windows)
-   ✅ Doesn't require admin privileges
-   ✅ Properly validates SSL certificates
-   ✅ Safe for production use

## Still Having Issues?

1. **Check MongoDB Atlas Status:**

    - Visit https://status.mongodb.com/

2. **Verify credentials:**

    - Make sure username/password in `.env` are correct
    - Ensure the database user has proper permissions

3. **Check Python version:**

    ```bash
    python --version
    # Should be Python 3.8 or higher
    ```

4. **Reinstall pymongo:**
    ```bash
    pip uninstall pymongo
    pip install pymongo
    ```

## Common Errors and Fixes

### "ModuleNotFoundError: No module named 'certifi'"

```bash
pip install certifi
```

### "Could not find a suitable TLS CA certificate bundle"

```bash
pip install --upgrade certifi
```

### "Access denied" or "Authentication failed"

-   Check your MongoDB username and password in `.env`
-   Make sure the user exists in MongoDB Atlas
-   Verify the user has read/write permissions

## Need More Help?

Check these resources:

-   [MongoDB Connection Issues](https://www.mongodb.com/docs/atlas/troubleshoot-connection/)
-   [Python SSL Documentation](https://docs.python.org/3/library/ssl.html)
-   [Certifi Documentation](https://github.com/certifi/python-certifi)
