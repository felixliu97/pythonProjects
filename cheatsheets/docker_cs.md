# Docker Cheatsheet

``` bash
#!/bin/bash
```

## 1. CONTAINER MANAGEMENT

``` bash
# List running containers
docker ps

# List all containers (running and stopped)
docker ps -a

# Start a container from an image
# -d: detach mode (run in background)
# -p: publish port (host_port:container_port)
# --name: assign a name
docker run -d -p 8080:80 --name my-container nginx

# Stop a running container
docker stop <container_id_or_name>

# Start a stopped container
docker start <container_id_or_name>

# Restart a container
docker restart <container_id_or_name>

# Kill a running container (immediate stop)
docker kill <container_id_or_name>

# Remove a stopped container
docker rm <container_id_or_name>

# Force remove a running container
docker rm -f <container_id_or_name>

# View container logs
# -f: follow log output
docker logs -f <container_id_or_name>

# Inspect container details (JSON format)
docker inspect <container_id_or_name>

# Execute a command inside a running container
# -it: interactive terminal
docker exec -it <container_id_or_name> /bin/bash
# or for alpine images:
docker exec -it <container_id_or_name> sh

# Copy files between host and container
# From container to host:
docker cp <container_id_or_name>:/path/to/file ./local/path
# From host to container:
docker cp ./local/file <container_id_or_name>:/path/to/destination
```

## 2. IMAGE MANAGEMENT

``` bash
# List local images
docker images

# Pull an image from a registry (e.g., Docker Hub)
docker pull <image_name>:<tag>

# Build an image from a Dockerfile in the current directory
# -t: tag the image
docker build -t <image_name>:<tag> .

# Remove an image
docker rmi <image_id_or_name>

# Remove all unused images (dangling)
docker image prune

# Tag an image
docker tag <source_image>:<tag> <target_image>:<tag>

# Push an image to a registry
docker push <image_name>:<tag>

# Save an image to a tar archive
docker save -o <path_for_generated_tar_file> <image_name>

# Load an image from a tar archive
docker load -i <path_to_image_tar_file>
```

## 3. VOLUMES & NETWORKS

``` bash
# List volumes
docker volume ls

# Create a volume
docker volume create <volume_name>

# Remove a volume
docker volume rm <volume_name>

# Remove all unused volumes
docker volume prune

# List networks
docker network ls

# Create a network
docker network create <network_name>

# Connect a container to a network
docker network connect <network_name> <container_name>

# Disconnect a container from a network
docker network disconnect <network_name> <container_name>
```

## 4. DOCKER COMPOSE

``` bash
# Start services defined in docker-compose.yml
# -d: detach mode
docker-compose up -d

# Stop and remove containers, networks, images, and volumes
docker-compose down

# View logs for services
docker-compose logs -f

# List containers for the project
docker-compose ps

# Build or rebuild services
docker-compose build

# Restart services
docker-compose restart
```

## 5. CLEANUP & ONE-LINERS (USE WITH CAUTION)

``` bash
# Stop ALL running containers
docker stop $(docker ps -q)

# Remove ALL stopped containers
docker rm $(docker ps -a -q)

# Remove ALL images
docker rmi $(docker images -q)

# System Prune: Remove all unused containers, networks, images (both dangling and unreferenced), and optionally, volumes.
# -a: Remove all unused images not just dangling ones
# --volumes: Prune volumes
docker system prune -a --volumes
```

## 6. STATS & INFO

``` bash
# Display a live stream of container(s) resource usage statistics
docker stats

# Show docker disk usage
docker system df

# Show system wide information
docker info
```

