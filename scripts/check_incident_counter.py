"""
Daily incident counter script for GitLab CI/CD
Calculates days since last incident and posts to Slack
"""

import json
import os
import sys
from datetime import datetime, date
from dateutil.parser import parse
import requests


def load_incident_data():
    """Load the last incident data from JSON file"""
    try:
        with open('last_incident.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: last_incident.json not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing last_incident.json: {e}")
        sys.exit(1)


def save_incident_data(data):
    """Save incident data back to JSON file"""
    with open('last_incident.json', 'w') as f:
        json.dump(data, f, indent=2)


def calculate_days_since_incident(last_incident_date_str):
    """Calculate days since the last incident"""
    try:
        last_incident_date = parse(last_incident_date_str).date()
        today = date.today()
        delta = today - last_incident_date
        return delta.days
    except ValueError as e:
        print(f"Error parsing date '{last_incident_date_str}': {e}")
        sys.exit(1)


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


def format_slack_message(data, days_since):
    """Format the Slack message"""
    # Update record if this is a new record
    if days_since > data.get('record_streak', 0):
        data['record_streak'] = days_since
        save_incident_data(data)
        record_note = f" 🏆 *NEW RECORD!* 🏆"
    else:
        record_note = f" (Record: {data.get('record_streak', 0)} days)"
    
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
                        "text": f"*Last Incident:*\n{data['last_incident_date']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Record Streak:*\n{data.get('record_streak', 0)} days"
                    }
                ]
            }
        ]
    }
    
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
                    "text": "Every day without an incident is a win for our customers and our team! 💪"
                }
            ]
        })
    
    return message


def send_slack_message(webhook_url, message):
    """Send message to Slack via webhook"""
    try:
        response = requests.post(webhook_url, json=message)
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
    print(f"📊 Last incident date: {data['last_incident_date']}")
    
    # Calculate days since incident
    days_since = calculate_days_since_incident(data['last_incident_date'])
    print(f"📈 Days since last incident: {days_since}")
    
    # Format message
    message = format_slack_message(data, days_since)
    
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
