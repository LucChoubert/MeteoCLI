IMAGE        := lucchoubert/meteocli
TAG          := $(shell git log -1 --pretty=%h)
DEPLOYMENT   := deployment/meteocli

all: build push

build:
	docker build -t $(IMAGE):$(TAG) .
	docker tag $(IMAGE):$(TAG) $(IMAGE):latest
 
push:
	docker push ${IMAGE}

deploy:
	kubectl rollout restart ${DEPLOYMENT}

clean:
	docker image rm ${IMAGE}:${TAG}
	docker image rm ${IMAGE}:latest

clean_all:
	docker image prune -a

login:
	docker log -u ${DOCKER_USER} -p ${DOCKER_PASS}