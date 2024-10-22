# Broccoli

This repository contains the source code for our Broccoli prototype.
Since the installation is complex (it requires you to set up API keys for the Azure Translation API and Firebase),
we are providing a demo video here:
![Broccoli Demo](demo.gif)

a high-res version can be found on YouTube:
https://www.youtube.com/watch?v=wg-5UqRaoNs&feature=youtu.be

# Code
This code is intended as a reference implementation and platform for further research.
As such we have included functionality that we consider useful but that has not been evaluated as a part of the current Broccoli publication.
For example, the plugin has an options menu where it is possible to enable additional user interactions. Instead of revealing the translation after an annotation is clicked, the prototype can also show a free-form text input where the user has to guess the translation. This is a template for setting up more complex user interactions that might improve word retention.
However, the current conception of Broccoli builds on passive, zero-effort learning. 
 
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
The plugin can now be installed in Firefox and Chrome (or any other browser that supports the WebExtension standard).
Since the plugin is not signed, it requires you to enable 'developer mode' in Chrome.
In Firefox, you can install the plugin by selecting to 'debug plugins' and then to install a temporary plugin.

## user Docker to start backend
once you've logged in, you'll be asked to connect to the backend.
Before doing this, start the docker container with:
```
docker run -p 127.0.0.1:5000:5000 broccoli_api
```
