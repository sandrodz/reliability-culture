"""
Daily incident counter script for GitLab CI/CD
Calculates days since last incident and posts to Slack
"""

import json
import os
import sys
from datetime import date
from dateutil.parser import parse
import requests


def load_incident_data():
    """Load the incident history from JSON file"""
    try:
        with open('last_incident.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: last_incident.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing last_incident.json: {e}")
        sys.exit(1)


def get_last_incident_date(incidents):
    """Get the date of the most recent incident"""
    if not incidents:
        return None

    # Sort incidents by date (most recent first)
    sorted_incidents = sorted(incidents, key=lambda x: x['date'], reverse=True)
    return sorted_incidents[0]['date']


def calculate_days_since_incident(incidents):
    """Calculate days since the most recent incident"""
    last_incident_date_str = get_last_incident_date(incidents)
    if not last_incident_date_str:
        return 0

    try:
        last_incident_date = parse(last_incident_date_str).date()
        today = date.today()
        delta = today - last_incident_date
        return delta.days
    except ValueError as e:
        print(f"Error parsing date '{last_incident_date_str}': {e}")
        sys.exit(1)


def calculate_record_streak(incidents):
    """Calculate the longest streak between any two incidents"""
    if len(incidents) < 2:
        # If we have 0 or 1 incidents, current streak is the record
        return calculate_days_since_incident(incidents)
    
    # Sort incidents by date (oldest first)
    sorted_incidents = sorted(incidents, key=lambda x: x['date'])
    
    max_streak = 0
    
    # Calculate streaks between consecutive incidents
    for i in range(len(sorted_incidents) - 1):
        start_date = parse(sorted_incidents[i]['date']).date()
        end_date = parse(sorted_incidents[i + 1]['date']).date()
        streak = (end_date - start_date).days
        max_streak = max(max_streak, streak)
    
    # Also check current streak (from last incident to today)
    current_streak = calculate_days_since_incident(incidents)
    max_streak = max(max_streak, current_streak)
    
    return max_streak


def get_milestone_message(days):
    """Get special milestone message if applicable"""
    milestones = {
        10: "🎉 10 Days! Team shoutout time! 🎉",
        30: "☕ 30 Days! Virtual coffee vouchers for everyone! ☕",
        50: "🍽️ 50 Days! Team lunch celebration! 🍽️",
        100: "🎁 100 Days! Custom swag incoming! 🎁"
    }
    
    if days in milestones:
        return milestones[days]
    elif days > 100 and days % 50 == 0:
        return f"🏆 {days} Days! Amazing streak! 🏆"
    
    return None


def format_slack_message(data, days_since, record_streak):
    """Format the Slack message"""
    last_incident_date = get_last_incident_date(data['incidents'])
    
    # Check if this is a new record
    # New record is defined as a streak that is greater or equal to the previous record
    is_new_record = days_since > 0 and days_since == record_streak
    
    # Base message
    if days_since == 0:
        emoji = "🔄"
        status = "Starting fresh"
    elif days_since < 10:
        emoji = "🌱"
        status = "Building momentum"
    elif days_since < 30:
        emoji = "🌿"
        status = "Growing strong"
    elif days_since < 50:
        emoji = "🌳"
        status = "Solid foundation"
    else:
        emoji = "🏆"
        status = "Excellence achieved"
    
    message = {
        "text": f"Days Without Incident: {days_since}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Days Without Incident"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Streak:*\n{days_since} days"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Last Incident:*\n{last_incident_date or 'None recorded'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Record Streak:*\n{record_streak} days"
                    }
                ]
            }
        ]
    }
    
    # Add new record celebration if applicable
    if is_new_record:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🎊 *NEW RECORD!* 🎊\nThis is now the longest streak in company history!"
            }
        })
    
    # Add milestone celebration if applicable
    milestone_msg = get_milestone_message(days_since)
    if milestone_msg:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"🎊 *MILESTONE REACHED!* 🎊\n{milestone_msg}"
            }
        })
    
    # Add motivational footer
    if days_since > 0:
        message["blocks"].append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Total incidents recorded: {len(data['incidents'])} | Every day without an incident is a win! 💪"
                }
            ]
        })
    
    return message


def send_slack_message(webhook_url, message):
    """Send message to Slack via webhook"""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Slack message sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Slack message: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Starting daily incident counter check...")
    
    # Check for required environment variables
    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    
    if not slack_webhook and not test_mode:
        print("❌ Error: SLACK_WEBHOOK_URL environment variable not set")
        print("💡 Tip: For local testing, set TEST_MODE=true")
        sys.exit(1)
    
    # Load incident data
    data = load_incident_data()
    incidents = data.get('incidents', [])
    
    last_incident_date = get_last_incident_date(incidents)
    print(f"📊 Last incident date: {last_incident_date or 'None recorded'}")
    print(f"📈 Total incidents recorded: {len(incidents)}")
    
    # Calculate metrics
    days_since = calculate_days_since_incident(incidents)
    record_streak = calculate_record_streak(incidents)
    
    print(f"📈 Days since last incident: {days_since}")
    print(f"🏆 Record streak: {record_streak}")
    
    # Format message
    message = format_slack_message(data, days_since, record_streak)
    
    if test_mode:
        print("🧪 TEST MODE: Would send this message to Slack:")
        print("=" * 50)
        print(f"Text: {message['text']}")
        for block in message.get('blocks', []):
            if block['type'] == 'header':
                print(f"Header: {block['text']['text']}")
            elif block['type'] == 'section':
                if 'text' in block:
                    print(f"Section: {block['text']['text']}")
                elif 'fields' in block:
                    for field in block['fields']:
                        print(f"Field: {field['text']}")
            elif block['type'] == 'context':
                for element in block['elements']:
                    print(f"Context: {element['text']}")
        print("=" * 50)
        print("✅ Test completed successfully")
    else:
        # Send to Slack
        if send_slack_message(slack_webhook, message):
            print("✅ Daily incident counter update completed successfully")
        else:
            print("❌ Failed to send Slack message")
            sys.exit(1)


if __name__ == "__main__":
    main()
