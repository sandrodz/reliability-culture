# 🚀 GitLab CI/CD Incident Counter Setup Guide

This guide will help you configure the GitLab CI/CD pipeline for the daily incident counter that posts to Slack.

## 📋 Prerequisites Checklist

- ✅ GitLab repository with CI/CD enabled
- ✅ [uv](https://docs.astral.sh/uv/) for dependency management
- ⏰ Slack webhook URL for notifications
- 🔑 GitLab CI/CD variables configured

## 🚀 Quick Setup

### 1. Install uv (if not already installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### 2. Install Dependencies
```bash
# Create virtual environment and install dependencies
uv sync
```

### 3. Test Locally
```bash
# Test the counter script (shows what would be sent to Slack)
TEST_MODE=true uv run python -m scripts.check_incident_counter

# Reset counter when incident occurs
uv run python -m scripts.reset_counter \
  --date 2025-06-25 \
  --description "Brief description"
```

## 🔧 Required GitLab CI/CD Variables

Navigate to your GitLab project → Settings → CI/CD → Variables and add:

| Variable Name | Type | Scope | Description |
|--------------|------|-------|-------------|
| `SLACK_WEBHOOK_URL` | Variable (masked) | All environments | Slack webhook URL for incident counter notifications |

## 🔗 Slack App Setup - Create App with Manifest (Recommended)

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Select **"From an app manifest"**
4. Choose your workspace
5. Use this JSON manifest:

```json
{
    "display_information": {
        "name": "reliability-culture",
        "description": "Tracks days without incidents to promote reliability culture",
        "background_color": "#2c3e50"
    },
    "features": {
        "bot_user": {
            "display_name": "Reliability Counter",
            "always_online": true
        }
    },
    "oauth_config": {
        "scopes": {
            "bot": [
                "incoming-webhook",
                "chat:write",
                "chat:write.public"
            ]
        }
    },
    "settings": {
        "org_deploy_enabled": false,
        "socket_mode_enabled": false,
        "is_hosted": false,
        "token_rotation_enabled": false
    }
}
```

6. Click **"Create"** and then **"Install to Workspace"**
7. Go to **"Incoming Webhooks"** in your app settings
8. Enable incoming webhooks
9. Click **"Add New Webhook to Workspace"**
10. Choose the channel (e.g., `#reliability-culture`)
11. Copy the webhook URL
12. Add it to GitLab CI/CD variables as `SLACK_WEBHOOK_URL`

## 📅 Pipeline Schedule Setup

1. Go to your GitLab project
2. Navigate to **CI/CD → Schedules**
3. Click **"New schedule"**
4. Configure with these settings:
   - **Description**: `Daily Incident Counter`
   - **Interval Pattern**: `0 9 * * *` (9 AM daily)
   - **Cron Timezone**: Your preferred timezone
   - **Target Branch**: `main` (or your default branch)
   - **Variables**: (none needed)
5. Click **"Create pipeline schedule"**

## 🧪 Testing the Setup

### Manual Pipeline Test

1. Go to **CI/CD → Pipelines**
2. Click **"Run Pipeline"**
3. Select your branch
4. Click **"Run Pipeline"**
5. Check the pipeline logs for any errors
6. Verify Slack message is posted to your channel

### Expected Slack Message Format

```
🏆 Days Without Incident: 42

📅 Last incident: May 14, 2025
🎯 Current streak: 42 days
🥇 Record streak: 87 days

Keep up the great work, team! 💪
```

## 🔄 Managing Incidents

When an incident occurs, use the reset script to add it to the incident history:

### Add New Incident

```bash
uv run python -m scripts.reset_counter \
  --date 2025-06-25 \
  --description "Database connection timeout" \
  --severity "Sev2" \
  --postmortem "https://company.com/postmortem/123" \
  --notify
```

### Parameters
- `--date`: Incident date (defaults to today)
- `--description`: Brief description of what happened
- `--severity`: Incident severity (Sev1, Sev2, etc.)
- `--postmortem`: Link to postmortem document
- `--notify`: Send Slack notification about the incident

### What Happens
- Incident is added to the history in `last_incident.json`
- Counter automatically resets (0 days since last incident)
- Record streak is preserved and calculated from historical data
- Optional Slack notification about the incident

## 📊 Running the Plotting Script
```
uv run python -m scripts.plot_incidents
```

This will display two plots:
- **Days Without Incident Over Time:** Highlights the best streak group in green.
- **Incidents Per Month:** Highlights the worst month in red.

## 🐛 Troubleshooting

### Pipeline Fails

- Check GitLab CI/CD variables are set correctly
- Verify `SLACK_WEBHOOK_URL` is valid
- Check pipeline logs for specific error messages

### No Slack Messages

- Test webhook URL directly with curl:
  ```bash
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test message"}' \
    YOUR_WEBHOOK_URL
  ```
- Verify the Slack app has permission to post in the channel

### Wrong Counter Value

- Check `last_incident.json` file for correct date format
- Verify timezone settings in GitLab schedule
- Manually trigger pipeline to see current calculation

## 📖 File Structure

```
reliability-culture/
├── .gitlab-ci.yml                    # GitLab CI/CD configuration
├── pyproject.toml                    # Python project dependencies
├── uv.lock                           # uv dependency lock file
├── last_incident.json                # Stores last incident data
├── README.md                         # Project documentation
├── SETUP.md                          # This setup guide
└── scripts/
    ├── __init__.py                   # Python package marker
    ├── check_incident_counter.py     # Main counter script
    ├── incident_utils.py             # Shared utility functions
    ├── plot_incidents.py             # Incident visualization script
    └── reset_counter.py              # Incident reset script
```

## ⚙️ Configuration

The system is highly configurable through the `config.json` file. You can customize:

### 🏆 Milestones
Configure celebration messages for different day counts:
```json
"milestones": {
  "10": "🎉 10 Days! Team shoutout time! 🎉",
  "30": "☕ 30 Days! Virtual coffee vouchers for everyone! ☕"
}
```

### 📊 Status Thresholds  
Define emojis and status messages for different streak ranges:
```json
"status_thresholds": [
  {
    "min_days": 1,
    "max_days": 9,
    "emoji": "🌱", 
    "status": "Building momentum"
  }
]
```

### 💬 Message Templates
Customize all user-facing text including:
- New record announcements
- Milestone celebration messages  
- Footer motivational text
- Field labels

### 🔧 Technical Settings
- Slack timeout duration
- Message templates
- Recurring milestone intervals

To modify the configuration, edit `config.json` and the changes will take effect on the next run.

---

🎉 **Setup Complete!** The daily incident counter will now run automatically and keep your team motivated to maintain high reliability standards.

For questions or improvements, reach out in `#reliability-culture` 😊
