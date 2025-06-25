# 🚀 GitLab CI/CD Incident Counter Setup Guide

This guide will help you configure the GitLab CI/CD pipeline for the daily incident counter that posts to Slack.

## 📋 Prerequisites Checklist

- ✅ GitLab repository with CI/CD enabled
- ⏰ Slack webhook URL for notifications
- 🔑 GitLab CI/CD variables configured

## 🔧 Required GitLab CI/CD Variables

Navigate to your GitLab project → Settings → CI/CD → Variables and add:

| Variable Name | Type | Scope | Description |
|--------------|------|-------|-------------|
| `SLACK_WEBHOOK_URL` | Variable (masked) | All environments | Slack webhook URL for incident counter notifications |

## 🔗 Slack Webhook Setup

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create a new app or select existing app
3. Go to **"Incoming Webhooks"**
4. Enable incoming webhooks
5. Click **"Add New Webhook to Workspace"**
6. Choose the channel (e.g., `#reliability-culture`)
7. Copy the webhook URL
8. Add it to GitLab CI/CD variables as `SLACK_WEBHOOK_URL`

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

When an incident occurs, you have two options:

### Option 1: Use the Reset Script (Recommended)

```bash
python scripts/reset_counter.py \
  --date 2025-06-25 \
  --description "Database connection timeout" \
  --postmortem "https://company.com/postmortem/123" \
  --notify
```

### Option 2: Manual Update

Edit the `last_incident.json` file directly:

```json
{
  "date": "2025-06-25",
  "description": "Database connection timeout",
  "postmortem_url": "https://company.com/postmortem/123"
}
```

Then commit and push the changes.

## 🏆 Milestone Celebrations

The system automatically recognizes these milestones:

| Days | Celebration |
|------|-------------|
| 10   | 🎉 Team shoutout |
| 30   | ☕ Virtual coffee vouchers |
| 50   | 🍕 Team lunch |
| 100+ | 🎁 Custom swag or surprise |

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
├── .gitlab-ci.yml           # GitLab CI/CD configuration
├── last_incident.json       # Stores last incident data
├── README.md                # Project documentation
├── SETUP.md                 # This setup guide
└── scripts/
    ├── check_incident_counter.py  # Main counter script
    └── reset_counter.py           # Incident reset script
```

## ✅ Verification Checklist

- [ ] GitLab CI/CD variables configured
- [ ] Slack webhook created and tested
- [ ] Pipeline schedule created (daily at 9 AM)
- [ ] Manual pipeline test successful
- [ ] Slack message received in correct channel
- [ ] Team knows how to report incidents

---

🎉 **Setup Complete!** The daily incident counter will now run automatically and keep your team motivated to maintain high reliability standards.

For questions or improvements, reach out in `#reliability-culture` 😊
