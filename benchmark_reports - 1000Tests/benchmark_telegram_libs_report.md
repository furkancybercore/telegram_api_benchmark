# Telegram HTTP Library Benchmark
## Overview
- **Date:** 2025-05-09 05:44:29 (Sydney UTC+10)
- **Number of Messages per Library:** 1000
- **Libraries Tested:** httpx, aiohttp, requests, urllib3, uplink, ptb, pytelegrambotapi
- **Python Version:** 3.13.2
- **Platform:** Windows-11-10.0.26100-SP0
- **GitHub Project:** [telegram_api_benchmark](https://github.com/furkancybercore/telegram_api_benchmark)

---

## Test Methodology
This benchmark test was conducted using the following steps:
- We created a PostgreSQL database to store test messages
- For each HTTP library, we:
  - Read messages from the database
  - Sent these messages to the Telegram API
  - Measured performance and resource usage
- Due to Telegram's message limit (20 messages per minute), we sent messages to a personal Telegram account instead of a channel
- This allowed us to run 1000 tests for each method
- We compared different Python HTTP libraries including requests, httpx, aiohttp, urllib3, etc.
- Each test measures success rate, speed, and computer resource usage

---

## Summary of Best Performers
**Performance Metrics:**
- **Success Rate:** 100.00% (httpx)
- **Total Processing Time:** 0.4502s (python-telegram-bot)
- **Throughput:** 2.24 msg/s (aiohttp)
- **HTTP Send Time:** 0.0000s (N/A)
- **DB Read Time:** 0.00000s (N/A)
- **Consistency (Lowest Std Dev):** 0.0236s (requests)
- **Response Size:** 0.0 bytes (N/A)
 
**Resource Usage Metrics:**
- **CPU Usage:** 0.20% (urllib3)
- **Memory Usage:** 0.24 MB (requests)

---

## All Metrics Comparison
The table below compares all libraries across the key metrics:

| Library | Success Rate (%) | Throughput (msg/s) | Avg Total Time (s) | Std Dev Total (s) | CPU Usage (%) | Memory (MB) | Avg HTTP Time (s) | Avg DB Read (s) | Avg Response Size (B) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| httpx | 100.00 | 2.20 | 0.4549 | 0.0766 | 0.33 | 3.41 | 0.4546 | 0.00027 | 255.6 |
| aiohttp | 53.00 | 2.24 | 0.4548 | 0.0626 | 0.22 | 1.65 | 0.4545 | 0.00029 | 257.8 |
| requests | 6.30 | 1.04 | 0.9679 | 0.0236 | 0.43 | 0.24 | 0.9676 | 0.00029 | 259.0 |
| urllib3 | 83.70 | 2.19 | 0.4598 | 0.1040 | 0.20 | 0.71 | 0.4595 | 0.00033 | 257.9 |
| uplink | 14.00 | 2.24 | 0.4533 | 0.0556 | 0.23 | 0.87 | 0.4530 | 0.00028 | 257.0 |
| python-telegram-bot | 76.00 | 2.23 | 0.4502 | 0.0574 | 0.45 | 2.01 | 0.4499 | 0.00030 | 375.9 |
| pytelegrambotapi | 0.00 | 2.30 | 0.0000 | 0.0000 | 0.25 | 0.93 | 0.0000 | 0.00000 | 0.0 |

---

## Performance

#### Success Rate
> _Number of attempts (DB read + Telegram send) that completed successfully. Higher is better._


![Success Rate Plot](plot_success_failure_rate.png)


#### Throughput
> _Messages processed per second. Higher indicates better efficiency._


![Throughput Plot](plot_throughput.png)


#### Total Processing Time
> _Average time per message (DB read + Telegram send). Lower is better._


![Total Processing Time Plot](plot_avg_total_processing_time.png)


#### Processing Time Consistency
> _Standard deviation of total processing time. Lower indicates more predictable performance._


![Processing Time Consistency Plot](plot_std_total_time.png)


#### HTTP Send Time
> _Average time for the Telegram API request only. Lower is better._


![HTTP Send Time Plot](plot_avg_http_send_time.png)


#### HTTP Time Consistency
> _Standard deviation of HTTP send time. Lower indicates less network variation._


![HTTP Time Consistency Plot](plot_std_http_time.png)


#### DB Read Time
> _Average time to read from PostgreSQL. Lower is better._


![DB Read Time Plot](plot_avg_db_read_time.png)


#### Response Size
> _Average size of the response from Telegram API. Smaller indicates less overhead._


![Response Size Plot](plot_avg_response_size.png)

## Resource Usage

#### CPU Usage
> _Average CPU percentage used by the Python process during the benchmark. Lower is better._


![CPU Usage Plot](plot_cpu_usage.png)


#### Memory Usage
> _Increase in Python process RAM from start to end of the benchmark. Lower is better._


![Memory Usage Plot](plot_memory_increase.png)


---

## Conclusion
- This benchmark shows how different Python libraries work when sending messages to Telegram
- The metrics focus on;
 -- resource utilization
 -- success rates
 -- throughput
 -- processing times
 -- consistency
- We should choose the library that matches our project's specific needs