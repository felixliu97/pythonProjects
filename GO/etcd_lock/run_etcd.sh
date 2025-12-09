#!/bin/bash
docker run -d --rm \
  --name etcd-server \
  -p 2379:2379 \
  -p 2380:2380 \
  --env ALLOW_NONE_AUTHENTICATION=yes \
  quay.io/coreos/etcd:v3.5.0

echo "Etcd server started on localhost:2379"
