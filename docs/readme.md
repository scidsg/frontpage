# Frontpage Documentation

## Docker

**Step 1:** Install and run Docker

Docker comes in many flavors. You can download the desktop application from [Docker's website](https://www.docker.com/products/docker-desktop/).

**Step 2:** Run Frontpage

From the app's root directory:

`docker build -t frontpage .`
`docker run -d -p 80:80 --name frontpage-container frontpage`
