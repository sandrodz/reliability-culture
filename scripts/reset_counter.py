"""
Reset incident counter script
Use this when an incident occurs to reset the counter and notify the team
"""

import json
import os
import sys
from datetime import date
import requests
import argparse


def load_incident_data():
    """Load the last incident data from JSON file"""
    try:
        with open('last_incident.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "last_incident_date": str(date.today()),
            "description": "",
            "postmortem_link": "",
            "record_streak": 0
        }


def save_incident_data(data):
    """Save incident data back to JSON file"""
    with open('last_incident.json', 'w') as f:
        json.dump(data, f, indent=2)


def format_incident_notification(data, days_lost, description, postmortem_link):
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
                        "text": f"*Incident Date:*\n{data['last_incident_date']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Days Lost:*\n{days_lost} days"
                    }
                ]
            }
        ]
    }
    
    if description:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Description:*\n{description}"
            }
        })
    
    if postmortem_link:
        message["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Postmortem:*\n<{postmortem_link}|View Postmortem>"
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
        response = requests.post(webhook_url, json=message)
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
    parser.add_argument('--notify', action='store_true', help='Send Slack notification')
    
    args = parser.parse_args()
    
    print("🚨 Resetting incident counter...")
    
    # Load current data to get the streak we're losing
    current_data = load_incident_data()
    
    # Calculate days lost (days since last incident)
    from dateutil.parser import parse
    try:
        last_date = parse(current_data['last_incident_date']).date()
        incident_date = parse(args.date).date()
        days_lost = (incident_date - last_date).days
    except:
        days_lost = 0
    
    # Create new incident data
    new_data = {
        "last_incident_date": args.date,
        "description": args.description,
        "postmortem_link": args.postmortem,
        "record_streak": current_data.get('record_streak', 0)
    }
    
    # Save the new data
    save_incident_data(new_data)
    print(f"✅ Counter reset. Last incident date set to: {args.date}")
    
    # Send Slack notification if requested
    if args.notify:
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            message = format_incident_notification(new_data, days_lost, args.description, args.postmortem)
            send_slack_message(slack_webhook, message)
        else:
            print("⚠️  SLACK_WEBHOOK_URL not set, skipping notification")


if __name__ == "__main__":
    main()
