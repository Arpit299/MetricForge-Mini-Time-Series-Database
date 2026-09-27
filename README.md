# MetricForge — Mini Time-Series Database

MetricForge is a lightweight time-series database implemented from scratch in Python.

It stores timestamped metric data, maintains sorted indexes for efficient range queries, calculates statistical summaries, performs rolling-window analysis, aggregates values into time buckets, and persists the database as JSON.

The project is designed to demonstrate practical data structures, indexing techniques, query processing, and time-series analytics without relying on an external database engine.

## Features

* Timestamped metric storage
* Multiple metric series
* Sorted timestamp indexing
* Binary-search range queries
* Fast latest-value lookup
* Min/max/average/sum statistics
* Percentile calculations
* Rolling-window averages
* Time-bucket aggregation
* Top-K and smallest-K queries
* CSV ingestion
* JSON persistence
* Database restore
* Command-line interface
* Built-in demo dataset
* Built-in self-test
* Standard-library-only implementation

## Tech Stack

**Python | Data Structures & Algorithms | Time-Series Analytics | Indexing | CLI | JSON | CSV**

## DSA Used

MetricForge uses core data structures and algorithms directly in the database engine:

* `dict` for metric and series indexing
* Sorted lists for timestamp indexes
* `bisect` for logarithmic boundary searches
* `deque` for rolling-window calculations
* `heapq` for Top-K and smallest-K queries
* Binary search for range selection
* Sorting for ordered time-series storage
* Sliding-window processing for rolling analytics

## Architecture

```text
Timestamped Data
       ↓
Metric Index
       ↓
Sorted Timestamp Series
       ↓
Binary Search
       ↓
Range Selection
       ↓
Statistics / Rolling Analysis / Aggregation
       ↓
JSON Persistence
```

## Example Data

```text
cpu,1727400000,61.4
cpu,1727400060,64.8
cpu,1727400120,69.2
memory,1727400000,48.6
memory,1727400060,51.1
```

Each record contains:

```text
metric
timestamp
value
```

## Installation

MetricForge uses only the Python standard library.

Clone the repository:

```bash
git clone https://github.com/Arpit299/metricforge.git
cd metricforge
```

No external packages are required.

## Run Directly

```bash
python metricforge.py
```

Running the file without arguments automatically executes the built-in self-test.

Example:

```text
SELF-TEST: PASS
```

## Run Self-Test

```bash
python metricforge.py --self-test
```

You can also use:

```bash
python metricforge.py self-test
```

## Run Demo

```bash
python metricforge.py demo
```

The demo creates sample metrics and demonstrates querying, statistics, rolling calculations, aggregation, and ranking.

## Insert Data

```bash
python metricforge.py insert cpu 1727400000 73.5
```

Insert another metric:

```bash
python metricforge.py insert memory 1727400060 52.7
```

## Query a Metric

```bash
python metricforge.py query cpu
```

Query within a timestamp range:

```bash
python metricforge.py query cpu --start 1727400000 --end 1727500000
```

The range query uses the sorted timestamp index with binary search to identify the relevant slice efficiently.

## Statistics

```bash
python metricforge.py stats cpu
```

Typical statistics include:

```text
count
sum
average
minimum
maximum
p50
p95
```

## Rolling Average

```bash
python metricforge.py rolling cpu 5
```

The rolling analysis uses a bounded `deque` to maintain the active window without repeatedly rebuilding the entire dataset.

## Time-Bucket Aggregation

```bash
python metricforge.py aggregate cpu 300
```

This groups timestamped values into fixed-size time buckets and calculates aggregated results for each interval.

## Top-K Values

```bash
python metricforge.py top cpu 5
```

This uses a heap-based approach to efficiently identify the highest values.

## CSV Workflow

MetricForge can load timestamped measurements from CSV files.

Example:

```text
metric,timestamp,value
cpu,1727400000,72.4
cpu,1727400060,75.2
memory,1727400000,49.8
memory,1727400060,53.1
```

The imported records can then be queried through the same indexing and analytics engine.

## Persistence

Database state can be saved to JSON and restored later.

Example persisted structure:

```text
metric
timestamp
value
```

This allows MetricForge to preserve data between executions without requiring a separate database server.

## Query Model

A range query follows this path:

```text
Query
 ↓
Metric Lookup
 ↓
Sorted Timestamp Index
 ↓
Binary Search
 ↓
Matching Range
 ↓
Result Set
```

Instead of scanning every record, MetricForge uses the ordered timestamp index to find the relevant boundaries.

## Rolling Analysis

For a rolling window:

```text
[10,20,30,40,50]
       ↓
Window = 3
       ↓
20
30
40
       ↓
30
30
```

The implementation maintains the active window using a `deque`, allowing efficient insertion and removal as time-series data moves forward.

## Time-Series Aggregation

MetricForge supports fixed-size temporal buckets.

Example:

```text
00:00 → 00:05
00:05 → 00:10
00:10 → 00:15
```

Each bucket can be analyzed independently to produce compact summaries from high-frequency data.

## Project Structure

```text
metricforge/
├── metricforge.py
└── README.md
```

## Example Workflow

```text
Raw Measurements
       ↓
Metric Storage
       ↓
Timestamp Index
       ↓
Binary Search
       ↓
Query
       ↓
Statistics
       ↓
Rolling Analysis
       ↓
Aggregation
       ↓
Persistence
```

## Use Cases

MetricForge can be used for:

* Application performance metrics
* CPU and memory monitoring
* IoT sensor data
* Server telemetry
* Network statistics
* Experiment measurements
* Financial time-series experiments
* System monitoring prototypes
* Time-series algorithm research

## Why MetricForge?

MetricForge demonstrates how a time-series database can be constructed from fundamental data structures and algorithms rather than simply connecting to an existing database.

The project focuses on:

```text
efficient indexing
fast range queries
stream-style analytics
time-based aggregation
memory-aware processing
persistent storage
```

## Limitations

MetricForge is intentionally lightweight and educational.

It does not provide:

* Distributed storage
* Replication
* Horizontal scaling
* Concurrent multi-process writes
* Network database access
* Enterprise-grade durability guarantees

The goal is to demonstrate the core mechanics behind a time-series database in a compact Python implementation.

## Future Improvements

Possible extensions include:

* Write-ahead logging
* Compression
* Concurrent readers and writers
* HTTP API
* SQL-like query language
* Downsampling
* Retention policies
* Multi-resolution indexes
* Memory-mapped storage
* On-disk B-tree indexing
* Real-time ingestion
* Web-based metrics dashboard


