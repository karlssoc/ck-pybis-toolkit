FROM python:3.11-slim

WORKDIR /app

COPY setup.py .
COPY pybis_scripts.py .
COPY pybis_common.py .
COPY README.md .

RUN pip install --no-cache-dir .

RUN mkdir -p /root/.openbis

ENV PATH="/root/.local/bin:$PATH"

ENTRYPOINT ["pybis"]
CMD ["--help"]