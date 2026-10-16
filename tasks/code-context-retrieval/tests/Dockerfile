FROM docker.io/hanhainebula/search-swe-base:cpu-py3.12-1.0.0

RUN useradd --create-home --uid 10001 --user-group submission \
    && mkdir -p /app /work /task/data /logs/verifier \
    && chmod 755 /app /work /logs \
    && chmod 700 /logs/verifier

COPY . /tests/
RUN chown -R root:root /tests && chmod -R go-rwx /tests \
    && chmod 700 /tests/test.sh
