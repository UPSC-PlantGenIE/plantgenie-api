ARG DEBIAN_VERSION=bookworm
ARG SAMTOOLS_VERSION=1.23
ARG BLAST_VERSION=2.17.0
ARG DIAMOND_VERSION=2.1.23

FROM debian:${DEBIAN_VERSION} AS tool-builder

ARG DIAMOND_VERSION
ARG SAMTOOLS_VERSION
ARG BLAST_VERSION
ARG BUILD_NCPU=1
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    wget \
    git \
    cmake \
    libzstd-dev \
    libsqlite3-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libcurl4-openssl-dev \
    libncurses5-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN wget https://github.com/samtools/samtools/releases/download/${SAMTOOLS_VERSION}/samtools-${SAMTOOLS_VERSION}.tar.bz2
RUN tar -xf samtools-${SAMTOOLS_VERSION}.tar.bz2
WORKDIR /build/samtools-${SAMTOOLS_VERSION}
RUN ./configure && \
    make -j${BUILD_NCPU}

WORKDIR /build/samtools-${SAMTOOLS_VERSION}/htslib-${SAMTOOLS_VERSION}
RUN ./configure && \
    make -j${BUILD_NCPU}

WORKDIR /build/samtools-${SAMTOOLS_VERSION}
RUN strip samtools htslib-${SAMTOOLS_VERSION}/tabix htslib-${SAMTOOLS_VERSION}/bgzip

WORKDIR /build
RUN git clone https://github.com/gpertea/gffread.git /build/gffread \
    && cd /build/gffread \
    && make release
RUN strip /build/gffread/gffread

WORKDIR /build
RUN wget "https://github.com/bbuchfink/diamond/archive/refs/tags/v${DIAMOND_VERSION}.tar.gz" && \
    tar xvf "v${DIAMOND_VERSION}.tar.gz"
WORKDIR /build/diamond-${DIAMOND_VERSION}/bin
RUN cmake .. && \
    make -j ${BUILD_NCPU}
RUN strip /build/diamond-${DIAMOND_VERSION}/bin/diamond

RUN case "${TARGETARCH}" in \
    amd64) BLAST_ARCH=x64-linux ;; \
    arm64) BLAST_ARCH=aarch64-linux ;; \
    *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    wget -q "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/ncbi-blast-${BLAST_VERSION}+-${BLAST_ARCH}.tar.gz" \
    -O /build/blast.tar.gz && \
    cd /build && \
    tar -xzf blast.tar.gz && \
    mkdir /blast-bin && \
    cp "ncbi-blast-${BLAST_VERSION}+/bin/blastn" \
    "ncbi-blast-${BLAST_VERSION}+/bin/blastp" \
    "ncbi-blast-${BLAST_VERSION}+/bin/blastx" \
    "ncbi-blast-${BLAST_VERSION}+/bin/makeblastdb" \
    /blast-bin/ && \
    strip /blast-bin/blastn \
    /blast-bin/blastp \
    /blast-bin/blastx \
    /blast-bin/makeblastdb

FROM python:3.13-slim-${DEBIAN_VERSION} AS py-builder

RUN apt-get update && \
    apt-get install -y \
        gcc \
        zlib1g-dev \
        && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml /app/
COPY uv.lock /app/

COPY packages/knowledge-builder/pyproject.toml /app/packages/knowledge-builder/pyproject.toml
COPY packages/knowledge-builder/src/knowledge_builder /app/packages/knowledge-builder/src/knowledge_builder
COPY packages/shared/pyproject.toml /app/packages/shared/pyproject.toml
COPY packages/shared/src/shared /app/packages/shared/src/shared
COPY packages/task-queue/pyproject.toml /app/packages/task-queue/pyproject.toml
COPY packages/task-queue/src/task_queue /app/packages/task-queue/src/task_queue
COPY packages/go-enrich/pyproject.toml /app/packages/go-enrich/pyproject.toml
COPY packages/go-enrich/src/go_enrich /app/packages/go-enrich/src/go_enrich
COPY packages/snakemake-storage-plugin-swift/pyproject.toml /app/packages/snakemake-storage-plugin-swift/pyproject.toml
COPY packages/snakemake-storage-plugin-swift/src/snakemake_storage_plugin_swift /app/packages/snakemake-storage-plugin-swift/src/snakemake_storage_plugin_swift

RUN touch /app/packages/shared/README.md
RUN touch /app/packages/knowledge-builder/README.md
RUN touch /app/packages/task-queue/README.md
RUN touch /app/packages/go-enrich/README.md

WORKDIR /app/packages/knowledge-builder
RUN uv sync --locked

FROM python:3.13-slim-${DEBIAN_VERSION}

ARG SAMTOOLS_VERSION
ARG DIAMOND_VERSION

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libbz2-1.0 \
    zlib1g \
    libcurl4 \
    liblzma5 \
    libncursesw6 \
    libsqlite3-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=tool-builder /build/samtools-${SAMTOOLS_VERSION}/samtools /usr/local/bin/samtools
COPY --from=tool-builder /build/samtools-${SAMTOOLS_VERSION}/htslib-${SAMTOOLS_VERSION}/tabix /usr/local/bin/tabix
COPY --from=tool-builder /build/samtools-${SAMTOOLS_VERSION}/htslib-${SAMTOOLS_VERSION}/bgzip /usr/local/bin/bgzip
COPY --from=tool-builder /build/gffread/gffread /usr/local/bin/gffread
COPY --from=tool-builder /blast-bin/blastn /usr/local/bin/blastn
COPY --from=tool-builder /blast-bin/blastp /usr/local/bin/blastp
COPY --from=tool-builder /blast-bin/blastx /usr/local/bin/blastx
COPY --from=tool-builder /blast-bin/makeblastdb /usr/local/bin/makeblastdb
COPY --from=tool-builder /build/diamond-${DIAMOND_VERSION}/bin/diamond /usr/local/bin/diamond

RUN useradd --create-home appuser

COPY --from=py-builder /app/.venv /app/.venv
COPY --from=py-builder /app/packages/knowledge-builder/src/knowledge_builder /app/packages/knowledge-builder/src/knowledge_builder
COPY --from=py-builder /app/packages/shared/src /app/packages/shared/src
COPY --from=py-builder /app/packages/snakemake-storage-plugin-swift/src /app/packages/snakemake-storage-plugin-swift/src
COPY packages/knowledge-builder/knowledge.yaml /app/packages/knowledge-builder/knowledge.yaml
COPY packages/knowledge-builder/Snakefile /app/packages/knowledge-builder/Snakefile
COPY packages/knowledge-builder/config.yaml /app/packages/knowledge-builder/config.yaml

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/packages/knowledge-builder
RUN chown -R appuser /app/packages/knowledge-builder

USER appuser

ENTRYPOINT ["kb"]
