# K8S Cheatsheet

``` bash
#!/bin/bash
```

## KUBERNETES (K8S) CHEATSHEET

## 1. CLUSTER INFO & CONTEXT

``` bash
# Display cluster info
kubectl cluster-info

# List all nodes
kubectl get nodes

# Display current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context_name>

# Set default namespace for current context
kubectl config set-context --current --namespace=<namespace>
```

## 2. POD MANAGEMENT

``` bash
# List pods in current namespace
kubectl get pods

# List pods in all namespaces
kubectl get pods --all-namespaces

# List pods with more details (IP, Node)
kubectl get pods -o wide

# Describe a pod (detailed info, events)
kubectl describe pod <pod_name>

# Create a pod from a YAML file
kubectl apply -f pod.yaml

# Delete a pod
kubectl delete pod <pod_name>

# Force delete a pod (now)
kubectl delete pod <pod_name> --grace-period=0 --force

# Get pod logs
kubectl logs <pod_name>

# Get pod logs (follow)
kubectl logs -f <pod_name>

# Get logs from a specific container in a pod
kubectl logs <pod_name> -c <container_name>

# Execute command in a running pod
kubectl exec -it <pod_name> -- /bin/bash
```

## 3. DEPLOYMENTS & SCALING

``` bash
# List deployments
kubectl get deployments

# Create a deployment
kubectl create deployment <deployment_name> --image=<image_name>

# Scale a deployment
kubectl scale deployment <deployment_name> --replicas=3

# Update image in deployment
kubectl set image deployment/<deployment_name> <container_name>=<new_image>

# Check rollout status
kubectl rollout status deployment/<deployment_name>

# Undo a rollout (rollback)
kubectl rollout undo deployment/<deployment_name>

# History of rollouts
kubectl rollout history deployment/<deployment_name>
```

## 4. SERVICES & NETWORKING

``` bash
# List services
kubectl get services

# Expose a deployment as a service (ClusterIP)
kubectl expose deployment <deployment_name> --port=80 --target-port=8080

# Expose as NodePort
kubectl expose deployment <deployment_name> --type=NodePort --port=80

# Expose as LoadBalancer
kubectl expose deployment <deployment_name> --type=LoadBalancer --port=80

# Port forward local port to pod port
kubectl port-forward <pod_name> 8080:80
```

## 5. CONFIGMAPS & SECRETS

``` bash
# List ConfigMaps
kubectl get configmaps

# Create ConfigMap from file
kubectl create configmap <name> --from-file=<path>

# List Secrets
kubectl get secrets

# Create Secret from literal
kubectl create secret generic <name> --from-literal=username=admin --from-literal=password=secret

# Decode a secret (linux)
kubectl get secret <secret_name> -o jsonpath="{.data.password}" | base64 --decode
```

## 6. DEBUGGING & DIAGNOSTICS

``` bash
# Get events in the namespace
kubectl get events --sort-by='.lastTimestamp'

# Top pods (CPU/Memory usage) - requires metrics-server
kubectl top pods

# Top nodes
kubectl top nodes

# Run a temporary busybox pod for debugging
kubectl run -it --rm debug --image=busybox --restart=Never -- sh
```

## 7. USEFUL ALIASES

``` bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgd='kubectl get deployments'
alias kgs='kubectl get services'
alias kdp='kubectl describe pod'
```

