"""
Utilities.
"""

import sys
import json
from datetime import date
from dateutil.parser import parse


def load_incident_data():
    """Load the incident history from JSON file"""
    try:
        with open('last_incident.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "incidents": []
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing last_incident.json: {e}")
        sys.exit(1)


def save_incident_data(data):
    """Save incident history back to JSON file"""
    with open('last_incident.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_last_incident_date(incidents):
    """Get the date of the most recent incident"""
    if not incidents:
        return None
    # Sort incidents by date (most recent first)
    sorted_incidents = sorted(incidents, key=lambda x: x['date'], reverse=True)
    return sorted_incidents[0]['date']


def calculate_days_since_incident(incidents, reference_date=None):
    """Calculate days since the most recent incident. Optionally pass a reference date to use instead of today."""
    last_incident_date_str = get_last_incident_date(incidents)
    if not last_incident_date_str:
        return 0
    try:
        last_incident_date = parse(last_incident_date_str).date()
        if reference_date is not None:
            ref_date = reference_date
        else:
            ref_date = date.today()
        delta = ref_date - last_incident_date
        return delta.days
    except ValueError as e:
        print(f"Error parsing date '{last_incident_date_str}': {e}")
        sys.exit(1)


def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: Configuration file not found at project root")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
