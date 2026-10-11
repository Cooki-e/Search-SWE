FROM docker.io/hanhainebula/search-swe-base:cpu-py3.12-1.0.0

COPY install-rust.sh /tmp/install-rust.sh
RUN sh /tmp/install-rust.sh && rm /tmp/install-rust.sh
ENV PATH="/opt/rust/bin:${PATH}" CARGO_HOME=/opt/cargo \
    JAVA_TOOL_OPTIONS="-Xmx10g -XX:ActiveProcessorCount=4"
COPY toolchain/ /seed/
RUN cd /seed && cargo fetch --locked && cargo build --release --locked --offline \
    && rm -rf /seed/target \
    && useradd --create-home --uid 10001 --user-group submission
COPY . /tests/
RUN chmod 700 /tests /tests/data /tests/test.sh
