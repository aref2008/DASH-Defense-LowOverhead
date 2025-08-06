import pandas as pd
import os
import glob
from pathlib import Path

# Path to the LongEnough dataset directory
data_dir = './LongEnough'

# List of subfolders to process
subfolders = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']

# List to store statistics for each log file
stats_list = []

# Find all .log files (excluding .qoe.log) in the specified subfolders
log_files = []
for subfolder in subfolders:
    subfolder_path = os.path.join(data_dir, subfolder)
    # Get all .log files, excluding those with .qoe.log
    log_files.extend([f for f in glob.glob(os.path.join(subfolder_path, '*.log')) 
                      if not f.endswith('.qoe.log')])

# Check if any log files were found
if not log_files:
    print("No .log files (excluding .qoe.log) found in the subfolders:", subfolders)
    exit()

# Process each .log file
for log_file in log_files:
    try:
        # Load the .log file
        df = pd.read_csv(log_file, 
                         names=['timestamp_ns', 'event_type', 'packet_size', 
                                'absolute_timestamp', 'cumulative_sent', 'cumulative_received'])
        
        # Filter sent packets (event_type == 's')
        sent_packets = df[df['event_type'] == 's']
        
        # Check if there are sent packets
        if not sent_packets.empty:
            # Calculate packet size statistics
            stats = {
                'file': log_file,
                'mean_packet_size': sent_packets['packet_size'].mean(),
                'std_packet_size': sent_packets['packet_size'].std(),
                'min_packet_size': sent_packets['packet_size'].min(),
                'max_packet_size': sent_packets['packet_size'].max(),
                'count': len(sent_packets)
            }
            stats_list.append(stats)
        else:
            print(f"Warning: No sent packets found in {log_file}")
            
    except Exception as e:
        print(f"Error processing {log_file}: {e}")

# Convert statistics to a DataFrame
stats_df = pd.DataFrame(stats_list)

# Check if any statistics were collected
if stats_df.empty:
    print("No valid statistics collected. Check the log files for sent packets.")
    exit()

# Calculate aggregated statistics across all files
overall_mean = stats_df['mean_packet_size'].mean()
overall_std = stats_df['std_packet_size'].mean()
overall_min = stats_df['min_packet_size'].min()
overall_max = stats_df['max_packet_size'].max()

# Print aggregated statistics
print("Aggregated packet size statistics for sent packets across all .log files:")
print(f"Mean packet size: {overall_mean:.2f} bytes")
print(f"Mean standard deviation: {overall_std:.2f} bytes")
print(f"Minimum packet size: {overall_min:.2f} bytes")
print(f"Maximum packet size: {overall_max:.2f} bytes")
print(f"Total number of sent packets: {stats_df['count'].sum()}")

# Save statistics to a CSV file
stats_df.to_csv('packet_size_stats.csv', index=False)
print("Statistics saved to packet_size_stats.csv")