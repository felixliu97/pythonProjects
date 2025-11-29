from croniter import croniter
from datetime import datetime, time
import pytz

def get_cron_execution_window(cron_expressions, timezone, base_time_utc, config_ids=None):
    """
    Get the execution window (from previous to next cron time) for multiple cron expressions.
    
    Args:
        cron_expressions (list): List of cron expressions for the same job
        timezone (str): The timezone of the cron expressions
        base_time_utc (datetime): The reference time in UTC
        config_ids (list): List of config IDs corresponding to each cron expression
    
    Returns:
        tuple: (window_start, window_end, window_config_id) as naive datetime objects and config_id
               window_start: The most recent previous execution time
               window_end: The next upcoming execution time
               window_config_id: The config ID that corresponds to the window end time
    """
    if not cron_expressions:
        raise ValueError("At least one cron expression must be provided")
    
    # Set default config IDs if not provided
    if config_ids is None:
        config_ids = [f"config_{i+1}" for i in range(len(cron_expressions))]
    
    if len(cron_expressions) != len(config_ids):
        raise ValueError("Number of cron expressions must match number of config IDs")
    
    # Set the timezone
    tz = pytz.timezone(timezone)
    
    # Convert base time to the cron's timezone
    base_time_tz = base_time_utc.astimezone(tz)
    
    # Get all previous and next times for each cron expression
    all_previous_times = []
    all_next_times = []
    next_time_configs = {}  # Map next times to their config IDs
    
    for i, cron_expr in enumerate(cron_expressions):
        cron = croniter(cron_expr, base_time_tz)
        
        # Get previous execution time
        prev_time_tz = cron.get_prev(datetime)
        prev_time_utc = prev_time_tz.astimezone(pytz.UTC).replace(tzinfo=None)
        all_previous_times.append(prev_time_utc)
        
        # Get next execution time
        next_time_tz = cron.get_next(datetime)
        next_time_utc = next_time_tz.astimezone(pytz.UTC).replace(tzinfo=None)
        all_next_times.append(next_time_utc)
        
        # Store the config ID for this next time
        next_time_configs[next_time_utc] = config_ids[i]
    
    # Find the window boundaries
    # Window start: most recent previous execution time
    window_start = max(all_previous_times)
    
    # Window end: next upcoming execution time
    window_end = min(all_next_times)
    
    # Get the config ID for the window end time
    window_config_id = next_time_configs[window_end]
    
    return window_start, window_end, window_config_id

def get_cron_timestamp_utc(cron_expression, timezone, base_time, count=1):
    """
    Get next or previous cron timestamps in UTC based on count.
    Positive count returns next timestamps, negative count returns previous timestamps.
    
    Args:
        cron_expression (str): The cron expression to evaluate
        timezone (str): The timezone of the cron expression
        base_time (datetime): The reference time in UTC
        count (int): Number of timestamps to return. Positive for next, negative for previous
    
    Returns:
        list: List of UTC timestamps as naive datetime objects
        
    Raises:
        ValueError: If base_time is None or invalid
    """
    if base_time is None:
        raise ValueError("base_time cannot be None")
    
    # Set the timezone
    tz = pytz.timezone(timezone)
    
    # Convert base time to the cron's timezone
    base_time_tz = base_time.astimezone(tz)
    
    # Create croniter object in the cron's timezone
    cron = croniter(cron_expression, base_time_tz)
    
    timestamps = []
    if count > 0:
        # Get next timestamps
        for _ in range(count):
            next_time_tz = cron.get_next(datetime)
            # Convert to UTC and then to naive datetime
            next_time_utc = next_time_tz.astimezone(pytz.UTC)
            next_time_naive = next_time_utc.replace(tzinfo=None)
            timestamps.append(next_time_naive)
    else:
        # Get previous timestamps
        for _ in range(abs(count)):
            prev_time_tz = cron.get_prev(datetime)
            # Convert to UTC and then to naive datetime
            prev_time_utc = prev_time_tz.astimezone(pytz.UTC)
            prev_time_naive = prev_time_utc.replace(tzinfo=None)
            timestamps.append(prev_time_naive)
    
    return timestamps

def get_current_utc_date_end():
    """
    Get the end timestamp (23:59:59) of the current UTC date.
    
    Returns:
        datetime: End timestamp of current UTC date as naive datetime object
    """
    current_utc = datetime.now(pytz.UTC)
    end_time = datetime.combine(current_utc.date(), time(23, 59, 59))
    return end_time.replace(tzinfo=None)

def main():
    # Example cron expressions for the same job with config IDs
    cron_expressions = ["30 0 * * *", "30 8 * * *", "30 16 * * *"]
    config_ids = ["config_001", "config_002", "config_003"]
    timezone = "UTC"
    current_time = datetime.now(pytz.UTC)
    current_date_end = get_current_utc_date_end()
    
    print(f"Current UTC time: {current_time.replace(tzinfo=None)}")
    print(f"Current UTC date end: {current_date_end}\n")
    
    # Get execution window for multiple crons
    window_start, window_end, window_config_id = get_cron_execution_window(
        cron_expressions, timezone, current_time, config_ids
    )
    print(f"Execution Window:")
    print(f"Window start (UTC): {window_start}")
    print(f"Window end (UTC): {window_end}")
    print(f"Window config ID: {window_config_id}")
    print(f"Window duration: {window_end - window_start}")
    print("-" * 50)
    
    # Show individual cron details
    for i, cron in enumerate(cron_expressions):
        print(f"Cron {i+1}: {cron}")
        print(f"Config ID: {config_ids[i]}")
        print(f"Timezone: {timezone}")
        
        # Get next execution time
        next_time = get_cron_timestamp_utc(cron, timezone, current_time, count=1)[0]
        print(f"Next execution (UTC): {next_time}")
        
        # Get previous execution time
        prev_time = get_cron_timestamp_utc(cron, timezone, current_time, count=-1)[0]
        print(f"Previous execution (UTC): {prev_time}")
        print("-" * 30)

if __name__ == "__main__":
    main()
