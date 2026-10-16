FROM docker.io/hanhainebula/search-swe-base:cpu-py3.12-1.0.0

RUN useradd --create-home --uid 10001 --user-group submission

RUN mkdir -p /work /task/data /logs/verifier \
    && chmod 755 /work /logs \
    && chmod 700 /logs/verifier

COPY launch.py /runner/launch.py
RUN chmod 555 /runner && chmod 444 /runner/launch.py

COPY . /tests/

RUN chmod 700 /tests \
    && chmod 700 /tests/test.sh
