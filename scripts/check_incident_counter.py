"""
Daily incident counter script for GitLab CI/CD
Calculates days since last incident and posts to Slack
"""

import os
import sys
from dateutil.parser import parse
import requests
from scripts.incident_utils import load_incident_data, get_last_incident_date, calculate_days_since_incident, load_config


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


def get_milestone_message(days, config):
    """Get special milestone message if applicable"""
    milestones = config['milestones']
    milestone_settings = config['milestone_settings']

    # Check for exact milestone matches
    if str(days) in milestones:
        return milestones[str(days)]

    # Check for recurring milestones (e.g., every 50 days after 100)
    recurring_interval = milestone_settings['recurring_interval']
    if days > 100 and days % recurring_interval == 0:
        return milestone_settings['recurring_template'].format(days=days)

    return None


def get_status_for_days(days, config):
    """Get emoji and status text for the given number of days"""
    status_thresholds = config['status_thresholds']

    for threshold in status_thresholds:
        min_days = threshold['min_days']
        max_days = threshold['max_days']

        if max_days is None:  # No upper bound
            if days >= min_days:
                return threshold['emoji'], threshold['status']
        else:
            if min_days <= days <= max_days:
                return threshold['emoji'], threshold['status']

    # Fallback to last option if no match found
    last_threshold = status_thresholds[-1]
    return last_threshold['emoji'], last_threshold['status']


def format_slack_message(data, days_since, record_streak, config):
    """Format the Slack message"""
    last_incident_date = get_last_incident_date(data['incidents'])
    messages = config['messages']
    slack_config = config['slack']
    field_labels = config['field_labels']

    # Check if this is a new record
    # New record is defined as a streak that is greater or equal to the previous record
    is_new_record = days_since > 0 and days_since == record_streak

    # Get status based on configuration
    emoji, status = get_status_for_days(days_since, config)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": slack_config['header_template'].format(emoji=emoji)
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"{field_labels['current_streak']}\n{days_since} days"
                },
                {
                    "type": "mrkdwn",
                    "text": f"{field_labels['status']}\n{status}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"{field_labels['last_incident']}\n{last_incident_date or messages['no_incident_fallback']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"{field_labels['record_streak']}\n{record_streak} days"
                }
            ]
        }
    ]

    # Add new record celebration if applicable
    if is_new_record:
        new_record_msg = messages['new_record']
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{new_record_msg['title']}\n{new_record_msg['text']}"
            }
        })

    # Add milestone celebration if applicable
    milestone_msg = get_milestone_message(days_since, config)
    if milestone_msg:
        milestone_config = messages['milestone_reached']
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{milestone_config['title']}\n{milestone_msg}"
            }
        })

    # Add motivational footer
    if days_since > 0:
        footer_text = messages['footer_template'].format(incident_count=len(data['incidents']))
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": footer_text
                }
            ]
        })

    message = {
        "text": slack_config['text_template'].format(days_since=days_since),
        "blocks": blocks
    }

    return message


def send_slack_message(webhook_url, message, config):
    """Send message to Slack via webhook"""
    timeout = config['slack']['timeout_seconds']
    try:
        response = requests.post(webhook_url, json=message, timeout=timeout)
        response.raise_for_status()
        print("✅ Slack message sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending Slack message: {e}")
        return False


def main():
    """Main function"""
    print("🚀 Starting daily incident counter check...")

    # Load configuration
    config = load_config()

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
    message = format_slack_message(data, days_since, record_streak, config)

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
        if send_slack_message(slack_webhook, message, config):
            print("✅ Daily incident counter update completed successfully")
        else:
            print("❌ Failed to send Slack message")
            sys.exit(1)


if __name__ == "__main__":
    main()
