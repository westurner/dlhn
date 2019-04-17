
FROM alpine

RUN apk add --update \
    python3 \
    py3-pip \
  && pip3 install virtualenv \
  && rm -rf /var/cache/apk/*
#    python-dev \
#    build-base \

WORKDIR /app
#ONBUILD RUN python3 -m venv /app
RUN virtualenv /app && mkdir /app/src
COPY . /app/src/dlhn
#RUN --mount=type=cache,target=/root/.cache/pip /app/bin/pip install -e /app/src/dlhn
RUN /app/bin/pip install -e /app/src/dlhn
RUN mkdir /app/src/hnlog

VOLUME /app/src
VOLUME /app/src/hnlog

CMD ["/app/bin/dlhn", "--help"]
