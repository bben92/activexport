#!/usr/bin/env python3
"""
Fetches complete details of a Strava activity via API
Exports activity details to multiple formats
"""

import os
import json
import argparse
from datetime import datetime
import requests
from strava_auth import get_valid_access_token

# Configuration
DEFAULT_OUTPUT_DIR = './output'
API_BASE = 'https://www.strava.com/api/v3'


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Fetch detailed information for a specific Strava activity.',
        epilog='''Examples:
  %(prog)s 6018412458
  %(prog)s 6018412458 -f json md
  %(prog)s 6018412458 -f json -o ./my_exports/''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'activity_id',
        help='Strava activity ID'
    )

    parser.add_argument(
        '-f', '--format',
        action='append',
        choices=['json', 'md', 'markdown'],
        dest='formats',
        metavar='FORMAT',
        help='Output format(s): json, md/markdown (default: stdout only). Can be specified multiple times for multiple formats'
    )

    parser.add_argument(
        '-o', '--output',
        default=DEFAULT_OUTPUT_DIR,
        help=f'Output directory path (default: {DEFAULT_OUTPUT_DIR})'
    )

    return parser.parse_args()


def get_activity_details(activity_id):
    """Fetches complete details of an activity"""
    access_token = get_valid_access_token()
    if not access_token:
        print("[X] Unable to get valid token")
        return None

    headers = {'Authorization': f'Bearer {access_token}'}

    try:
        response = requests.get(
            f'{API_BASE}/activities/{activity_id}',
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"[X] Error: {e}")
        return None


def display_activity(activity):
    """Displays activity details"""
    if not activity:
        return

    print("\n" + "="*60)
    print("ACTIVITY DETAILS")
    print("="*60 + "\n")

    # Basic information
    date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
    print(f"Name: {activity.get('name', 'N/A')}")
    print(f"Date: {date.strftime('%d/%m/%Y %H:%M')}")
    print(f"Type: {activity.get('sport_type', 'N/A')}")
    print(f"ID: {activity.get('id', 'N/A')}")

    # Metrics
    print(f"\nMETRICS:")
    print(f"   Distance: {activity.get('distance', 0)/1000:.2f} km")
    print(f"   Elevation gain: {activity.get('total_elevation_gain', 0):.0f} m D+")
    print(f"   Time: {activity.get('moving_time', 0)//3600:02d}h{(activity.get('moving_time', 0)%3600)//60:02d}'{(activity.get('moving_time', 0)%60):02d}\"")
    print(f"   Total time: {activity.get('elapsed_time', 0)//3600:02d}h{(activity.get('elapsed_time', 0)%3600)//60:02d}'{(activity.get('elapsed_time', 0)%60):02d}\"")

    # Pace
    moving_time = activity.get('moving_time', 0)
    distance = activity.get('distance', 0)
    if moving_time > 0 and distance > 0:
        pace_sec_km = (moving_time / (distance / 1000))
        pace_min = int(pace_sec_km // 60)
        pace_sec = int(pace_sec_km % 60)
        print(f"   Average pace: {pace_min}'{pace_sec:02d}\"/km")

    # HR
    if activity.get('has_heartrate'):
        print(f"\nHEART RATE:")
        print(f"   Average HR: {activity.get('average_heartrate', 'N/A')} bpm")
        print(f"   Max HR: {activity.get('max_heartrate', 'N/A')} bpm")

    # Altitude
    if activity.get('elev_high') or activity.get('elev_low'):
        print(f"\nALTITUDE:")
        print(f"   Min: {activity.get('elev_low', 'N/A')} m")
        print(f"   Max: {activity.get('elev_high', 'N/A')} m")

    # Cadence
    if activity.get('average_cadence'):
        print(f"\nCADENCE:")
        print(f"   Average: {activity.get('average_cadence', 'N/A')} spm")

    # Equipment
    if activity.get('gear'):
        print(f"\nEQUIPMENT:")
        print(f"   {activity['gear'].get('name', 'N/A')} ({activity['gear'].get('distance', 0)/1000:.1f} km)")

    # Description
    if activity.get('description'):
        print(f"\nDESCRIPTION:")
        try:
            print(f"   {activity['description']}")
        except UnicodeEncodeError:
            print(f"   [Contains special characters]")

    print("\n" + "="*60 + "\n")


def export_to_json(activity, filepath):
    """Export activity to JSON format"""
    if not activity:
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(activity, f, indent=2, ensure_ascii=False)

    file_size_kb = os.path.getsize(filepath) / 1024
    print(f"[OK] JSON exported to: {filepath}")
    print(f"     File size: {file_size_kb:.2f} KB")


def export_to_markdown(activity, filepath):
    """Export activity to Markdown format"""
    if not activity:
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        # Header
        name = activity.get('name', 'N/A')
        f.write(f"# Activity Details: {name}\n\n")

        # Basic info
        activity_id = activity.get('id', 'N/A')
        date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
        date_str = date.strftime('%Y-%m-%d %H:%M')
        sport_type = activity.get('sport_type', 'N/A')

        f.write(f"**ID:** {activity_id}\n")
        f.write(f"**Date:** {date_str}\n")
        f.write(f"**Type:** {sport_type}\n\n")

        # Metrics
        f.write("## Metrics\n\n")
        distance_km = activity.get('distance', 0) / 1000
        elevation_m = activity.get('total_elevation_gain', 0)
        moving_time = activity.get('moving_time', 0)
        elapsed_time = activity.get('elapsed_time', 0)

        # Format times
        moving_hours = moving_time // 3600
        moving_mins = (moving_time % 3600) // 60
        moving_secs = moving_time % 60
        moving_str = f"{moving_hours:02d}h{moving_mins:02d}'{moving_secs:02d}\""

        elapsed_hours = elapsed_time // 3600
        elapsed_mins = (elapsed_time % 3600) // 60
        elapsed_secs = elapsed_time % 60
        elapsed_str = f"{elapsed_hours:02d}h{elapsed_mins:02d}'{elapsed_secs:02d}\""

        f.write(f"- **Distance:** {distance_km:.2f} km\n")
        f.write(f"- **Elevation gain:** {elevation_m:.0f} m D+\n")
        f.write(f"- **Time:** {moving_str}\n")
        f.write(f"- **Total time:** {elapsed_str}\n")

        # Pace
        if moving_time > 0 and distance_km > 0:
            pace_sec_km = moving_time / distance_km
            pace_min = int(pace_sec_km // 60)
            pace_sec = int(pace_sec_km % 60)
            f.write(f"- **Average pace:** {pace_min}'{pace_sec:02d}\"/km\n")

        # Heart rate
        if activity.get('has_heartrate'):
            f.write("\n## Heart Rate\n\n")
            avg_hr = activity.get('average_heartrate', 'N/A')
            max_hr = activity.get('max_heartrate', 'N/A')
            f.write(f"- **Average HR:** {avg_hr} bpm\n")
            f.write(f"- **Max HR:** {max_hr} bpm\n")

        # Altitude
        if activity.get('elev_high') or activity.get('elev_low'):
            f.write("\n## Altitude\n\n")
            min_alt = activity.get('elev_low', 'N/A')
            max_alt = activity.get('elev_high', 'N/A')
            f.write(f"- **Min:** {min_alt} m\n")
            f.write(f"- **Max:** {max_alt} m\n")

        # Cadence
        if activity.get('average_cadence'):
            f.write("\n## Cadence\n\n")
            avg_cadence = activity.get('average_cadence', 'N/A')
            f.write(f"- **Average:** {avg_cadence} spm\n")

        # Equipment
        if activity.get('gear'):
            f.write("\n## Equipment\n\n")
            gear_name = activity['gear'].get('name', 'N/A')
            gear_distance_km = activity['gear'].get('distance', 0) / 1000
            f.write(f"- {gear_name} ({gear_distance_km:.1f} km)\n")

        # Description
        if activity.get('description'):
            f.write("\n## Description\n\n")
            try:
                f.write(f"{activity['description']}\n")
            except UnicodeEncodeError:
                f.write("[Contains special characters]\n")

    print(f"[OK] Markdown exported to: {filepath}")


def save_activity(activity, formats, output_dir):
    """Save activity to specified formats"""
    if not activity:
        print("[X] No activity to save")
        return

    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)

    activity_id = activity.get('id', 'unknown')

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
        filepath = os.path.join(output_dir, f'activity_{activity_id}.json')
        export_to_json(activity, filepath)

    if 'markdown' in normalized_formats:
        filepath = os.path.join(output_dir, f'activity_{activity_id}.md')
        export_to_markdown(activity, filepath)

    if normalized_formats:
        print()


if __name__ == '__main__':
    # Parse arguments
    args = parse_arguments()

    # Fetch activity details
    activity = get_activity_details(args.activity_id)

    if activity:
        # Always display to stdout
        display_activity(activity)

        # Save to specified formats if any
        if args.formats:
            save_activity(activity, args.formats, args.output)
    else:
        print("[X] Failed to fetch activity details")
        import sys
        sys.exit(1)
