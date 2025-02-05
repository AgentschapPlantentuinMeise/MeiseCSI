# syntax=docker/dockerfile:1
FROM python:3.12-rc-bullseye
WORKDIR /mbg
ENV FLASK_APP=mbg.csi:create_app
ENV FLASK_RUN_HOST=0.0.0.0
RUN apt-get update && apt-get install -y cmake
RUN apt install -y -V ca-certificates lsb-release wget
RUN wget https://apache.jfrog.io/artifactory/arrow/$(lsb_release --id --short \
| tr 'A-Z' 'a-z')/apache-arrow-apt-source-latest-$(lsb_release \
--codename --short).deb
RUN apt install -y -V \
./apache-arrow-apt-source-latest-$(lsb_release --codename --short).deb
RUN apt update
RUN apt install -y -V libarrow-dev
RUN apt install -y -V libarrow-flight-dev
# https://arrow.apache.org/docs/developers/guide/step_by_step/building.html
# https://arrow.apache.org/docs/developers/python.html#build-pyarrow
RUN PYARROW_WITH_FLIGHT=1 pip install --no-cache-dir pyarrow
# scikit-learn
RUN apt-get install -y build-essential gfortran libopenblas-dev
# Openstreetmaps
RUN apt-get install -y libxml2-dev libxslt-dev python3-dev
RUN pip install cython==0.29.34 #TODO check when can be done with newer version
RUN pip install git+https://github.com/lxml/lxml
# omspythontools in requirements

# CSI code
# build command needs to be executed from git root
COPY . .
RUN pip install .

EXPOSE 5000
CMD ["flask", "run"]
