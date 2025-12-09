#!/bin/bash

# Cleanup on exit
trap 'docker stop etcd-test-server; rm -f worker.exe' EXIT

# Ensure etcd is running
docker rm -f etcd-test-server || true
docker run -d --rm \
  --name etcd-test-server \
  -p 12379:2379 \
  --env ALLOW_NONE_AUTHENTICATION=yes \
  quay.io/coreos/etcd:v3.5.0 \
  //usr/local/bin/etcd \
  --advertise-client-urls http://127.0.0.1:2379 \
  --listen-client-urls http://0.0.0.0:2379

echo "Waiting for etcd to be ready..."
sleep 3

# Build the worker binary first
echo "Building worker binary..."
go build -o worker.exe main.go
if [ $? -ne 0 ]; then
    echo "Build failed"
    exit 1
fi



# Clear previous log
if [ -f combined.log ]; then
    rm combined.log
fi

{
    echo "$(date "+%Y/%m/%d %H:%M:%S") Starting Worker 1"
    ./worker.exe -name "Worker-1" -ttl 5 -endpoint "127.0.0.1:12379" &
    PID1=$!

    # Small delay to ensure Worker 1 likely gets there first
    sleep 2

    echo "$(date "+%Y/%m/%d %H:%M:%S") Starting Worker 2"
    ./worker.exe -name "Worker-2" -ttl 5 -endpoint "127.0.0.1:12379" &
    PID2=$!

    echo "$(date "+%Y/%m/%d %H:%M:%S") Starting Worker 3"
    ./worker.exe -name "Worker-3" -ttl 5 -endpoint "127.0.0.1:12379" &
    PID3=$!

    wait $PID1
    wait $PID2
    wait $PID3
} > combined.log 2>&1



echo "Combined Worker Output:"
cat combined.log


echo "Test finished."
