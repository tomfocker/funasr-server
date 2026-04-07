# Docker API Service 使用说明

## 功能

这个仓库当前只提供 `Fun-ASR-Nano` 的后端服务能力：

- 健康检查：`GET /healthz`
- 服务摘要：`GET /`
- OpenAPI 文档：`GET /docs`
- OpenAI 风格接口：`POST /v1/audio/transcriptions`
- 简洁别名接口：`POST /api/transcriptions`

前端能力已经拆分到独立仓库：

- `video-cuter`：纯浏览器视频裁剪
- 完整版整合仓库：前端 + 本服务的联动发布

## 快速启动

```bash
docker compose up --build
```

启动后访问：

- 服务摘要: `http://localhost:8000/`
- OpenAPI: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/healthz`

## 模型策略

默认按下面顺序找模型：

1. 如果 `CW_MODEL_DIR` 已经有完整模型文件，直接使用
2. 如果 `/data/models/Fun-ASR-Nano/Fun-ASR-Nano-GGUF/` 下已有模型，直接使用
3. 如果没有模型，再下载 `Fun-ASR-Nano-GGUF.zip` 并解压到 `/data/models/...`

主镜像默认不内置模型，这样镜像更轻，模型也可以复用宿主机挂载目录。

## API 示例

### 纯文本

```bash
curl -F file=@sample.wav \
     -F response_format=text \
     http://localhost:8000/v1/audio/transcriptions
```

### 详细 JSON

```bash
curl -F file=@sample.wav \
     -F response_format=verbose_json \
     http://localhost:8000/v1/audio/transcriptions
```

返回字段：

- `text`
- `segments`
- `subtitle_segments`
- `srt`
- `model`
- `timings`

### SRT

```bash
curl -F file=@sample.wav \
     -F response_format=srt \
     http://localhost:8000/api/transcriptions
```

## 数据目录

`docker-compose.yml` 默认挂载：

```bash
./.docker-data:/data
```

其中会保存：

- `/data/models/...`：自动下载或持久化保存的模型文件
- `/data/cache/...`：下载缓存
- `/data/uploads/...`：运行时临时上传目录

如果你已经手动下载好了模型，推荐额外挂载到：

```bash
./Fun-ASR-Nano-GGUF:/app/Fun-ASR-Nano-GGUF:ro
```

也可以通过环境变量指定：

```bash
CW_MODEL_DIR=/app/Fun-ASR-Nano-GGUF
```

## 常用环境变量

- `CW_PORT`：服务端口，默认 `8000`
- `CW_DATA_DIR`：数据目录，默认 `/data`
- `CW_MODEL_DIR`：自定义模型目录
- `CW_AUTO_DOWNLOAD_MODEL`：是否自动下载模型，默认 `1`
- `CW_VULKAN_ENABLE`：是否启用 Vulkan，默认 `0`
- `CW_DML_ENABLE`：是否启用 DML，默认 `0`
- `CW_N_THREADS`：自定义推理线程数

## 给其他 Docker 应用调用

在同一个 `docker compose` 网络里，其他服务可以直接请求：

```bash
http://capswriter-funasr:8000/v1/audio/transcriptions
```

如果是在宿主机调用，则使用：

```bash
http://localhost:8000
```
