ACCOUNT=omhq
IMAGE=llmt-workspace
IMAGE_TAG=0.0.4

CURRENT_DIR=$(shell pwd)


.PHONY: clean
clean:
	docker compose rm -vf

.PHONY: run
run:
	docker compose run $(IMAGE); docker compose down --remove-orphans

.PHONY: shell
shell:
	docker compose run -it --entrypoint=/bin/bash $(IMAGE); docker compose down --remove-orphans

.PHONY: all
all: build-image tag-image push-image

.PHONY: build-image
build-image:
	DOCKER_BUILDKIT=1 docker build -t $(IMAGE):$(IMAGE_TAG) -f $(CURRENT_DIR)/Dockerfile .

.PHONY: tag-image
tag-image:
	docker tag $(IMAGE):$(IMAGE_TAG) $(ACCOUNT)/$(IMAGE):$(IMAGE_TAG)

.PHONY: push-image
push-image:
	docker push $(ACCOUNT)/$(IMAGE):$(IMAGE_TAG)
