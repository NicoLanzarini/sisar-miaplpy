FROM mambaorg/micromamba:1.5.8

USER root

RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    gcc \
    g++ \
    make \
    libfftw3-dev \
    && rm -rf /var/lib/apt/lists/*

USER $MAMBA_USER

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml

RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ENV PATH="/opt/conda/bin:$PATH"
ENV ISCE_HOME="/opt/conda/lib/python3.10/site-packages/isce"

WORKDIR /workspace

COPY --chown=$MAMBA_USER:$MAMBA_USER scripts/ /workspace/scripts/
COPY --chown=$MAMBA_USER:$MAMBA_USER entrypoint.sh /workspace/entrypoint.sh

RUN chmod +x /workspace/entrypoint.sh

CMD ["bash", "/workspace/entrypoint.sh"]
