# MeiseCSI
MeiseBG Crop Source Investigations platform

## Reproducible Infrastructure as Code

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

