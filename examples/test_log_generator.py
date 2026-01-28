"""Simple test log generator for testing the agent."""

import time
import random
from datetime import datetime


def generate_test_logs(log_file="/tmp/test-app.log", interval=5):
    """
    Generate test log entries with errors.

    Args:
        log_file: Path to log file
        interval: Seconds between log entries
    """
    error_patterns = [
        "ERROR: Out of memory - heap exhausted",
        "ERROR: Disk full - cannot write to /tmp",
        "FATAL: Connection refused to database on port 5432",
        "Exception: NullPointerException at line 42",
        "ERROR: Too many open files",
        "WARNING: High CPU usage detected - 95%",
    ]

    print(f"Generating test logs to {log_file}")
    print(f"Writing errors every {interval} seconds...")
    print("Press Ctrl+C to stop\n")

    try:
        with open(log_file, "a") as f:
            count = 0
            while True:
                count += 1
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Write normal log
                f.write(f"[{timestamp}] INFO: Application running normally (count: {count})\n")
                f.flush()

                # Randomly write an error
                if count % 3 == 0:
                    error = random.choice(error_patterns)
                    f.write(f"[{timestamp}] {error}\n")
                    f.flush()
                    print(f"[{timestamp}] Generated error: {error}")

                time.sleep(interval)

    except KeyboardInterrupt:
        print("\nStopped generating logs")


if __name__ == "__main__":
    import sys

    log_file = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test-app.log"
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    generate_test_logs(log_file, interval)
