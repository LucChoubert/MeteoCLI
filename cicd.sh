#! /bin/sh

docker image rm meteocli:latest
docker image rm lucchoubert/meteocli:latest
docker build -t meteocli:latest .
docker image tag meteocli:latest lucchoubert/meteocli:latest
docker push lucchoubert/meteocli
kubectl apply -f configKube
