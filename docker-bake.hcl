variable "platforms" {
  default = ["linux/amd64", "linux/arm64", "linux/arm/v6", "linux/arm/v7"]
}

variable "dockerfile" {
  default = "Dockerfile"
}

group "default" {
  targets = ["sickchill-final", "sickchill-wheels"]
}

target "sickchill-final" {
  platforms  = platforms
  target    = "sickchill-final"
  dockerfile = dockerfile
  tags       = ["docker.io/sickchill/sickchill"]
  cache-from = ["type=local,src=/tmp/.buildx-cache"]
  cache-to   = ["type=local,dest=/tmp/.buildx-cache-new"]
}

target "sickchill-wheels" {
  platforms = platforms
  dockerfile = dockerfile
  target = "sickchill-wheels"
  cache-from = ["type=local,src=/tmp/.buildx-cache"]
  output = ["type=local,dest=/tmp/sickchill-wheels"]
}
