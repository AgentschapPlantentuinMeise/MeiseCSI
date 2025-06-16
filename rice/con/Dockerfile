# syntax=docker/dockerfile:1
# Build from git root with following command:
# docker build -t mcsi -f rice/con/Dockerfile .
# Other option using build-context
# docker build -t mcsi:latest --build-context projectroot=. rice/con
FROM python:3.12-rc-bullseye

# root installs

RUN addgroup --system app && adduser --system --group app
USER app
WORKDIR /app

# CSI code
ENV TZ="Europe/Brussels"
ENV PATH=/home/app/.local/bin/:$PATH
ENV FLASK_APP=mbg.csi:app
ENV FLASK_RUN_HOST=0.0.0.0

#COPY --from=projectroot . .
COPY --chown=app:app . .
RUN pip install .[fullstack]

WORKDIR /app/src
EXPOSE 5000
CMD ["flask", "run"]
