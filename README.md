# DASH-Defense-LowOverhead

## Overview

This repository implements a defense mechanism against the **Beauty attack** for **DASH (Dynamic Adaptive Streaming over HTTP)** video streaming. The defense employs **low-overhead packet padding** and **timing obfuscation** to mitigate website fingerprinting attacks while minimizing bandwidth overhead.

The provided Python scripts analyze packet size statistics, modify packet traces, and evaluate the defense's effectiveness using a **k-Nearest Neighbors (k-NN)** classifier, leveraging the **LongEnough** dataset.

> **Based on the paper:**  
> *Optimizing DASH Video Streaming Defenses Against Website Fingerprinting: Low-Overhead Packet Padding and Timing Obfuscation*

> ⚠️ **This work is based on and extends the original repository:**  
> [trafnex/raising-the-bar](https://github.com/trafnex/raising-the-bar)

---

## Features

- **Packet Size Analysis**  
  Computes statistics (mean, standard deviation, min, max) for sent packets to inform padding strategies.

- **Defense Mechanism**  
  Applies low-overhead padding, timestamp scrambling, and dummy packet injection to obfuscate traffic patterns.

- **Overhead Analysis**  
  Compares bandwidth overhead between original and modified traces to quantify efficiency.

- **Attack Evaluation**  
  Uses a k-NN classifier to assess the Beauty attack's effectiveness on both original and defended traces.

---

## Dataset

The project uses the **LongEnough** and **LongEnough-defended** datasets, available at:

📂 **LongEnough Dataset**

- `LongEnough/`: Contains original packet traces in subfolders `0`, `1`, ..., `15`.
- `LongEnough-defended/`: Contains traces with applied defenses in the subfolder `constant_4000-scramblerz120z1100z400z1000`.

---

## Repository Structure

| File | Description |
|------|-------------|
| `analyze_packet_size.py` | Analyzes packet size statistics in the LongEnough dataset and saves results to `packet_size_stats.csv`. |
| `modify_padding_improved.py` | Modifies packet traces by applying defense mechanisms, outputs `_modified.log` files, and saves stats to `overhead_stats.csv`. |
| `analyze_overhead.py` | Compares bandwidth overhead of original and modified traces, outputs `overhead_comparison.csv`. |
| `beauty_modified_knn.py` | Implements k-NN classifier to evaluate Beauty attack. Extracts features and saves results. |
| `requirements.txt` | Lists required Python packages. |

---

## Requirements

Install the required Python packages:

```

pandas>=1.5.0
numpy>=1.23.0
scikit-learn>=1.2.0

````

Install via pip:

```bash
pip install -r requirements.txt
````

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/DASH-Defense-LowOverhead.git
cd DASH-Defense-LowOverhead
```

### 2. Download the Dataset

Download the LongEnough and LongEnough-defended datasets from the provided link.
Place them in the project root as:

```
./LongEnough/
./LongEnough-defended/
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Analyze Packet Sizes

```bash
python analyze_packet_size.py
```

* **Input:** `.log` files in `LongEnough/0`, `1`, ..., `15`
* **Output:** `packet_size_stats.csv`

---

### Apply Defense Mechanism

```bash
python modify_padding_improved.py
```

* **Input:** `.log` files in `LongEnough-defended/constant_4000-scramblerz120z1100z400z1000/`
* **Output:**

  * Modified traces: `*_modified.log`
  * Overhead statistics: `overhead_stats.csv`

---

### Analyze Overhead

```bash
python analyze_overhead.py
```

* **Input:** Original and modified `.log` files in `LongEnough-defended/`
* **Output:** `overhead_comparison.csv`

---

### Evaluate Beauty Attack

```bash
python beauty_modified_knn.py ./LongEnough-defended --extract --modified
```

**Arguments:**

* `path`: Dataset directory path (e.g., `./LongEnough-defended`)
* `--extract`: Extract and save features to `features.txt`
* `--modified`: Use `_modified.log` files
* `--start` and `--end`: Eavesdropping window (default: `60` and `0` seconds)

**Example:**

```bash
python beauty_modified_knn.py ./LongEnough-defended --extract --modified
```

* **Output:** `features.txt` (if `--extract` is used)
* Prints train/test accuracy metrics

---

## Output Files

* `packet_size_stats.csv`: Stats (mean, std, min, max, count) for sent packets.
* `overhead_stats.csv`: Overhead stats for modified traces.
* `overhead_comparison.csv`: Overhead comparison (original vs modified).
* `features.txt`: Extracted features for k-NN classifier.
* `*_modified.log`: Defended packet traces.

---

## Notes

* **Dataset Structure:**

  * `LongEnough/`: subfolders `0`, `1`, ..., `15`
  * `LongEnough-defended/constant_4000-scramblerz120z1100z400z1000/`

* **Timestamp Handling:**
  Uses 64-bit integers for nanosecond timestamps to avoid overflow.

* **Log File Cleaning:**
  Non-numeric values are skipped with warnings.

* **Classifier Parameters:**
  Default `n_neighbors=5` (can be adjusted in `beauty_modified_knn.py`).

* **Error Handling:**
  Robust checks for missing files, invalid data, and processing errors.

---

## Contributing

Contributions are welcome!

### To contribute:

1. Fork the repository
2. Create a feature branch

   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit your changes

   ```bash
   git commit -m "Add your feature"
   ```
4. Push to your fork

   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request

> **Note:** Please open an issue first to propose changes or report bugs.

---

## License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions, support, or feedback:

* Open an issue on GitHub
* Contact the repository maintainers via GitHub

---

## Acknowledgments

* Thanks to the **LongEnough** dataset providers for making the data publicly available.
* **Original source code and inspiration** from:
  [trafnex/raising-the-bar](https://github.com/trafnex/raising-the-bar)



