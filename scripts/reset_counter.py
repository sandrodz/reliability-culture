"""
Reset incident counter script
Use this when an incident occurs to add it to the incident history
"""

import json
import os
import argparse
from datetime import date
from dateutil.parser import parse
import requests


def load_incident_data():
    """Load the incident history from JSON file"""
    try:
        with open('last_incident.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "incidents": []
        }


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
        return 0


def format_incident_notification(incidents, days_lost, new_incident):
    """Format the incident notification message"""
    message = {
        "text": "Incident Reported - Counter Reset",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Incident Reported"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"An incident has been reported. Our streak of {days_lost} days has ended, but we're starting fresh!"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Incident Date:*\n{new_incident['date']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Days Lost:*\n{days_lost} days"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Incidents:*\n{len(incidents)} recorded"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{new_incident.get('severity', 'Not specified')}"
                    }
                ]
            }
        ]
    }
    
    if new_incident.get('description'):
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{new_incident['description']}"
            }
        })
    
    if new_incident.get('postmortem_link'):
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Postmortem:*\n<{new_incident['postmortem_link']}|View Postmortem>"
            }
        })
    
    message["blocks"].append({
        "type": "divider"
    })
    
    message["blocks"].append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "💪 *Remember:* Incidents are learning opportunities. Let's use this to make our systems even stronger!"
        }
    })
    
    return message


def send_slack_message(webhook_url, message):
    """Send message to Slack via webhook"""
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Incident notification sent to Slack")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Slack message: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset the incident counter')
    parser.add_argument('--date', default=str(date.today()), help='Incident date (YYYY-MM-DD)')
    parser.add_argument('--description', default='', help='Brief incident description')
    parser.add_argument('--postmortem', default='', help='Link to postmortem document')
    parser.add_argument('--severity', default='', help='Incident severity (e.g., Sev1, Sev2)')
    parser.add_argument('--notify', action='store_true', help='Send Slack notification')
    
    args = parser.parse_args()
    
    print("🚨 Adding new incident to history...")
    
    # Load current data to get the streak we're losing
    current_data = load_incident_data()
    incidents = current_data.get('incidents', [])
    
    # Calculate days lost (days since last incident)
    days_lost = calculate_days_since_incident(incidents)
    
    # Create new incident record
    new_incident = {
        "date": args.date,
        "description": args.description,
        "postmortem_link": args.postmortem,
        "severity": args.severity
    }
    
    # Add incident to history
    incidents.append(new_incident)
    
    # Update data
    updated_data = {
        "incidents": incidents
    }
    
    # Save the new data
    save_incident_data(updated_data)
    print(f"✅ Incident added to history. Date: {args.date}")
    print(f"📊 Total incidents now: {len(incidents)}")
    print(f"📉 Streak lost: {days_lost} days")
    
    # Send Slack notification if requested
    if args.notify:
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            message = format_incident_notification(incidents, days_lost, new_incident)
            send_slack_message(slack_webhook, message)
        else:
            print("⚠️  SLACK_WEBHOOK_URL not set, skipping notification")


if __name__ == "__main__":
    main()
