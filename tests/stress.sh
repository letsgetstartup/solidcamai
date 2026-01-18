#!/bin/bash
URL="https://solidcam-f58bc.web.app/pair_init"
CONCURRENCY=100
TOTAL=1000

echo "🚀 Starting Shell Stress Test: $TOTAL requests, $CONCURRENCY at a time..."
start_time=$(date +%s)

seq $TOTAL | xargs -I {} -P $CONCURRENCY curl -s -o /dev/null -w "%{http_code}\n" -X POST "$URL" -d "{\"fingerprint\": \"stress-test-{}\"}" -H "Content-Type: application/json" > results.txt

end_time=$(date +%s)
duration=$((end_time - start_time))

echo "--- Results ---"
cat results.txt | sort | uniq -c
echo "Total Time: $duration seconds"
echo "Requests per second: $((TOTAL / duration))"
