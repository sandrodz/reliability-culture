"""
Reset incident counter script
Use this when an incident occurs to add it to the incident history
"""

import os
import argparse
from datetime import date
import requests
from dateutil.parser import parse
from scripts.incident_utils import load_incident_data, save_incident_data, calculate_days_since_incident


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
            {"type": "divider"},
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
                    }
                ]
            }
        ]
    }

    # Add optional fields if present
    if new_incident.get('severity'):
        message["blocks"][3]["fields"].append({
            "type": "mrkdwn",
            "text": f"*Severity:*\n{new_incident['severity']}"
        })
    if new_incident.get('duration_minutes') is not None:
        message["blocks"][3]["fields"].append({
            "type": "mrkdwn",
            "text": f"*Duration:*\n{new_incident['duration_minutes']} minutes"
        })

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
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "💪 *Remember:* Incidents are learning opportunities. Let's use this to make our systems even stronger!"
            }
        ]
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
    parser.add_argument('--duration', type=int, default=None, help='Duration of the incident in minutes')
    parser.add_argument('--notify', action='store_true', help='Send Slack notification')

    args = parser.parse_args()

    print("🚨 Adding new incident to history...")

    # Load current data to get the streak we're losing
    current_data = load_incident_data()
    incidents = current_data.get('incidents', [])

    # Calculate days lost (days since last incident)
    try:
        reference_date = parse(args.date).date()
    except ValueError:
        print(f"❌ Error: Invalid date format for --date: {args.date}. Use YYYY-MM-DD.")
        return
    days_lost = calculate_days_since_incident(incidents, reference_date)

    # Create new incident record
    new_incident = {
        "date": args.date,
        "description": args.description,
        "postmortem_link": args.postmortem,
        "severity": args.severity,
        "duration_minutes": args.duration
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
