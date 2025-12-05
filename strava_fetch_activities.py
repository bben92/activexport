#!/usr/bin/env python3
"""
Strava activities fetching script via API
Fetches all activities (complete history) and exports to multiple formats
"""

import os
import json
import csv
import time
import argparse
from datetime import datetime
import requests
from strava_auth import get_valid_access_token

# Configuration
DEFAULT_OUTPUT_DIR = './output'
API_BASE = 'https://www.strava.com/api/v3'

# Strava API limits
RATE_LIMIT_15MIN = 100
RATE_LIMIT_DAY = 1000


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Fetch all Strava activities via API and export to multiple formats.',
        epilog='''Examples:
  %(prog)s
  %(prog)s -f json csv
  %(prog)s "trail" -f json -o ./my_exports/''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'search',
        nargs='?',
        default=None,
        help='Optional search term to filter activities by name'
    )

    parser.add_argument(
        '-f', '--format',
        action='append',
        choices=['json', 'csv', 'md', 'markdown'],
        dest='formats',
        metavar='FORMAT',
        help='Output format(s): json, csv, md/markdown (default: stdout only). Can be specified multiple times for multiple formats'
    )

    parser.add_argument(
        '-o', '--output',
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory path (default: {DEFAULT_OUTPUT_DIR})'
    )

    return parser.parse_args()


def fetch_all_activities(page_size=200):
    """
    Fetches all athlete's activities
    Strava API: max 200 activities per page
    """
    access_token = get_valid_access_token()
    if not access_token:
        print("[X] Unable to get valid token")
        return None

    headers = {'Authorization': f'Bearer {access_token}'}
    all_activities = []
    page = 1
    request_count = 0

    print("\n" + "="*60)
    print("FETCHING STRAVA ACTIVITIES")
    print("="*60 + "\n")

    while True:
        print(f"[Page {page}] Fetching max {page_size} activities...")

        params = {
            'per_page': page_size,
            'page': page
        }

        try:
            response = requests.get(
                f'{API_BASE}/athlete/activities',
                headers=headers,
                params=params
            )
            response.raise_for_status()
            request_count += 1

            activities = response.json()

            if not activities:
                print(f"[OK] No additional activities (end of pagination)\n")
                break

            all_activities.extend(activities)
            print(f"      -> {len(activities)} activities fetched")
            print(f"      Cumulative total: {len(all_activities)} activities\n")

            # If fewer activities than requested = last page
            if len(activities) < page_size:
                print(f"[OK] Last page reached\n")
                break

            page += 1

            # Pause to respect API limits (caution)
            if request_count % 10 == 0:
                print(f"[PAUSE] 10 requests made, pausing 3s...\n")
                time.sleep(3)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print(f"[X] API limit reached (429 Too Many Requests)")
                print(f"    Waiting 15 minutes...")
                time.sleep(900)
            else:
                print(f"[X] HTTP Error: {e}")
                break
        except Exception as e:
            print(f"[X] Error: {e}")
            break

    print("="*60)
    print(f"TOTAL: {len(all_activities)} activities fetched")
    print(f"API requests used: {request_count}")
    print("="*60 + "\n")

    return all_activities


def export_to_json(activities, filepath):
    """Export activities to JSON format"""
    # Add metadata
    data = {
        'metadata': {
            'export_date': datetime.now().isoformat(),
            'total_activities': len(activities),
            'source': 'Strava API v3'
        },
        'activities': activities
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    file_size_mb = os.path.getsize(filepath) / 1024 / 1024
    print(f"[OK] JSON exported to: {filepath}")
    print(f"     File size: {file_size_mb:.2f} MB")


def export_to_csv(activities, filepath):
    """Export activities to CSV format"""
    if not activities:
        return

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            'date', 'name', 'type', 'distance_km', 'elevation_m',
            'moving_time', 'elapsed_time', 'avg_pace', 'avg_hr', 'max_hr'
        ])

        # Write activity data
        for activity in activities:
            date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            date_str = date.strftime('%Y-%m-%d')
            name = activity.get('name', '')
            sport_type = activity.get('sport_type', '')
            distance_km = activity.get('distance', 0) / 1000
            elevation_m = activity.get('total_elevation_gain', 0)
            moving_time = activity.get('moving_time', 0)
            elapsed_time = activity.get('elapsed_time', 0)

            # Calculate average pace
            avg_pace = ''
            if moving_time > 0 and distance_km > 0:
                pace_sec_km = moving_time / distance_km
                pace_min = int(pace_sec_km // 60)
                pace_sec = int(pace_sec_km % 60)
                avg_pace = f"{pace_min}'{pace_sec:02d}\""

            avg_hr = activity.get('average_heartrate', '')
            max_hr = activity.get('max_heartrate', '')

            writer.writerow([
                date_str, name, sport_type, f"{distance_km:.2f}", int(elevation_m),
                moving_time, elapsed_time, avg_pace, avg_hr, max_hr
            ])

    print(f"[OK] CSV exported to: {filepath}")


def export_to_markdown(activities, filepath):
    """Export activities to Markdown format"""
    if not activities:
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Strava Activities Export\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Activities:** {len(activities)}\n\n")

        # Summary statistics
        f.write("## Summary Statistics\n\n")
        total_distance = sum(a.get('distance', 0) for a in activities) / 1000
        total_elevation = sum(a.get('total_elevation_gain', 0) for a in activities)
        total_time = sum(a.get('moving_time', 0) for a in activities) / 3600

        f.write(f"- **Total Distance:** {total_distance:,.1f} km\n")
        f.write(f"- **Total Elevation:** {total_elevation:,.0f} m\n")
        f.write(f"- **Total Time:** {total_time:,.1f} hours\n\n")

        # Activities by sport type
        f.write("## Activities by Sport Type\n\n")
        sport_types = {}
        for activity in activities:
            sport = activity.get('sport_type', 'Unknown')
            sport_types[sport] = sport_types.get(sport, 0) + 1

        f.write("| Sport Type | Count |\n")
        f.write("|------------|-------|\n")
        for sport, count in sorted(sport_types.items(), key=lambda x: x[1], reverse=True):
            f.write(f"| {sport} | {count} |\n")

        # Recent activities table
        f.write("\n## Recent Activities\n\n")
        f.write("| Date | Name | Type | Distance | Elevation | Time |\n")
        f.write("|------|------|------|----------|-----------|------|\n")

        for activity in activities[:50]:  # Limit to 50 most recent
            date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            date_str = date.strftime('%Y-%m-%d')
            name = activity.get('name', 'N/A')
            sport_type = activity.get('sport_type', 'N/A')
            distance_km = activity.get('distance', 0) / 1000
            elevation_m = activity.get('total_elevation_gain', 0)
            moving_time = activity.get('moving_time', 0)

            # Format time
            hours = moving_time // 3600
            minutes = (moving_time % 3600) // 60
            time_str = f"{hours:02d}h{minutes:02d}'"

            f.write(f"| {date_str} | {name} | {sport_type} | {distance_km:.2f} km | {elevation_m:.0f} m | {time_str} |\n")

    print(f"[OK] Markdown exported to: {filepath}")


def save_activities(activities, formats, output_dir):
    """Save activities to specified formats"""
    if not activities:
        print("[X] No activities to save")
        return

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Normalize formats (treat 'md' and 'markdown' as same)
    normalized_formats = set()
    if formats:
        for fmt in formats:
            if fmt in ['md', 'markdown']:
                normalized_formats.add('markdown')
            else:
                normalized_formats.add(fmt)

    # Export to each format
    if 'json' in normalized_formats:
        filepath = os.path.join(output_dir, f'strava_activities_{timestamp}.json')
        export_to_json(activities, filepath)

    if 'csv' in normalized_formats:
        filepath = os.path.join(output_dir, f'strava_activities_{timestamp}.csv')
        export_to_csv(activities, filepath)

    if 'markdown' in normalized_formats:
        filepath = os.path.join(output_dir, f'strava_activities_{timestamp}.md')
        export_to_markdown(activities, filepath)

    if normalized_formats:
        print()


def analyze_activities(activities):
    """Displays summary of fetched activities"""
    if not activities:
        return

    print("="*60)
    print("ACTIVITY ANALYSIS")
    print("="*60 + "\n")

    # By sport type
    sport_types = {}
    for activity in activities:
        sport = activity.get('sport_type', 'Unknown')
        sport_types[sport] = sport_types.get(sport, 0) + 1

    print("Distribution by sport type:")
    for sport, count in sorted(sport_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {sport:20s}: {count:4d} activities")

    # Covered period
    dates = [datetime.fromisoformat(a['start_date'].replace('Z', '+00:00'))
             for a in activities if 'start_date' in a]

    if dates:
        print(f"\nCovered period:")
        print(f"   First activity: {min(dates).strftime('%d/%m/%Y')}")
        print(f"   Last activity: {max(dates).strftime('%d/%m/%Y')}")

    # Global statistics
    total_distance = sum(a.get('distance', 0) for a in activities) / 1000
    total_elevation = sum(a.get('total_elevation_gain', 0) for a in activities)
    total_time = sum(a.get('moving_time', 0) for a in activities) / 3600

    print(f"\nGlobal statistics:")
    print(f"   Total distance: {total_distance:.1f} km")
    print(f"   Total elevation: {total_elevation:.0f} m")
    print(f"   Total time: {total_time:.1f} hours")

    print("\n" + "="*60 + "\n")


def find_activity_by_name(activities, search_term):
    """Searches for an activity by name"""
    matches = [a for a in activities if search_term.lower() in a.get('name', '').lower()]

    if matches:
        print(f"\n{len(matches)} activity(ies) found containing '{search_term}':\n")
        for activity in matches[:10]:  # Max 10 results
            date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            print(f"   [{date.strftime('%d/%m/%Y')}] {activity['name']}")
            print(f"      {activity.get('distance', 0)/1000:.2f} km - {activity.get('total_elevation_gain', 0):.0f} m elevation")
            print(f"      ID: {activity['id']}")
            print()
        return matches
    else:
        print(f"\n[X] No activity found containing '{search_term}'")
        return []


if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Fetch all activities
    activities = fetch_all_activities()

    if activities:
        # Filter by search term if provided
        if args.search:
            filtered_activities = find_activity_by_name(activities, args.search)
            export_activities = filtered_activities if filtered_activities else activities
        else:
            export_activities = activities

        # Save to specified formats if any
        if args.formats:
            save_activities(export_activities, args.formats, args.output)

        # Always display analysis
        analyze_activities(export_activities)

        # Show recent examples if not searching
        if not args.search:
            print("RECENT ACTIVITY EXAMPLES:\n")
            for activity in export_activities[:5]:
                date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
                print(f"   [{date.strftime('%d/%m/%Y')}] {activity['name']}")
                print(f"      {activity.get('distance', 0)/1000:.2f} km - {activity.get('total_elevation_gain', 0):.0f} m elevation")
                print()
    else:
        print("[X] Failed to fetch activities")
        import sys
        sys.exit(1)
