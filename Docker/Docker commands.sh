# stop all the containers
docker stop $(docker ps -a -q)

# docker rm $(docker ps -a -q)
docker rm $(docker ps -a -q)

# copy folder from container to local
docker cp <container>:/usr/local/lib/python3.9/site-packages/. ./kafka