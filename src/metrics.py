import os
import glob
import pandas as pd
import sys

def analyze_api_metrics(log_message, log_dir="api_response_logs", days=7):
    # Get the application's base directory
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script - get project root directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level if we're in the src directory
        if os.path.basename(current_dir) == 'src':
            base_dir = os.path.dirname(current_dir)
        else:
            base_dir = current_dir

    log_dir = os.path.join(base_dir, log_dir)
    log_message(f"Looking for logs in: {log_dir}")  # Debug line
    
    # Combine all log files
    all_files = glob.glob(os.path.join(log_dir, "bw_api_metrics_*.csv"))
    if not all_files:
        log_message("\nNo API metrics files found!")
        return None
        
    df = pd.concat((pd.read_csv(f) for f in all_files))
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Filter for last N days
    recent_df = df[df['timestamp'] >= (pd.Timestamp.now() - pd.Timedelta(days=days))]
    
    log_message("\nAPI Performance Analysis")
    log_message("-" * 50)
    log_message(f"\nLast {days} days summary:")
    log_message(f"Total Requests: {len(recent_df)}")
    
    # Success rate
    success_rate = (recent_df['status'] == 'success').mean() * 100
    log_message(f"\nSuccess Rate: {success_rate:.1f}%")
    
    # Response time statistics
    log_message("\nResponse Time Statistics (seconds):")
    stats = recent_df['response_time'].describe()
    for stat_name, value in stats.items():
        log_message(f"{stat_name}: {value:.2f}")
    
    # Status breakdown
    log_message("\nStatus Breakdown:")
    for status, count in recent_df['status'].value_counts().items():
        log_message(f"{status}: {count}")
    
    # Daily success rates
    daily_stats = recent_df.groupby('date').agg({
        'status': lambda x: (x == 'success').mean() * 100,
        'response_time': 'mean'
    }).round(2)
    daily_stats.columns = ['Success Rate %', 'Avg Response Time']
    log_message("\nDaily Metrics (last 5 days):")
    for date, row in daily_stats.tail().iterrows():
        log_message(f"{date}: Success Rate={row['Success Rate %']}%, Avg Response Time={row['Avg Response Time']:.2f}s")
    
    return df

