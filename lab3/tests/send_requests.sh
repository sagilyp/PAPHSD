#!/bin/bash

sleep 10

URL="http://nginx:80/api/login"
JSON_FILE="/app/users.json"
LOG_FILE="/app/test_log.txt"

total_requests=0
successful_requests=0
failed_requests=0
total_time=0

if [[ -f "$JSON_FILE" ]]; then
  cat $JSON_FILE | jq -c '.[]' | head -n 1000 | parallel -j 1000 curl -X POST $URL \
    -H "Content-Type: application/json" \
    -d {} \
    --max-time 255 \
    --connect-timeout 255 \
    --write-out "%{http_code} %{time_total}\n" \
    --silent \
    --output /dev/null 2>&1 | while read -r line; do
          echo "Line from curl: $line"
      http_code=$(echo $line | awk '{print $1}')
      response_time=$(echo $line | awk '{print $2}')
      total_requests=$((total_requests + 1))
      total_time=$(echo "$total_time + $response_time" | bc)
      if [[ "$http_code" -eq 200 ]]; then
        successful_requests=$((successful_requests + 1))
      else
        failed_requests=$((failed_requests + 1))
      fi
  done

  if [[ "$total_requests" -gt 0 ]]; then
    average_time=$(echo "scale=3; $total_time / $total_requests" | bc)
  else
    average_time=0
  fi

  echo "Total Requests: $total_requests" > $LOG_FILE
  echo "Successful Requests: $successful_requests" >> $LOG_FILE
  echo "Failed Requests: $failed_requests" >> $LOG_FILE
  echo "Average Response Time: $average_time seconds" >> $LOG_FILE
else
  echo "Файл с пользователями не найден!"
fi
