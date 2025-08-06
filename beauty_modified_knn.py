import argparse
import ast
import math
import numpy as np
import os
import random
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

FEATURE_PATH = "features.txt"

def get_last_time(lines):
    for line in reversed(lines):
        tokens = line.split(",")
        if len(tokens) < 2:
            continue
        if "r" == tokens[1] or "r+p" == tokens[1] or "s" == tokens[1] or "s+p" == tokens[1]:
            try:
                last_time = int(tokens[0]) / 1000000000
                last_time = math.ceil(last_time / 2) * 2
                return last_time
            except ValueError:
                continue
    return -1

def get_packet_count(trace_file, direction, start, end):
    counts = []
    
    try:
        with open(trace_file) as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {trace_file}: {e}")
        return counts
    
    last_time = get_last_time(lines)
    if last_time == -1:
        print(f"Warning: No valid packets found in {trace_file}")
        return counts
    
    for line in lines:
        tokens = line.split(",")
        if len(tokens) < 2:
            continue
        try:
            timestamp = int(tokens[0]) / 1000000000
        except ValueError:
            continue
        
        if timestamp < last_time - start:
            continue
        if timestamp >= last_time - end:
            break
        
        if direction not in tokens[1]:
            continue
        
        offset = (timestamp - (last_time - start)) * 4.0
        
        while len(counts) <= offset:
            counts.append(0)
        
        counts[math.floor(offset)] += 1
    
    offset = (start - end) * 4.0
    while len(counts) < offset:
        counts.append(0)
    
    return counts

def extract_features(path, start, end, modified=False):
    all_pairs = []
    
    max_pps_up = None
    max_pps_down = None
    max_pps_all = None
    
    video_folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    num_classes = len(video_folders)
    print(f"Found {num_classes} video folders: {video_folders}")
    
    for video in video_folders:
        video_root = os.path.join(path, video)
        all_traces = [file for file in os.listdir(video_root) if (not modified and ".log" in file and file.count(".") == 1 and "_modified.log" not in file) or (modified and "_modified.log" in file)]
        print(f"Found {len(all_traces)} traces in {video_root}: {all_traces}")
        
        if not all_traces:
            print(f"Warning: No valid traces found in {video_root}")
            continue
        
        for trace in all_traces:
            trace_file = os.path.join(video_root, trace)
            
            pps_up = get_packet_count(trace_file, "s", start, end)
            pps_down = get_packet_count(trace_file, "r", start, end)
            pps_all = [pps_up[i] + pps_down[i] for i in range(len(pps_up))]
            
            if not pps_up or not pps_down:
                print(f"Warning: Empty packet counts for {trace_file}")
                continue
            
            pps_up = [value / 0.25 for value in pps_up]
            pps_down = [value / 0.25 for value in pps_down]
            pps_all = [value / 0.25 for value in pps_all]
            
            max_pps_up = max(max_pps_up, max(pps_up)) if max_pps_up else max(pps_up)
            max_pps_down = max(max_pps_down, max(pps_down)) if max_pps_down else max(pps_down)
            max_pps_all = max(max_pps_all, max(pps_all)) if max_pps_all else max(pps_all)
            
            labels = [0.0] * num_classes
            try:
                labels[int(video)] = 1.0
            except ValueError:
                print(f"Warning: Invalid video folder name {video}, skipping")
                continue
            
            all_pairs.append(([pps_down, pps_up, pps_all], labels))
    
    if not all_pairs:
        print("Error: No valid features extracted")
        exit()
    
    for i in range(len(all_pairs)):
        for j in range((start - end) * 4):
            all_pairs[i][0][0][j] /= max_pps_down
            all_pairs[i][0][1][j] /= max_pps_up
            all_pairs[i][0][2][j] /= max_pps_all
    
    print(f"Extracted {len(all_pairs)} feature-label pairs")

    feature_set = {tuple(np.concatenate(x)) for x, _ in all_pairs}
    print(f"Unique feature vectors: {len(feature_set)}, Total pairs: {len(all_pairs)}")

    with open(FEATURE_PATH, "w") as f:
        f.write(f"{all_pairs}\n")
    
    return num_classes

def load_features():
    with open(FEATURE_PATH) as f:
        lines = f.readlines()
    all_pairs = ast.literal_eval(lines[0])
    
    random.shuffle(all_pairs)
    split = math.floor(len(all_pairs) * 0.7)
    
    train_x = [np.concatenate(x) for x, _ in all_pairs[:split]]  # Flatten features
    train_y = [np.argmax(y) for _, y in all_pairs[:split]]       # Convert one-hot to class index
    
    test_x = [np.concatenate(x) for x, _ in all_pairs[split:]]
    test_y = [np.argmax(y) for _, y in all_pairs[split:]]
    
    print(f"Training set size: {len(train_x)}, Test set size: {len(test_x)}")
    
    return np.array(train_x), np.array(train_y), np.array(test_x), np.array(test_y)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="trace dataset for use in attack")
    parser.add_argument("-s", "--start", help="eavesdropping start time, in seconds from end of trace", type=int, default=60)
    parser.add_argument("-e", "--end", help="eavesdropping end time, in seconds from end of trace", type=int, default=0)
    parser.add_argument("--extract", help="extract features, required when running first time", action="store_true")
    parser.add_argument("--modified", help="process _modified.log files instead of .log files", action="store_true")
    args = parser.parse_args()
    
    if args.extract:
        num_classes = extract_features(args.path, args.start, args.end, args.modified)
    else:
        num_classes = len([f for f in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, f))])
    
    # Train and evaluate k-NN
    train_x, train_y, test_x, test_y = load_features()
    
    knn = KNeighborsClassifier(n_neighbors=5)  # k=5 as a starting point
    knn.fit(train_x, train_y)
    
    train_pred = knn.predict(train_x)
    test_pred = knn.predict(test_x)
    
    train_accuracy = accuracy_score(train_y, train_pred)
    test_accuracy = accuracy_score(test_y, test_pred)
    
    print(f"Train accuracy: {train_accuracy:.4f}")
    print(f"Test accuracy: {test_accuracy:.4f}")