#!/bin/bash
set -e

echo "1. Deploying etcd-dev..."
kubectl apply -f deploy_etcd.yaml

echo "2. Waiting for pod to be ready..."
kubectl wait --for=condition=Ready pod/etcd-dev --timeout=60s

echo "3. Starting port-forward (background)..."
# Kill any existing port-forward on 23799 just in case
pkill -f "kubectl port-forward pod/etcd-dev 23799:2379" || true
kubectl port-forward pod/etcd-dev 23799:2379 &
PF_PID=$!

# Give port-forward a moment to establish
sleep 2

echo "4. Running Go test..."
# Ensure we use the full path to go if it's not in PATH, or assume it's in PATH if running from Git Bash
if command -v go &> /dev/null; then
    GO_CMD="go"
elif [ -f "/c/Program Files/Go/bin/go.exe" ]; then
    GO_CMD="/c/Program Files/Go/bin/go.exe"
else
    echo "Error: Go not found"
    kill $PF_PID
    exit 1
fi

"$GO_CMD" run main.go -endpoint=localhost:23799

echo "5. Cleanup..."
kill $PF_PID
echo "Done."
