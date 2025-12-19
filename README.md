# ActivExport - Strava Activity Extraction Tool

**Version:** 2.0
**Date:** December 2025
**Author:** Benoit Boucher

Python tool to fetch and analyze your Strava activities via the official API.
Export your data to multiple formats: JSON, CSV, and Markdown.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Output Formats](#output-formats)
6. [Available Scripts](#available-scripts)
7. [Project Structure](#project-structure)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### 1. Technical Environment

**Python**
- Version: Python 3.7 or higher
- Check: `python --version`

**Required Python Modules**
- `requests`: HTTP requests to Strava API
- `python-dotenv`: Environment variables management

These modules will be installed automatically via `requirements.txt`.

### 2. Strava Account

- Have an active Strava account
- Have activities recorded on Strava

### 3. Internet Access

- Required to communicate with Strava API
- Local port 8000 available (for OAuth callback)

---

## 📥 Installation

### Step 1: Clone/Download the Project

Place the `activexport/` directory wherever you want.

```
activexport/
├── .env.example                        # Configuration file template
├── .gitignore                          # Files to ignore (Git)
├── requirements.txt                    # Python dependencies
├── activexport_auth.py                 # Authentication script
├── activexport_fetch_activities.py     # Fetch activities
├── activexport_get_activity_details.py # Activity details
└── README.md                           # This documentation
```

### Step 2: Install Python Dependencies

```bash
cd activexport
pip install -r requirements.txt
```

**Verification:**
```bash
python -c "import requests; import dotenv; print('OK')"
```

If "OK" is displayed, the modules are properly installed.

---

## ⚙️ Configuration

### Step 1: Create a Strava Application

**1. Access the developer portal**

Go to: https://www.strava.com/settings/api

You must be logged into your Strava account.

**2. Create the application**

Click on **"Create an App"** and fill in:

| Field | Recommended Value |
|-------|-------------------|
| **Application Name** | `Running Analysis Tool` (or your name) |
| **Category** | `Data Importer` or `Visualizer` |
| **Club** | Leave empty (or your club) |
| **Website** | `http://localhost` |
| **Application Description** | `Personal running data analysis` |
| **Authorization Callback Domain** | `localhost` ⚠️ IMPORTANT |

⚠️ **Important note:** The "Authorization Callback Domain" field must be exactly `localhost` (without http://, without port).

**3. Accept the terms**

- Check "I agree to Strava API Agreement"
- Click on **"Create"**

**4. Retrieve your Credentials**

After creation, Strava displays:

```
Client ID:          [a number, e.g.: 123456]
Client Secret:      [an alphanumeric string]
```

⚠️ **IMPORTANT:**
- Note these 2 values carefully
- NEVER share them publicly
- They are personal and confidential

---

### Step 2: Configure the `.env` File

**1. Create the `.env` file**

In the `activexport/` directory, create a file named `.env` (without extension).

**On Windows:**
```bash
copy NUL .env
```

**On Linux/Mac:**
```bash
touch .env
```

**2. Edit the `.env` file**

Open `.env` with a text editor and add:

```bash
# Strava API Credentials
# ⚠️ NEVER COMMIT THIS FILE TO GIT

STRAVA_CLIENT_ID=YOUR_CLIENT_ID
STRAVA_CLIENT_SECRET=YOUR_CLIENT_SECRET

# Tokens will be added automatically after first authentication
STRAVA_ACCESS_TOKEN=
STRAVA_REFRESH_TOKEN=
STRAVA_TOKEN_EXPIRES_AT=
```

Replace:
- `YOUR_CLIENT_ID` with the Client ID provided by Strava
- `YOUR_CLIENT_SECRET` with the Client Secret provided by Strava

**Example (fictional values):**
```bash
STRAVA_CLIENT_ID=123456
STRAVA_CLIENT_SECRET=abc123def456ghi789jkl012mno345pqr678stu90
```

**3. Save**

The `.env` file is automatically protected by `.gitignore`.

---

### Step 3: Initial Authentication

**1. Run the authentication script**

```bash
python activexport_auth.py
```

**2. What will happen?**

The script will:
1. Open your browser automatically
2. Redirect you to Strava to authorize the application
3. Start a local server (http://localhost:8000)
4. Wait for you to accept the authorization on Strava

**3. On the Strava page**

- Check the requested permissions:
  - `read`: Read your public data
  - `activity:read_all`: Read all your activities
  - `profile:read_all`: Read your complete profile
- Click on **"Authorize"**

**4. Success**

The browser will display:
```
Strava authentication successful!
You can close this window and return to the terminal.
```

In the terminal:
```
============================================================
AUTHENTICATION SUCCESSFUL!
============================================================

Athlete: [Your Name]
Token expires at: [Date]

Tokens saved to: activexport_tokens.json
```

**5. Created files**

A `activexport_tokens.json` file has been created automatically. It contains your access tokens.

⚠️ **NEVER share this file** (protected by `.gitignore`).

---

### Step 4: Test the Connection

```bash
python activexport_auth.py test
```

**Expected result:**
```
============================================================
STRAVA API CONNECTION TEST
============================================================

API connection successful!

Athlete Profile:
   Name: [Your Name]
   City: [Your City]
   Country: France
   Weight: [Your Weight] kg
   ...

API ready to fetch your activities!
```

✅ **If this message is displayed, the API is configured!**

---

## 🚀 Usage

### Getting Help

Display help for any script:

```bash
python activexport_fetch_activities.py --help
python activexport_get_activity_details.py --help
```

---

### 1. Fetch All Your Activities

#### Basic Usage (Display Only)

```bash
python activexport_fetch_activities.py
```

**What the script does:**
- Fetches ALL your activities since the creation of your Strava account
- Displays global statistics on screen
- **No files created** (stdout only)

**Example output:**
```
============================================================
FETCHING STRAVA ACTIVITIES
============================================================

[Page 1] Fetching max 200 activities...
      -> 200 activities fetched
...
TOTAL: 1527 activities fetched

============================================================
ACTIVITY ANALYSIS
============================================================

Distribution by sport type:
   Run                 :  786 activities
   TrailRun            :  132 activities
   ...

Global statistics:
   Total distance: 15540.1 km
   Total elevation: 174412 m
   Total time: 1629.4 hours
```

---

#### Export to Files

**Export to JSON:**
```bash
python activexport_fetch_activities.py -f json
```
Creates: `./output/activexport_activities_YYYYMMDD_HHMMSS.json`

**Export to CSV:**
```bash
python activexport_fetch_activities.py -f csv
```
Creates: `./output/activexport_activities_YYYYMMDD_HHMMSS.csv`

**Export to Markdown:**
```bash
python activexport_fetch_activities.py -f md
```
Creates: `./output/activexport_activities_YYYYMMDD_HHMMSS.md`

**Export to multiple formats:**
```bash
python activexport_fetch_activities.py -f json -f csv -f md
```
Creates all 3 files simultaneously.

---

#### Custom Output Directory

```bash
python activexport_fetch_activities.py -f json -o ./my_exports/
```

Saves the JSON file to `./my_exports/` instead of `./output/`.

---

### 2. Search for Activities by Name

```bash
python activexport_fetch_activities.py "search term"
```

**Examples:**

```bash
# Find all "Sancy" trails
python activexport_fetch_activities.py "sancy"

# Find all "Team RM" outings
python activexport_fetch_activities.py "Team RM"

# Find and export to JSON
python activexport_fetch_activities.py "maines" -f json
```

**Example output:**
```
3 activity(ies) found containing 'sancy':

   [24/09/2022] Trail du Sancy
      33.15 km - 2029 m elevation
      ID: 7812345678
   ...
```

When using `-f`, only the matching activities are exported.

---

### 3. Fetch Activity Details

#### Basic Usage (Display Only)

```bash
python activexport_get_activity_details.py <activity_id>
```

**Example:**
```bash
python activexport_get_activity_details.py 6018412458
```

**Output:**
```
============================================================
ACTIVITY DETAILS
============================================================

Name: Trail de la Digue
Date: 25/09/2021 10:00
Type: TrailRun
ID: 6018412458

METRICS:
   Distance: 51.00 km
   Elevation gain: 0 m D+
   Time: 06h04'20"
   Average pace: 7'08"/km

EQUIPMENT:
   HOKA Challenger ATR 5 (1041.5 km)
```

---

#### Export to Files

**Export to JSON:**
```bash
python activexport_get_activity_details.py 6018412458 -f json
```
Creates: `./output/activity_6018412458.json`

**Export to Markdown:**
```bash
python activexport_get_activity_details.py 6018412458 -f md
```
Creates: `./output/activity_6018412458.md`

**Export to both:**
```bash
python activexport_get_activity_details.py 6018412458 -f json -f md
```

**Custom output directory:**
```bash
python activexport_get_activity_details.py 6018412458 -f json -o ./my_data/
```

---

## 📊 Output Formats

### JSON Format

**Structure for activities:**
```json
{
  "metadata": {
    "export_date": "2025-12-05T19:30:00",
    "total_activities": 1527,
    "source": "Strava API v3"
  },
  "activities": [
    {
      "id": 6018412458,
      "name": "Trail de la Digue",
      "sport_type": "TrailRun",
      "distance": 51000,
      "total_elevation_gain": 0,
      "moving_time": 21860,
      ...
    }
  ]
}
```

**Use cases:**
- Data analysis with Python/R
- Import into databases
- Machine learning datasets
- Programmatic processing

---

### CSV Format

**Columns:**
```csv
date,name,type,distance_km,elevation_m,moving_time,elapsed_time,avg_pace,avg_hr,max_hr
2025-12-05,Morning Run,Run,10.5,120,3600,3720,5'43",145,165
2025-12-04,Trail,TrailRun,17.0,300,7920,8100,7'46",142,170
```

**Use cases:**
- Open in Excel/LibreOffice Calc
- Import into Google Sheets
- Quick data visualization
- Pivot tables and charts

---

### Markdown Format

**Example for activities list:**
```markdown
# Strava Activities Export
**Generated:** 2025-12-05 19:30:00
**Total Activities:** 1527

## Summary Statistics
- **Total Distance:** 15,540.1 km
- **Total Elevation:** 174,412 m
- **Total Time:** 1,629.4 hours

## Activities by Sport Type
| Sport Type | Count |
|------------|-------|
| Run | 786 |
| TrailRun | 132 |

## Recent Activities
| Date | Name | Type | Distance | Elevation | Time |
|------|------|------|----------|-----------|------|
| 2025-12-05 | Morning Run | Run | 10.5 km | 120 m | 1h00' |
```

**Example for activity details:**
```markdown
# Activity Details: Trail de la Digue
**ID:** 6018412458
**Date:** 2021-09-25 10:00
**Type:** TrailRun

## Metrics
- **Distance:** 51.00 km
- **Elevation gain:** 0 m D+
- **Time:** 06h04'20"
- **Average pace:** 7'08"/km
```

**Use cases:**
- Documentation
- Blog posts
- GitHub READMEs
- Easy to read and share

---

## 📚 Available Scripts

### `activexport_auth.py`

**Function:** OAuth2 authentication management

**Commands:**
```bash
python activexport_auth.py        # Initial authentication
python activexport_auth.py test   # Test the connection
```

**Features:**
- Opens browser for Strava authorization
- Exchanges authorization code for tokens
- Automatically refreshes expired tokens
- Saves tokens to `activexport_tokens.json`

---

### `activexport_fetch_activities.py`

**Function:** Fetch all activities and export to multiple formats

**Usage:**
```bash
python activexport_fetch_activities.py [OPTIONS] [SEARCH]
```

**Options:**
- `-h, --help`: Show help message
- `-f, --format FORMAT`: Output format (json, csv, md). Can be used multiple times
- `-o, --output DIR`: Output directory (default: `./output`)

**Examples:**
```bash
# Display only (no export)
python activexport_fetch_activities.py

# Export to JSON
python activexport_fetch_activities.py -f json

# Export to all formats
python activexport_fetch_activities.py -f json -f csv -f md

# Search and export
python activexport_fetch_activities.py "trail" -f json

# Custom output directory
python activexport_fetch_activities.py -f json -o ./my_exports/
```

**Features:**
- Automatic pagination (200 activities/page)
- API limits management (automatic pause)
- Multiple export formats: JSON, CSV, Markdown
- Analysis by sport type
- Global statistics (distance, elevation, time)
- Search by activity name
- Customizable output directory

---

### `activexport_get_activity_details.py`

**Function:** Complete details of a specific activity

**Usage:**
```bash
python activexport_get_activity_details.py ACTIVITY_ID [OPTIONS]
```

**Options:**
- `-h, --help`: Show help message
- `-f, --format FORMAT`: Output format (json, md). Can be used multiple times
- `-o, --output DIR`: Output directory (default: `./output`)

**Examples:**
```bash
# Display only
python activexport_get_activity_details.py 6018412458

# Export to JSON
python activexport_get_activity_details.py 6018412458 -f json

# Export to JSON and Markdown
python activexport_get_activity_details.py 6018412458 -f json -f md

# Custom output directory
python activexport_get_activity_details.py 6018412458 -f json -o ./data/
```

**Extracted data:**
- Name, date, type, ID
- Distance, elevation, time
- Average pace
- Average/max HR (if available)
- Min/max altitude
- Cadence
- Equipment used
- Description/comments

---

## 📁 Project Structure

```
activexport/
├── .env                                # ⚠️ Credentials (DO NOT COMMIT)
├── .env.example                        # .env template
├── .gitignore                          # Sensitive files protection
├── requirements.txt                    # Python dependencies
├── activexport_tokens.json             # ⚠️ OAuth2 tokens (DO NOT COMMIT)
├── activexport_auth.py                 # OAuth2 authentication
├── activexport_fetch_activities.py     # Fetch activities
├── activexport_get_activity_details.py # Activity details
└── README.md                           # Documentation

output/                              # Default output directory
├── activexport_activities_YYYYMMDD_HHMMSS.json
├── activexport_activities_YYYYMMDD_HHMMSS.csv
├── activexport_activities_YYYYMMDD_HHMMSS.md
├── activity_XXXXXXXXX.json
└── activity_XXXXXXXXX.md
```

### Sensitive Files (NEVER COMMIT)

- `.env`: Your API credentials
- `activexport_tokens.json`: Your access tokens
- `output/`: Your personal activity data

These files are automatically protected by `.gitignore`.

---

## ⚙️ Token Management

### Expiration and Refresh

**Strava tokens expire every 6 hours.**

✅ **Good news:** Refresh is AUTOMATIC!

The `activexport_auth.py` script contains the `get_valid_access_token()` function which:
1. Checks if the token is expired
2. Refreshes it automatically if necessary
3. Saves the new token

**You don't have to do anything!**

### Revoke Access

If you want to revoke application access:

1. Go to https://www.strava.com/settings/apps
2. Find your application
3. Click on "Revoke Access"

To reactivate, simply run again:
```bash
python activexport_auth.py
```

---

## 🚨 Troubleshooting

### Error: "Module not found"

**Cause:** Python dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

---

### Error: "No token found"

**Cause:** Initial authentication not performed

**Solution:**
```bash
python activexport_auth.py
```

---

### Error 401 Unauthorized

**Cause:** Invalid or revoked token

**Solution:**
```bash
# Delete the tokens file
rm activexport_tokens.json  # Linux/Mac
del activexport_tokens.json  # Windows

# Re-authenticate
python activexport_auth.py
```

---

### Error 429 Too Many Requests

**Cause:** Strava API limit reached

**Limits:**
- 100 requests / 15 minutes (read)
- 1000 requests / day (read)

**Solution:** Wait 15 minutes (automatic handling in scripts)

---

### Browser doesn't open

**Cause:** Automatic browser opening issue

**Manual solution:**

1. Copy the URL displayed in the terminal
2. Open it manually in your browser
3. Authorize the application
4. You will be redirected to localhost:8000

---

### Error "Can't connect to localhost:8000"

**Cause:** Port 8000 already in use

**Solution:**
```bash
# Find process using port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Stop the process or change port
```

---

### CSV/Excel Encoding Issues

**Symptom:** Special characters display incorrectly in Excel

**Cause:** Excel doesn't automatically detect UTF-8

**Solution:**
1. Open Excel
2. Data → Get Data → From Text/CSV
3. Select encoding: UTF-8
4. Import

Or open directly in Google Sheets (automatic UTF-8 detection).

---

## 📊 Strava API Limits

### Quotas

| Type | Limit | Period |
|------|-------|--------|
| Read | 100 requests | 15 minutes |
| Read | 1000 requests | 24 hours |
| Global | 200 requests | 15 minutes |
| Global | 2000 requests | 24 hours |

### Available Data

✅ **Accessible via API:**
- All activities (complete history)
- Activity details (distance, time, HR, etc.)
- Athlete profile
- Equipment/shoes
- Crossed segments
- Photos

❌ **Not accessible:**
- Private activities of other athletes
- High-frequency stream data (requires additional scope)

---

## 🔒 Security and Privacy

### Data Protection

**Files to NEVER share/commit:**
- `.env`: Your credentials
- `activexport_tokens.json`: Your access tokens
- `output/`: Your personal activity data

The `.gitignore` file automatically protects these files if you use Git.

### Requested Permissions

The application only requests:
- `read`: Read public data
- `activity:read_all`: Read all your activities (even private)
- `profile:read_all`: Read your complete profile

**No write or modification permissions.**

---

## 📖 Resources

### Strava API Documentation

- **API Reference:** https://developers.strava.com/docs/reference/
- **OAuth Guide:** https://developers.strava.com/docs/authentication/
- **Playground:** https://developers.strava.com/playground/

### Support

- Python Documentation: https://docs.python.org/3/
- Requests Documentation: https://requests.readthedocs.io/

---

## 📝 Version Notes

### v2.0 - December 2025

**New Features:**
- ✅ Multi-format export: JSON, CSV, Markdown
- ✅ Customizable output directory
- ✅ `--help` option for all scripts
- ✅ Multiple formats in single export
- ✅ Improved command-line interface

**Previous Features (v1.0):**
- ✅ Complete OAuth2 authentication
- ✅ Fetch all activities
- ✅ Search by name
- ✅ Activity details
- ✅ Automatic token refresh
- ✅ API limits management

---

**Document created on:** December 5, 2025
**Last updated:** December 5, 2025
**Author:** Benoit Boucher

---

## 💡 Usage Tips

**First use:**
1. Install dependencies (`pip install -r requirements.txt`)
2. Create Strava application
3. Configure `.env`
4. Authenticate (`python activexport_auth.py`)
5. Test (`python activexport_auth.py test`)
6. Fetch activities (`python activexport_fetch_activities.py`)

**Daily usage:**
```bash
# Display activities
python activexport_fetch_activities.py

# Export to JSON and CSV
python activexport_fetch_activities.py -f json -f csv

# Search and export
python activexport_fetch_activities.py "trail" -f json

# Get activity details
python activexport_get_activity_details.py 6018412458 -f md
```

**Maintenance:**
- Tokens refresh automatically
- No action required except manual revocation

---

**Happy running! 🏃‍♂️**
