# MeiseCSI
MeiseBG Crop Source Investigations platform

## Reproducible Infrastructure as Code

You can install pulumi with the package manager of your OS
 - MacOS: `brew install pulumi/tap/pulumi`
 - Windows: `choco install pulumi`
 - Linux: `curl -fsSL https://get.pulumi.com | sh`

### Starting up

    mkdir rice
    pulumi new # e.g. choose aws-python
    python3 -m venv C:\Users\$USERNAME\repos\MeiseCSI\rice\venv
    C:\Users\$USERNAME\repos\MeiseCSI\rice\venv\Scripts\python -m pip \
      install --upgrade pip setuptools wheel
    C:\Users\$USERNAME\repos\MeiseCSI\rice\venv\Scripts\python -m pip \
      install -r requirements.txt
    cd rice
    pulumi up

### Create environment for secrets

    pulumi env init mcsi/dev
    
### Build container

    docker build -t mcsi -f rice/con/Dockerfile .
    docker run -v /c/Users/$USERNAME/repos/MeiseCSI:/app -p 5000:5000 -it mcsi /bin/bash

