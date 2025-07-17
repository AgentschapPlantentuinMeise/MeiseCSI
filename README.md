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

### Update container on live server

    sudo su - -l mcsi
    docker stop mcsiserver
    docker remove mcsiserver
    cd repos/MeiseCSI/
    git pull origin
    docker build --build-arg USER_ID=$(id -u) \
    --build-arg GROUP_ID=$(id -g) \
    -t localhost/webapp -f rice/con/Dockerfile .
    docker run -d -p 5000:5000 -e BADMIN_INIT='ton~1873' -v
    ~/instance:/app/src/instance --name mcsiserver localhost/webapp
    docker exec -it mcsiserver /bin/bash
    mkdir migrations
    flask db init

If you need to remove previous migrations

    import sqlite3
    conn = sqlite3.connect('instance/mcsi.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(cursor.fetchall())
    cursor.execute("DELETE FROM alembic_version;")
    conn.commit()
    conn.close()

