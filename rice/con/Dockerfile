# syntax=docker/dockerfile:1
FROM python:3.12-rc-bullseye
WORKDIR /app

# root installs

RUN addgroup --system app && adduser --system --group app
USER app

# CSI code
ENV FLASK_APP=mbg.csi:create_app
ENV FLASK_RUN_HOST=0.0.0.0

COPY . .
RUN pip install .

EXPOSE 5000
CMD ["flask", "run"]
