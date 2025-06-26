"""
Plot incident streaks and monthly incident counts from last_incident.json.
"""

from collections import Counter
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scripts.incident_utils import load_incident_data


def parse_incident_dates(incidents):
    """Parse and return a list of incident dates as date objects."""
    return [datetime.strptime(inc['date'], '%Y-%m-%d').date() for inc in incidents]


def plot_streak_over_time(incidents):
    """Plot a bar chart of days without incident over time, highlighting the best streak group in green."""
    if not incidents:
        print("No incidents to plot.")
        return
    dates = parse_incident_dates(incidents)
    start_date = min(dates)
    end_date = datetime.today().date()
    days = (end_date - start_date).days + 1
    x = [start_date + timedelta(days=i) for i in range(days)]
    streak = []
    last_incident = start_date
    incident_set = set(dates)
    for day in x:
        if day in incident_set:
            last_incident = day
            streak.append(0)
        else:
            streak.append((day - last_incident).days)
    # Find the best streak (longest sequence of consecutive days with increasing streak)
    max_streak = max(streak)
    best_indices = [i for i, s in enumerate(streak) if s == max_streak]
    # Find the start and end indices of the best streak group
    best_groups = []
    for idx in best_indices:
        # Go backwards to find the start of the streak
        start_idx = idx
        while start_idx > 0 and streak[start_idx-1] == streak[start_idx] - 1:
            start_idx -= 1
        # Go forwards to find the end of the streak
        end_idx = idx
        while end_idx + 1 < len(streak) and streak[end_idx+1] == streak[end_idx] + 1:
            end_idx += 1
        best_groups.append((start_idx, idx))
    # Merge overlapping groups (should only be one group for max streak)
    if best_groups:
        best_start, best_end = best_groups[0]
    else:
        best_start, best_end = -1, -1
    colors = []
    for i in range(len(streak)):
        if best_start <= i <= best_end and max_streak > 0:
            colors.append('limegreen')
        else:
            colors.append('skyblue')
    plt.figure(figsize=(10, 5))
    plt.bar(x, streak, width=1.0, color=colors, label='Days Without Incident', align='center')
    if best_start != -1:
        plt.bar([x[i] for i in range(best_start, best_end+1)], [streak[i] for i in range(best_start, best_end+1)],
                width=1.0, color='limegreen', label='Best Streak', align='center')
    plt.title('Streak (Days Without Incident) Over Time')
    plt.xlabel('Date')
    plt.ylabel('Days Without Incident')
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()
    plt.show()


def plot_incident_timeline(incidents):
    """Plot a bar chart of the number of incidents per month, highlighting the worst month."""
    if not incidents:
        print("No incidents to plot.")
        return
    # Group incidents by month
    dates = parse_incident_dates(incidents)
    months = [date.strftime('%Y-%m') for date in dates]
    month_counts = Counter(months)
    # Sort months chronologically
    sorted_months = sorted(month_counts.keys())
    counts = [month_counts[m] for m in sorted_months]
    # Find the worst month (max incidents)
    max_count = max(counts)
    colors = ['crimson' if c == max_count else 'salmon' for c in counts]
    plt.figure(figsize=(10, 4))
    plt.bar(sorted_months, counts, color=colors, width=0.6)
    plt.title('Incidents per Month (Worst Month Highlighted)')
    plt.xlabel('Month')
    plt.ylabel('Number of Incidents')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main():
    """Main entry point: load data and plot graphs."""
    data = load_incident_data()
    incidents = data.get('incidents', [])
    plot_streak_over_time(incidents)
    plot_incident_timeline(incidents)


if __name__ == "__main__":
    main()
