import pandas as pd
import os
import glob
from pathlib import Path
import numpy as np

# Path to the LongEnough-defended dataset directory
data_dir = './LongEnough-defended'

# Scrambler subfolder to process
scrambler_folder = os.path.join(data_dir, 'constant_4000-scramblerz120z1100z400z1000')

# Discover all subfolders dynamically
subfolders = [f for f in os.listdir(scrambler_folder) 
              if os.path.isdir(os.path.join(scrambler_folder, f))]

# Parameters for improved defense based on LongEnough analysis
padding_size_range = (50, 70)  # Random padding size between 50-70 bytes (based on mean 52.69 bytes)
time_scramble_std = 5000000  # Standard deviation for time scrambling (5 ms in nanoseconds)
padding_reduction_ratio = 0.3  # Keep 30% of padding packets
extra_dummy_packets = 15  # Add 15 extra dummy packets at random times

# List to store overhead statistics
overhead_stats = []

# Find all .log files (excluding .qoe.log and _modified.log) in the discovered subfolders
log_files = []
for subfolder in subfolders:
    subfolder_path = os.path.join(scrambler_folder, subfolder)
    log_files.extend([f for f in glob.glob(os.path.join(subfolder_path, '*.log')) 
                      if not f.endswith('.qoe.log') and '_modified.log' not in f])

# Check if any log files were found
if not log_files:
    print("No original .log files (excluding .qoe.log and _modified.log) found in Scrambler subfolders:", subfolders)
    exit()

# Process each .log file
for log_file in log_files:
    try:
        # Load the .log file
        df = pd.read_csv(log_file, 
                         names=['timestamp_ns', 'event_type', 'packet_size', 
                                'absolute_timestamp', 'cumulative_sent', 'cumulative_received'])
        
        # Ensure packet_size and timestamp_ns are numeric
        df['packet_size'] = pd.to_numeric(df['packet_size'], errors='coerce')
        df['timestamp_ns'] = pd.to_numeric(df['timestamp_ns'], errors='coerce', downcast='integer')
        
        # Check for non-numeric values
        if df['packet_size'].isna().any() or df['timestamp_ns'].isna().any():
            print(f"Warning: Non-numeric values found in {log_file}. Skipping invalid rows.")
            df = df.dropna(subset=['packet_size', 'timestamp_ns'])
        
        # Ensure timestamp_ns is int64 to avoid overflow
        df['timestamp_ns'] = df['timestamp_ns'].astype(np.int64)
        
        # Calculate original overhead (total packet size)
        original_overhead = df['packet_size'].sum()
        
        # Modify padding packets
        df_modified = df.copy()
        
        # 1. Reduce padding packets (keep only a fraction)
        padding_mask = df_modified['event_type'].isin(['sp', 'rp'])
        padding_indices = df_modified[padding_mask].index
        if len(padding_indices) > 0:
            keep_indices = np.random.choice(padding_indices, 
                                           size=int(len(padding_indices) * padding_reduction_ratio), 
                                           replace=False)
            df_modified = df_modified.drop(padding_indices[~padding_indices.isin(keep_indices)])
        
        # 2. Randomize padding packet sizes (sp, rp)
        mask = df_modified['event_type'].isin(['sp', 'rp'])
        df_modified.loc[mask, 'packet_size'] = np.random.randint(
            padding_size_range[0], padding_size_range[1] + 1, size=mask.sum(), dtype=np.int64
        )
        
        # 3. Add time scrambling to all packets
        time_noise = np.random.normal(0, time_scramble_std, size=len(df_modified)).astype(np.int64)
        df_modified['timestamp_ns'] = df_modified['timestamp_ns'] + time_noise
        df_modified['timestamp_ns'] = df_modified['timestamp_ns'].clip(lower=0).astype(np.int64)
        
        # 4. Update absolute_timestamp to maintain consistency
        start_time = df_modified['absolute_timestamp'].iloc[0]
        df_modified['absolute_timestamp'] = start_time + (df_modified['timestamp_ns'] / 1e6).astype(np.int64)
        
        # 5. Add extra dummy packets at random times
        max_time = df_modified['timestamp_ns'].max()
        if max_time > np.iinfo(np.int64).max:
            print(f"Warning: max_time ({max_time}) exceeds int64 limit in {log_file}. Using int64.")
        dummy_times = np.random.randint(0, max_time + 1, size=extra_dummy_packets, dtype=np.int64)
        dummy_types = np.random.choice(['sp', 'rp'], size=extra_dummy_packets)
        dummy_sizes = np.random.randint(padding_size_range[0], padding_size_range[1] + 1, 
                                        size=extra_dummy_packets, dtype=np.int64)
        dummy_cumulative_sent = [1 if t == 'sp' else 0 for t in dummy_types]
        dummy_cumulative_received = [1 if t == 'rp' else 0 for t in dummy_types]
        
        dummy_df = pd.DataFrame({
            'timestamp_ns': dummy_times,
            'event_type': dummy_types,
            'packet_size': dummy_sizes,
            'absolute_timestamp': start_time + (dummy_times / 1e6).astype(np.int64),
            'cumulative_sent': dummy_cumulative_sent,
            'cumulative_received': dummy_cumulative_received
        })
        
        df_modified = pd.concat([df_modified, dummy_df], ignore_index=True)
        df_modified = df_modified.sort_values('timestamp_ns').reset_index(drop=True)
        
        # Update cumulative_sent and cumulative_received
        df_modified['cumulative_sent'] = (df_modified['event_type'] == 's').cumsum() + \
                                        (df_modified['event_type'] == 'sp').cumsum()
        df_modified['cumulative_received'] = (df_modified['event_type'] == 'r').cumsum() + \
                                            (df_modified['event_type'] == 'rp').cumsum()
        
        # Calculate modified overhead
        modified_overhead = df_modified['packet_size'].sum()
        
        # Save modified data to a new file
        modified_file = log_file.replace('.log', '_modified.log')
        df_modified.to_csv(modified_file, index=False)
        
        # Store overhead statistics
        stats = {
            'file': log_file,
            'original_overhead': original_overhead,
            'modified_overhead': modified_overhead,
            'overhead_reduction': original_overhead - modified_overhead
        }
        overhead_stats.append(stats)
        
        print(f"Processed {log_file}:")
        print(f"  Original overhead: {original_overhead} bytes")
        print(f"  Modified overhead: {modified_overhead} bytes")
        print(f"  Overhead reduction: {stats['overhead_reduction']} bytes")
        print(f"  Modified file saved as: {modified_file}")
        
    except Exception as e:
        print(f"Error processing {log_file}: {e}")

# Convert overhead statistics to a DataFrame
overhead_df = pd.DataFrame(overhead_stats)

# Check if any statistics were collected
if overhead_df.empty:
    print("No valid statistics collected. Check the log files for padding packets.")
    exit()

# Calculate aggregated overhead statistics
overall_original_overhead = overhead_df['original_overhead'].sum()
overall_modified_overhead = overhead_df['modified_overhead'].sum()
overall_reduction = overall_original_overhead - overall_modified_overhead

# Print aggregated overhead statistics
print("\nAggregated overhead statistics across all Scrambler .log files:")
print(f"Total original overhead: {overall_original_overhead} bytes")
print(f"Total modified overhead: {overall_modified_overhead} bytes")
print(f"Total overhead reduction: {overall_reduction} bytes")

# Save overhead statistics to a CSV file
overhead_df.to_csv('overhead_stats.csv', index=False)
print("Overhead statistics saved to overhead_stats.csv")