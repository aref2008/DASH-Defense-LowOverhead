import pandas as pd
import os
import glob
from pathlib import Path

# Path to the LongEnough-defended dataset directory
data_dir = './LongEnough-defended'

# Scrambler subfolder to process
scrambler_folder = os.path.join(data_dir, 'constant_4000-scramblerz120z1100z400z1000')

# Discover all subfolders dynamically
subfolders = [f for f in os.listdir(scrambler_folder) 
              if os.path.isdir(os.path.join(scrambler_folder, f))]

# List to store overhead statistics
overhead_stats = []

# Find all .log and _modified.log files in the discovered subfolders
log_files = []
modified_log_files = []
for subfolder in subfolders:
    subfolder_path = os.path.join(scrambler_folder, subfolder)
    log_files.extend([f for f in glob.glob(os.path.join(subfolder_path, '*.log')) 
                      if not f.endswith('.qoe.log') and '_modified.log' not in f])
    modified_log_files.extend([f for f in glob.glob(os.path.join(subfolder_path, '*_modified.log')) 
                              if not f.endswith('.qoe.log')])

# Check if any log files were found
if not log_files or not modified_log_files:
    print("No .log or _modified.log files found in Scrambler subfolders:", subfolders)
    exit()

# Process each pair of original and modified .log files
for log_file in log_files:
    try:
        # Find corresponding modified file
        modified_file = log_file.replace('.log', '_modified.log')
        if modified_file not in modified_log_files:
            print(f"Warning: No modified file found for {log_file}")
            continue
        
        # Load original .log file
        df_original = pd.read_csv(log_file, 
                                  names=['timestamp_ns', 'event_type', 'packet_size', 
                                         'absolute_timestamp', 'cumulative_sent', 'cumulative_received'])
        
        # Load modified .log file
        df_modified = pd.read_csv(modified_file, 
                                  names=['timestamp_ns', 'event_type', 'packet_size', 
                                         'absolute_timestamp', 'cumulative_sent', 'cumulative_received'])
        
        # Ensure packet_size is numeric
        df_original['packet_size'] = pd.to_numeric(df_original['packet_size'], errors='coerce')
        df_modified['packet_size'] = pd.to_numeric(df_modified['packet_size'], errors='coerce')
        
        # Check for non-numeric values
        if df_original['packet_size'].isna().any():
            print(f"Warning: Non-numeric packet_size values found in {log_file}. Skipping invalid rows.")
            df_original = df_original.dropna(subset=['packet_size'])
        if df_modified['packet_size'].isna().any():
            print(f"Warning: Non-numeric packet_size values found in {modified_file}. Skipping invalid rows.")
            df_modified = df_modified.dropna(subset=['packet_size'])
        
        # Calculate overhead (total packet size)
        original_overhead = df_original['packet_size'].sum()
        modified_overhead = df_modified['packet_size'].sum()
        
        # Store statistics
        stats = {
            'file': log_file,
            'original_overhead': original_overhead,
            'modified_overhead': modified_overhead,
            'overhead_reduction': original_overhead - modified_overhead,
            'overhead_reduction_percentage': (original_overhead - modified_overhead) / original_overhead * 100
        }
        overhead_stats.append(stats)
        
        print(f"Processed {log_file}:")
        print(f"  Original overhead: {original_overhead} bytes")
        print(f"  Modified overhead: {modified_overhead} bytes")
        print(f"  Overhead reduction: {stats['overhead_reduction']} bytes ({stats['overhead_reduction_percentage']:.2f}%)")
        
    except Exception as e:
        print(f"Error processing {log_file}: {e}")

# Convert overhead statistics to a DataFrame
overhead_df = pd.DataFrame(overhead_stats)

# Check if any statistics were collected
if overhead_df.empty:
    print("No valid statistics collected. Check the log files for packet_size data.")
    exit()

# Calculate aggregated overhead statistics
overall_original_overhead = overhead_df['original_overhead'].sum()
overall_modified_overhead = overhead_df['modified_overhead'].sum()
overall_reduction = overall_original_overhead - overall_modified_overhead
overall_reduction_percentage = (overall_reduction / overall_original_overhead * 100) if overall_original_overhead > 0 else 0

# Print aggregated overhead statistics
print("\nAggregated overhead statistics across all Scrambler .log files:")
print(f"Total original overhead: {overall_original_overhead} bytes")
print(f"Total modified overhead: {overall_modified_overhead} bytes")
print(f"Total overhead reduction: {overall_reduction} bytes ({overall_reduction_percentage:.2f}%)")

# Save overhead statistics to a CSV file
overhead_df.to_csv('overhead_comparison.csv', index=False)
print("Overhead comparison statistics saved to overhead_comparison.csv")