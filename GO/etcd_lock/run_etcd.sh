#!/bin/bash
docker run -d --rm \
  --name etcd-server \
  -p 2379:2379 \
  -p 2380:2380 \
  --env ALLOW_NONE_AUTHENTICATION=yes \
  bitnami/etcd:3.5.18

echo "Etcd server started on localhost:2379"
