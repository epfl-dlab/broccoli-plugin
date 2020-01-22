# Installation guide
The following guide has been tested with Ubuntu 19.10

## install Docker
follow official instructions
https://docs.docker.com/install/

e.g. for Ubuntu
https://docs.docker.com/install/linux/docker-ce/ubuntu/

While the official guide contains instruction for the installation of docker-ce,
the remaining part of this document has been tested against an installation of docker.io

You can install docker.io with:
```
sudo apt update
sudo apt remove docker docker-engine docker.io
sudo apt install docker.io

sudo systemctl start docker
sudo systemctl enable docker
```

## install node.js
The official website hosts installers for most platforms: https://nodejs.org/en/
Ubuntu download packages can be found here: https://github.com/nodesource/distributions/blob/master/README.md##debinstall

The following has been tested with node version v10.18.1 and npm version 6.13.4

## create third-party ressources
Our code relies on the Azure Text Translation API.
Since we can't openly publish our API keys, you have to create the corresponding Azure ressources yourself.
Please set up an Azure Text Translation endpoint and generate a custom key.
The key needs to be placed in:

```
broccoli_api_neural/config/azure_api_key.py
key = "ToDo"
```

Similarly we use Firebase as a storage backend.
Please set up a Firebase project and enable email authentication.
Then visit https://console.firebase.google.com/project/broccoli-1537781957741/overview
select firebase console, add app, web and copy the credentials to:

```
broccoli_plugin/src/config.ts
export var config = {ToDo}
```

## build backend and frontend

The backend is a docker image and can be built with:
```
cd broccoli_api_neural/
docker build -f Dockerfile_deps -t broccoli_deps . 
docker build -f Dockerfile_downloads -t broccoli_downloads .
docker build -f Dockerfile_api -t broccoli_api .
```

The browser plugin is built with parcel and uses npm as a package manager:
```
cd broccoli_plugin
npm install -d
sudo npm install -g parcel-bundler
parcel build src/manifest.json

```
## install and run the plugin the plugin in Firefox or Chrome
ToDo: embed video


## user Docker to start backend
once you've logged in, you'll be asked to connect to the backend.
Before doing this, start the docker container with:
```
docker run -p 127.0.0.1:5000:5000 broccoli_api
```