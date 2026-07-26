FROM ghcr.io/astral-sh/uv:latest AS uv

FROM apache/airflow:3.3.0-python3.12

# Installe uv dans l'image Airflow
COPY --from=uv /uv /uvx /bin/

# Prépare le projet
WORKDIR /opt/airflow/checkit_ai
COPY pyproject.toml uv.lock ./

# Exporte le lock puis installe dans le Python déjà fourni par Airflow
RUN uv export \
        --frozen \
        --no-dev \
        --no-emit-project \
        --format requirements.txt \
        --output-file /tmp/checkit-requirements.txt \
    && uv pip install \
        --python "$(which python)" \
        --requirement /tmp/checkit-requirements.txt \
    && uv pip check \
        --python "$(which python)" \
    && rm -f /tmp/checkit-requirements.txt