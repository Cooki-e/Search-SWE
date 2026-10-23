FROM docker.io/hanhainebula/search-swe-base:gpu-cu13.0-py3.12-1.0.0

RUN useradd --create-home --uid 10001 --user-group submission

COPY . /tests/

RUN chmod 700 /tests /tests/data /tests/test.sh
