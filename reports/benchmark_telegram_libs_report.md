# Telegram HTTP Library Benchmark
## Overview
- **Date:** 2025-05-08 14:28:06
- **Number of Messages per Library:** 2
- **Libraries Tested:** httpx, aiohttp, requests, urllib3
- **Python Version:** 3.13.2
- **Platform:** Windows-11-10.0.26100-SP0

---

## Summary of Best Performers
- **Fastest Avg. Telegram Send Time:** urllib3 (0.7129s)
- **Highest Success Rate:** httpx (100.00%)
- **Lowest Memory Usage (Workflow):** requests (0.13 MB)
- **Lowest CPU Usage (Workflow):** aiohttp (0.00%)

---

## Detailed Results per Library
| Library | Version | Avg TG Send (s) | Min TG Send (s) | Max TG Send (s) | Total Runs | Success Runs | Failed Runs | Success Rate (%) | CPU (%) | Memory (MB) |
|---------|---------|-----------------|-----------------|-----------------|------------|--------------|-------------|------------------|---------|-------------|
| httpx | 0.27.0 | 1.2047 | 1.1623 | 1.2472 | 2 | 2 | 0 | 100.00 | 13.73 | 4.20 |
| aiohttp | 3.9.5 | 0.9639 | 0.9637 | 0.9641 | 2 | 2 | 0 | 100.00 | 0.00 | 1.37 |
| requests | 2.32.3 | 0.9818 | 0.9592 | 1.0043 | 2 | 2 | 0 | 100.00 | 0.00 | 0.13 |
| urllib3 | 2.2.2 | 0.7129 | 0.4481 | 0.9777 | 2 | 2 | 0 | 100.00 | 0.96 | 0.27 |

---

## Performance Rankings & Visualizations

### Fastest Average Telegram Send Time

![Avg TG Send Time Plot](plot_avg_telegram_send_time.png)

| Rank | Library | Avg Time (s) |
|------|---------|--------------|
| 1 | urllib3 | 0.7129 |
| 2 | aiohttp | 0.9639 |
| 3 | requests | 0.9818 |
| 4 | httpx | 1.2047 |


### Highest Success Rate

![Success/Failure Rate Plot](plot_success_failure_rate.png)

| Rank | Library | Success Rate (%) |
|------|---------|------------------|
| 1 | httpx | 100.00 |
| 2 | aiohttp | 100.00 |
| 3 | requests | 100.00 |
| 4 | urllib3 | 100.00 |


## Resource Usage Rankings (Lower is Better - Placeholders)

### Lowest Memory Usage (Workflow)

![Memory Usage Plot](plot_memory_increase.png)

| Rank | Library | Memory Increase (MB) |
|------|---------|----------------------|
| 1 | requests | 0.13 |
| 2 | urllib3 | 0.27 |
| 3 | aiohttp | 1.37 |
| 4 | httpx | 4.20 |


### Lowest CPU Usage (Workflow)

![CPU Usage Plot](plot_cpu_usage.png)

| Rank | Library | CPU Usage (%) |
|------|---------|---------------|
| 1 | aiohttp | 0.00 |
| 2 | requests | 0.00 |
| 3 | urllib3 | 0.96 |
| 4 | httpx | 13.73 |


---

## Conclusion
This benchmark measures the performance of different Python HTTP client libraries for sending messages to the Telegram API. The metrics focus on the Telegram message send time, success rates, and resource utilization.