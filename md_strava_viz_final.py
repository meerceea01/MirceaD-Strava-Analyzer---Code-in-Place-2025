import csv
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

########################################################### Mircea Danciulescu Strava Analysis ######################################################################   
########################################################## Final Project for Code in Place 2025 #####################################################################   


############################# Function that reads the csv data ##############################   
def read_csv_file(filename):
    """
    Read the Strava CSV file (I used the activities.csv file) and return a list of activities.
    Each activity is a dictionary with all the data from one row.
    * Note that I removed some fields that I didn't need for the analysis.
    * The CSV file should have a header row with the following columns:
      - Activity Name
      - Activity Type
      - Activity Description
      - Activity Gear
      - Distance_KM
      - Moving Time
      - Elapsed Time
      - Elevation Low
      - Elevation High
      - Max Heart Rate
      - Max Speed
      - Max Grade
      - Average Grade
      - Average Speed (in m/s)
      - Commute (TRUE/FALSE)
      - Activity Date (in format: 01 Jan 2024, 12:00:00)
    """
    
    # Instantiate an empty list to hold all activities
    activities = []
    
    try:
        # Open the CSV file
        with open(filename, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            # Go through each row in the CSV
            for row in csv_reader:
                activity = process_single_row(row)
                if activity:  # Only add if we successfully processed it
                    activities.append(activity)
                    
    except FileNotFoundError:
        print(f"ERROR: Could not find file '{filename}'")
        print("Make sure the file is in the same folder as this Python script.")
        return []
    
    return activities



############################# Function that processes a single row from the csv data ##############   
def process_single_row(row):
    """
    Takes one row from the CSV and converts it into clean data.
    Returns None if there's a problem with the row.
    """
    try:
        # Create a new activity dictionary
        activity = {}
        
        # Copy text fields as-is
        activity['name'] = row.get('Activity Name', '')
        activity['type'] = row.get('Activity Type', '')
        activity['description'] = row.get('Activity Description', '')
        activity['gear'] = row.get('Activity Gear', '')
        
        # Convert number fields (handle empty cells)
        activity['distance_km'] = convert_to_number(row.get('Distance_KM', ''))
        activity['time_seconds'] = convert_to_number(row.get('Moving Time', ''))
        activity['elapsed_time'] = convert_to_number(row.get('Elapsed Time', ''))
        activity['elevation_low'] = convert_to_number(row.get('Elevation Low', ''))
        activity['elevation_high'] = convert_to_number(row.get('Elevation High', ''))
        activity['max_heart_rate'] = convert_to_number(row.get('Max Heart Rate', ''))
        activity['max_speed'] = convert_to_number(row.get('Max Speed', ''))
        activity['max_grade'] = convert_to_number(row.get('Max Grade', ''))
        activity['avg_grade'] = convert_to_number(row.get('Average Grade', ''))
        

        # Your Average Speed is already in m/s, convert to km/h for readability
        speed_ms = convert_to_number(row.get('Average Speed', ''))
        if speed_ms > 0:
            activity['avg_speed_kmh'] = speed_ms * 3.6  # Convert m/s to km/h
        else:
            activity['avg_speed_kmh'] = 0
        
        # Max speed conversion (also from m/s to km/h)
        max_speed_ms = activity['max_speed']
        if max_speed_ms > 0:
            activity['max_speed_kmh'] = max_speed_ms * 3.6
        else:
            activity['max_speed_kmh'] = 0
        
        # Check if this is a commute activity
        activity['is_commute'] = row.get('Commute', '').upper() == 'TRUE'
        
        # Calculate pace (min/km) for running activities (I like min/km better than m/s 🙂)
        if activity['distance_km'] > 0 and activity['time_seconds'] > 0:
            pace_seconds_per_km = activity['time_seconds'] / activity['distance_km']
            activity['pace_min_per_km'] = pace_seconds_per_km / 60
        else:
            activity['pace_min_per_km'] = 0
        
        # Handle the date (remove quotes and convert to datetime)
        date_text = row.get('Activity Date', '').strip().strip('"')
        if date_text:
            activity['date'] = datetime.strptime(date_text, '%d %b %Y, %H:%M:%S')
            activity['day_of_week'] = activity['date'].strftime('%A')
            activity['hour'] = activity['date'].hour
        else:
            print(f"Skipping activity with no date: {activity['name']}")
            return None
        
        # Only keep activities that have actual distance
        if activity['distance_km'] <= 0:
            print(f"Skipping activity with no distance: {activity['name']}")
            return None
        
        return activity
        
    except Exception as error:
        print(f"Problem processing activity '{row.get('Activity Name', 'Unknown')}': {error}")
        return None



############################# Function that converts strings to numeric  ##############   
def convert_to_number(text_value):
    """
    Convert text to a number. If it's empty or invalid, return 0.
    """
    if not text_value or str(text_value).strip() == '':
        return 0
    
    try:
        return float(str(text_value).strip())
    except:
        return 0


############################# Function that separates running and cycling activities ##############
def separate_running_and_cycling(activities):
    """
    Split the activities into two lists: running and cycling. There's also a third list for other activities.
    """
    running_activities = []
    cycling_activities = []
    other_activities = []
    
    for activity in activities:
        activity_type = activity['type'].lower()
        
        if 'run' in activity_type:
            running_activities.append(activity)
        elif any(word in activity_type for word in ['ride', 'cycling', 'bike']):
            cycling_activities.append(activity)
        else:
            other_activities.append(activity)
    
    return running_activities, cycling_activities, other_activities

############################# Function that calculates advanced statistics for activities ##############
def calculate_advanced_stats(activities, activity_type_name):
    """
    Calculate detailed statistics for a list of activities.
    """
    if not activities:
        print(f"\nNo {activity_type_name} activities found!")
        return {}
    
    # Count activities
    total_count = len(activities)
    
    # Calculate totals
    total_distance = sum(activity['distance_km'] for activity in activities)
    total_time_hours = sum(activity['time_seconds'] for activity in activities) / 3600
    total_elapsed_hours = sum(activity['elapsed_time'] for activity in activities) / 3600


    # Count commute activities
    commute_count = sum(1 for activity in activities if activity.get('is_commute', False))
    
    # Calculate averages and statistics
    distances = [a['distance_km'] for a in activities if a['distance_km'] > 0]
    speeds = [a['avg_speed_kmh'] for a in activities if a['avg_speed_kmh'] > 0]
    max_speeds = [a['max_speed_kmh'] for a in activities if a['max_speed_kmh'] > 0]
    heart_rates = [a['max_heart_rate'] for a in activities if a['max_heart_rate'] > 0]
    paces = [a['pace_min_per_km'] for a in activities if a['pace_min_per_km'] > 0]
    max_grades = [a['max_grade'] for a in activities if a['max_grade'] > 0]
    avg_grades = [a['avg_grade'] for a in activities if a['avg_grade'] != 0]  # 0 is valid for grade
    
    stats = {
        'count': total_count,
        'total_distance': total_distance,
        'total_time_hours': total_time_hours,
        'total_elapsed_hours': total_elapsed_hours,
        'commute_count': commute_count,
        'avg_distance': statistics.mean(distances) if distances else 0,
        'median_distance': statistics.median(distances) if distances else 0,
        'max_distance': max(distances) if distances else 0,
        'min_distance': min(distances) if distances else 0,
        'avg_speed': statistics.mean(speeds) if speeds else 0,
        'max_speed': max(max_speeds) if max_speeds else 0,
        'avg_max_hr': statistics.mean(heart_rates) if heart_rates else 0,
        'avg_pace': statistics.mean(paces) if paces else 0,
        'best_pace': min(paces) if paces else 0,
        'avg_max_grade': statistics.mean(max_grades) if max_grades else 0,
        'steepest_grade': max(max_grades) if max_grades else 0,
        'avg_grade': statistics.mean(avg_grades) if avg_grades else 0
    }
    
    # Print the results
    print(f"\n=== {activity_type_name.upper()} DETAILED STATISTICS ===")
    print(f"Total activities: {total_count}")
    if commute_count > 0:
        print(f"  └─ Commute activities: {commute_count} ({commute_count/total_count*100:.1f}%)")
    print(f"Total distance: {total_distance:.1f} km")
    print(f"Total moving time: {total_time_hours:.1f} hours ({total_time_hours/24:.1f} days)")
    print(f"Total elapsed time: {total_elapsed_hours:.1f} hours ({total_elapsed_hours/24:.1f} days)")


    
    print(f"\nDistance Statistics:")
    print(f"  Average: {stats['avg_distance']:.1f} km")
    print(f"  Median: {stats['median_distance']:.1f} km")
    print(f"  Longest: {stats['max_distance']:.1f} km")
    print(f"  Shortest: {stats['min_distance']:.1f} km")
    
    if speeds:
        print(f"\nSpeed Statistics:")
        print(f"  Average speed: {stats['avg_speed']:.1f} km/h")
        print(f"  Top speed: {stats['max_speed']:.1f} km/h")
    
    if paces and activity_type_name.lower() == 'running':
        print(f"\nPace Statistics:")
        print(f"  Average pace: {format_pace(stats['avg_pace'])}")
        print(f"  Best pace: {format_pace(stats['best_pace'])}")
    
    if heart_rates:
        print(f"\nHeart Rate Statistics:")
        print(f"  Average max HR: {stats['avg_max_hr']:.0f} bpm")
    
    if max_grades:
        print(f"\nGradient Statistics:")
        print(f"  Average max gradient: {stats['avg_max_grade']:.1f}%")
        print(f"  Steepest gradient: {stats['steepest_grade']:.1f}%")
        if avg_grades:
            print(f"  Overall average gradient: {stats['avg_grade']:.1f}%")
    
    return stats

############################# Function that formats pace from decimal minutes to MM:SS format ##############
def format_pace(pace_min_per_km):
    """Convert pace from decimal minutes to MM:SS format"""
    if pace_min_per_km <= 0:
        return "N/A"
    
    minutes = int(pace_min_per_km)
    seconds = int((pace_min_per_km - minutes) * 60)
    return f"{minutes}:{seconds:02d} min/km"

############################# Functions for analyzing weekly patterns, time of day, personal records, gear usage, monthly patterns, and comparisons ##############
def analyze_weekly_patterns(activities, activity_type):
    """Analyze which days of the week you're most active"""
    print(f"\n=== {activity_type.upper()} WEEKLY PATTERNS ===")
    
    day_counts = defaultdict(int)
    day_distances = defaultdict(float)
    
    for activity in activities:
        day = activity['day_of_week']
        day_counts[day] += 1
        day_distances[day] += activity['distance_km']
    
    # Order days properly
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    print(f"{'Day':<12} {'Activities':<12} {'Total Distance':<15} {'Avg Distance'}")
    print("-" * 55)
    
    for day in days_order:
        count = day_counts[day]
        total_dist = day_distances[day]
        avg_dist = total_dist / count if count > 0 else 0
        
        print(f"{day:<12} {count:<12} {total_dist:<15.1f} {avg_dist:.1f} km")
    
    # Find favorite day
    favorite_day = max(day_counts, key=day_counts.get) if day_counts else "None"
    print(f"\nYour favorite {activity_type} day: {favorite_day} ({day_counts[favorite_day]} activities)")


  
def analyze_time_of_day_patterns(activities, activity_type):
    """Analyze what time of day you prefer to exercise"""
    print(f"\n=== {activity_type.upper()} TIME OF DAY PATTERNS ===")
    
    hour_counts = defaultdict(int)
    
    for activity in activities:
        hour = activity['hour']
        hour_counts[hour] += 1
    
    # Group into time periods
    periods = {
        'Early Morning (5-8 AM)': list(range(5, 9)),
        'Morning (9-11 AM)': list(range(9, 12)),
        'Afternoon (12-4 PM)': list(range(12, 17)),
        'Evening (5-8 PM)': list(range(17, 21)),
        'Night (9 PM - 4 AM)': list(range(21, 24)) + list(range(0, 5))
    }
    
    # Count activities in each period
    period_counts = {}
    for period_name, hours in periods.items():
        period_counts[period_name] = sum(hour_counts[hour] for hour in hours)
    
    print("Time Period Preferences:")
    for period, count in sorted(period_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            percentage = (count / len(activities)) * 100
            print(f"  {period}: {count} activities ({percentage:.1f}%)")


def analyze_personal_records(activities, activity_type):
    """Find personal records and achievements"""
    if not activities:
        return
    
    print(f"\n=== {activity_type.upper()} PERSONAL RECORDS ===")
    
    # Sort by different metrics
    longest = max(activities, key=lambda x: x['distance_km'])
    fastest_speed = max(activities, key=lambda x: x['avg_speed_kmh']) if any(a['avg_speed_kmh'] > 0 for a in activities) else None
    steepest_climb = max(activities, key=lambda x: x['max_grade']) if any(a['max_grade'] > 0 for a in activities) else None
    
    print(f"🏆 Longest {activity_type.lower()}: {longest['distance_km']:.1f} km")
    print(f"   Date: {longest['date'].strftime('%B %d, %Y')}")
    print(f"   Name: {longest['name']}")
    
    if fastest_speed and fastest_speed['avg_speed_kmh'] > 0:
        print(f"\n🚀 Fastest average speed: {fastest_speed['avg_speed_kmh']:.1f} km/h")
        print(f"   Date: {fastest_speed['date'].strftime('%B %d, %Y')}")
        print(f"   Distance: {fastest_speed['distance_km']:.1f} km")
        print(f"   Name: {fastest_speed['name']}")
    
    if steepest_climb and steepest_climb['max_grade'] > 0:
        print(f"\n🏔️ Steepest gradient: {steepest_climb['max_grade']:.1f}%")
        print(f"   Date: {steepest_climb['date'].strftime('%B %d, %Y')}")
        print(f"   Distance: {steepest_climb['distance_km']:.1f} km")
        print(f"   Name: {steepest_climb['name']}")
    
    # Best pace for running
    if activity_type.lower() == 'running':
        best_pace_activity = min(activities, key=lambda x: x['pace_min_per_km']) if any(a['pace_min_per_km'] > 0 for a in activities) else None
        if best_pace_activity and best_pace_activity['pace_min_per_km'] > 0:
            print(f"\n🏃 Best pace: {format_pace(best_pace_activity['pace_min_per_km'])}")
            print(f"   Date: {best_pace_activity['date'].strftime('%B %d, %Y')}")
            print(f"   Distance: {best_pace_activity['distance_km']:.1f} km")
            print(f"   Name: {best_pace_activity['name']}")


def analyze_gear_usage(activities, activity_type):
    """Analyze which gear/equipment is used most"""
    if not any(a['gear'] for a in activities):
        return
    
    print(f"\n=== {activity_type.upper()} GEAR ANALYSIS ===")
    
    gear_counts = defaultdict(int)
    gear_distances = defaultdict(float)
    
    for activity in activities:
        gear = activity['gear'] if activity['gear'] else 'No gear specified'
        gear_counts[gear] += 1
        gear_distances[gear] += activity['distance_km']
    
    print("Gear Usage:")
    for gear in sorted(gear_counts.keys(), key=lambda x: gear_counts[x], reverse=True):
        count = gear_counts[gear]
        distance = gear_distances[gear]
        avg_distance = distance / count
        print("-" * 60)
        print(f"  {gear}:")
        print(f"    Activities: {count}")
        print(f"    Total distance: {distance:.1f} km")
        print(f"    Average per activity: {avg_distance:.1f} km")



def create_text_bar_chart(data_dict, title, max_bar_length=40):
    """
    Create a simple text-based bar chart.
    data_dict should be like {'2024-01': 5, '2024-02': 8, ...}
    """
    print(f"\n{title}")
    print("=" * len(title))
    
    if not data_dict:
        print("No data to display")
        return
    
    # Find the maximum value to scale the bars
    max_value = max(data_dict.values())
    
    # Create bars for each month
    for month, count in data_dict.items():
        # Calculate bar length (proportional to count)
        if max_value > 0:
            bar_length = int((count / max_value) * max_bar_length)
        else:
            bar_length = 0
        
        # Create the bar using █ characters
        bar = "█" * bar_length
        
        # Format the month name nicely
        try:
            month_date = datetime.strptime(month, '%Y-%m')
            month_name = month_date.strftime('%b %Y')  # e.g., "Jan 2024"
        except:
            month_name = month
        
        # Print the bar chart line
        print(f"{month_name:<12} {bar} {count}")



def analyze_monthly_patterns(running, cycling, other):
    """
    Show which months you prefer running vs cycling, with visualizations.
    """
    print("\n" + "="*60)
    print("MONTHLY ACTIVITY PATTERNS")
    print("="*60)
    
    # Count activities by month for all activity types
    monthly_running = defaultdict(int)
    monthly_cycling = defaultdict(int)
    monthly_other = defaultdict(int)
    
    # Populate monthly counts
    for activity in running:
        month_key = activity['date'].strftime('%Y-%m')
        monthly_running[month_key] += 1
    
    for activity in cycling:
        month_key = activity['date'].strftime('%Y-%m')
        monthly_cycling[month_key] += 1
    
    for activity in other:
        month_key = activity['date'].strftime('%Y-%m')
        monthly_other[month_key] += 1
    
    # Get all months that have any activities
    all_months = set()
    all_months.update(monthly_running.keys())
    all_months.update(monthly_cycling.keys())
    all_months.update(monthly_other.keys())
    all_months = sorted(all_months)
    
    # Show the last 12 months
    recent_months = all_months[-12:] if len(all_months) >= 12 else all_months
    
    # Create data dictionaries for recent months only
    recent_running = {month: monthly_running[month] for month in recent_months if monthly_running[month] > 0}
    recent_cycling = {month: monthly_cycling[month] for month in recent_months if monthly_cycling[month] > 0}
    recent_other = {month: monthly_other[month] for month in recent_months if monthly_other[month] > 0}
    
    # Show text-based bar charts
    if recent_running:
        create_text_bar_chart(recent_running, "RUNNING ACTIVITIES BY MONTH")
    
    if recent_cycling:
        create_text_bar_chart(recent_cycling, "CYCLING ACTIVITIES BY MONTH")
    
    if recent_other:
        create_text_bar_chart(recent_other, "OTHER ACTIVITIES BY MONTH")


def compare_running_vs_cycling(running_act, cycling_act):
    """
    Compare running and cycling activities side by side.
    """
    print("\n" + "="*60)
    print("RUNNING vs CYCLING COMPARISON")
    print("="*60)
    
    if not running_act:
        print("No running activities found to compare!")
        return
    if not cycling_act:
        print("No cycling activities found to compare!")
        return
    
    # Activity counts
    total_activities = len(running_act) + len(cycling_act)
    running_percentage = (len(running_act) / total_activities) * 100
    
    print(f"\nActivity Frequency:")
    print(f"  Running: {len(running_act)} activities ({running_percentage:.1f}%)")
    print(f"  Cycling: {len(cycling_act)} activities ({100-running_percentage:.1f}%)")
    
    # Distance comparison
    run_total_km = sum(a['distance_km'] for a in running_act)
    cycle_total_km = sum(a['distance_km'] for a in cycling_act)
    total_distance = run_total_km + cycle_total_km
    
    print(f"\nTotal Distance:")
    print(f"  Running: {run_total_km:.1f} km ({run_total_km/total_distance*100:.1f}%)")
    print(f"  Cycling: {cycle_total_km:.1f} km ({cycle_total_km/total_distance*100:.1f}%)")
    
    # Average distance per activity
    run_avg_distance = run_total_km / len(running_act)
    cycle_avg_distance = cycle_total_km / len(cycling_act)
    
    print(f"\nAverage Distance per Activity:")
    print(f"  Running: {run_avg_distance:.1f} km")
    print(f"  Cycling: {cycle_avg_distance:.1f} km")

    if run_avg_distance > cycle_avg_distance:
        print(f"  → Running activities are {run_avg_distance/cycle_avg_distance:.1f}x longer on average")
    elif cycle_avg_distance > run_avg_distance:
        print(f"  → Cycling activities are {cycle_avg_distance/run_avg_distance:.1f}x longer on average")
    else:
        print("  → Running and Cycling activities have the same average distance")

    
    # Time comparison
    run_total_hours = sum(a['time_seconds'] for a in running_act) / 3600
    cycle_total_hours = sum(a['time_seconds'] for a in cycling_act) / 3600
    
    print(f"\nTotal Time Spent:")
    print(f"  Running: {run_total_hours:.1f} hours")
    print(f"  Cycling: {cycle_total_hours:.1f} hours")

############################# End of Functions for analyzing weekly patterns, time of day, personal records, gear usage, monthly patterns, and comparisons ##############



################################################################################## MAIN FUNCTION ######################################################################   
################################################################################## MAIN FUNCTION ######################################################################   

def main():
    """
    Main function that runs the entire analysis.
    """
    print("🏃🏻‍♂️🚴🏻‍♂️ MirceaD Enhanced Strava Activity Analysis Tool 🏃🏻‍♂️🚴🏻‍♂️")
    print("=" * 60)
    
    # Input Strava activities filename [hardcoded for simplicity]
    filename = 'md_strava_acts.csv'
    
    # Load all activities from CSV
    print(f"\nReading activities from {filename}...")
    all_activities = read_csv_file(filename)
    
    if not all_activities:
        print("No activities were loaded. Please check your file and try again.")
        return
    
    print(f"Successfully loaded {len(all_activities)} activities!")
    
    # Separate activities by type
    running_activities, cycling_activities, other_activities = separate_running_and_cycling(all_activities)
    
    print(f"\nActivity breakdown:")
    print(f"  🏃🏻‍♂️ Running: {len(running_activities)} activities")
    print(f"  🚴🏻‍♂️ Cycling: {len(cycling_activities)} activities")
    print(f"  Other: {len(other_activities)} activities")
    
    choice = ""  # Initialize choice variable

    while choice not in ['0', '8']:

        # Show what analysis to run
        print(f"\n{'='*60}")
        print("ANALYSIS MENU")
        print(f"{'='*60}")
        print("1. Detailed Statistics")
        print("2. Weekly Patterns")
        print("3. Time of Day Analysis")
        print("4. Personal Records")
        print("5. Gear Analysis")
        print("6. Monthly Patterns")
        print("7. Running vs Cycling Comparison")
        print("8. Run All Analyses")
        print("0. Cancel and Exit")    
        
        choice = input("\nEnter your choice (1-8) or press Enter for all (0 to Exit): ").strip()
        
        if choice in ['1', '8', '']:
            # Basic stats
            if running_activities:
                calculate_advanced_stats(running_activities, "Running")
            if cycling_activities:
                calculate_advanced_stats(cycling_activities, "Cycling")
            if other_activities:
                calculate_advanced_stats(other_activities, "Other Activities")
        

        if choice in ['2', '8', '']:
            # Weekly patterns
            if running_activities:
                analyze_weekly_patterns(running_activities, "Running")
            if cycling_activities:
                analyze_weekly_patterns(cycling_activities, "Cycling")
        
        if choice in ['3', '8', '']:
            # Time of day patterns
            if running_activities:
                analyze_time_of_day_patterns(running_activities, "Running")
            if cycling_activities:
                analyze_time_of_day_patterns(cycling_activities, "Cycling")
        
        if choice in ['4', '8', '']:
            # Personal records
            if running_activities:
                analyze_personal_records(running_activities, "Running")
            if cycling_activities:
                analyze_personal_records(cycling_activities, "Cycling")
        
        if choice in ['5', '8', '']:
            # Gear analysis
            if running_activities:
                analyze_gear_usage(running_activities, "Running")
            if cycling_activities:
                analyze_gear_usage(cycling_activities, "Cycling")
        
        if choice in ['6', '8', '']:
            # Monthly patterns
            analyze_monthly_patterns(running_activities, cycling_activities, other_activities)
        
        if choice in ['7', '8', '']:
            # Comparison
            compare_running_vs_cycling(running_activities, cycling_activities)
    

    print("\n" + "="*60)
    print("🎉 Analysis complete! Hope you discovered some interesting insights!")
    print("="*60)

# This runs the program 
if __name__ == "__main__":
    main()