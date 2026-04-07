FROM python:3.11-slim AS llama-builder

ARG LLAMA_CPP_TAG=b7798

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src

RUN git clone --depth 1 --branch ${LLAMA_CPP_TAG} https://github.com/ggml-org/llama.cpp.git

WORKDIR /src/llama.cpp

RUN cmake -S . -B build \
    -DBUILD_SHARED_LIBS=ON \
    -DGGML_VULKAN=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_SERVER=OFF \
 && cmake --build build --config Release -j"$(nproc)" \
 && mkdir -p /out \
 && find build -type f \( -name 'libllama.so*' -o -name 'libggml*.so*' \) -exec cp -av {} /out/ \;


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CW_DATA_DIR=/data \
    CW_PORT=8000 \
    CW_VULKAN_ENABLE=0 \
    CW_DML_ENABLE=0 \
    LD_LIBRARY_PATH=/app/util/llama/bin:/app/util/fun_asr_gguf/inference/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-docker.txt /app/requirements-docker.txt
RUN pip install --no-cache-dir -r /app/requirements-docker.txt

COPY . /app

COPY --from=llama-builder /out/ /app/util/llama/bin/
RUN mkdir -p /app/util/fun_asr_gguf/inference/bin \
 && cp -av /app/util/llama/bin/* /app/util/fun_asr_gguf/inference/bin/ \
 && chmod +x /app/scripts/start_api_service.sh

EXPOSE 8000
VOLUME ["/data"]

CMD ["./scripts/start_api_service.sh"]
