FROM docker.io/hanhainebula/search-swe-base:gpu-cu13.0-py3.12-1.0.0

ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

RUN useradd --create-home --uid 10001 --user-group submission

COPY . /tests/

RUN chmod 700 /tests \
    && chmod 700 /tests/test.sh /tests/data \
    && chmod 600 /tests/data/*
