# Fun-ASR Docker WebUI Design

## 背景

当前仓库的核心价值在于 `Fun-ASR-Nano` 离线识别能力，但现有交付形态主要面向 Windows 桌面端：

- 服务端入口默认带托盘和桌面 UI。
- 依赖集合偏向 Windows，例如 `onnxruntime-directml`。
- 现有网络接口是给桌面客户端使用的自定义 WebSocket 协议，不适合直接作为浏览器和容器间标准接口。

本次子项目的目标是基于上游识别核心，新增一个面向 Linux 容器的交付层，提供开箱即用的 Web 页面和标准 HTTP API。

## 目标

- 仅支持一个模型：`Fun-ASR-Nano-GGUF`。
- 提供 Docker 镜像与 `docker compose` 启动方式。
- 提供浏览器可用的 WebUI，用于上传音频或视频文件并查看转录结果。
- 提供适合其他容器调用的 HTTP 接口。
- 输出文本、时间戳明细和 SRT。
- 尽量复用上游 `util/fun_asr_gguf` 推理能力，避免重写识别逻辑。

## 非目标

- 不兼容上游全部模型。
- 不实现桌面端实时按键听写。
- 不保留托盘、全局快捷键、剪贴板输出等 Windows 桌面功能。
- 第一版不追求 GPU 容器支持，优先保证 Linux CPU 版可运行。

## 方案比较

### 方案 A：直接改造现有 `core_server.py`

优点：

- 复用最多。
- 可以保留原始 WebSocket 流式协议。

缺点：

- 现有入口和生命周期深度绑定托盘与桌面 UI。
- 现有协议不适合浏览器端直接使用。
- 改动会污染上游桌面服务端路径，回归风险高。

### 方案 B：新增独立容器服务层，复用推理引擎

优点：

- 与桌面版隔离，边界清晰。
- 可以提供面向浏览器和容器的标准 HTTP API。
- 更适合单独维护 Docker 依赖与入口。

缺点：

- 需要补一层服务代码、配置和前端页面。

### 方案 C：完全重写识别管线

优点：

- 技术栈最干净。

缺点：

- 与上游分叉过大。
- 工作量和风险都明显更高。

## 选型

采用方案 B。

理由：

- 用户需求核心是“把现有能力做成 Docker 服务”，而不是重构原项目。
- 独立服务层能避免破坏桌面版本入口，同时让 HTTP API、WebUI、镜像依赖更干净。
- 识别内核仍复用上游 `util/fun_asr_gguf`，尽量减少模型行为偏差。

## 架构设计

新增一个独立的 `capsweb` 服务层：

1. `FastAPI` 作为 HTTP 服务框架。
2. `FunAsrNanoTranscriber` 作为模型封装层，负责：
   - 按需初始化模型
   - 串行执行转录任务
   - 统一产出文本、时间戳和 SRT
3. `WebUI` 使用服务端模板输出单页上传面板。
4. Docker 入口脚本负责：
   - 安装或校验 Linux 运行依赖
   - 自动下载 `Fun-ASR-Nano-GGUF` 模型
   - 自动下载 `llama.cpp` Linux 二进制库
   - 启动 HTTP 服务

## API 设计

### `GET /`

返回 WebUI 页面，提供：

- 文件上传
- 温度参数
- 返回格式选择
- 转录结果展示

### `GET /healthz`

返回服务健康状态，包括：

- 服务版本
- 模型路径
- 模型是否已准备

### `POST /v1/audio/transcriptions`

OpenAI 风格的表单上传接口：

- `file`: 音频或视频文件
- `temperature`: 可选
- `response_format`: `text` / `json` / `verbose_json` / `srt`

响应：

- `text`: 纯文本
- `json`: `{ text }`
- `verbose_json`: `{ text, segments, srt, model, timings }`
- `srt`: 纯字幕文本

### `POST /api/transcriptions`

与 `/v1/audio/transcriptions` 等价的中文语义别名，便于直接接入内部服务。

## 模型与运行时策略

### 模型

- 默认模型资产来源：上游 `models` release 中的 `Fun-ASR-Nano-GGUF.zip`
- 默认模型落盘目录：容器内 `/data/models/Fun-ASR-Nano/Fun-ASR-Nano-GGUF`
- 通过环境变量允许改写模型目录或关闭自动下载

### llama.cpp 动态库

- 通过启动脚本自动下载官方 Linux x64 二进制包
- 将运行所需 `.so` 文件解压到 `util/fun_asr_gguf/inference/bin`
- 默认关闭 Vulkan，加快 CPU 场景落地稳定性

## 并发与资源控制

- 模型实例在进程内单例持有。
- 转录请求使用互斥锁串行执行，避免底层推理对象线程安全问题。
- Web 层继续并发接收请求，但实际转录按顺序执行。

## 错误处理

- 上传文件为空或格式错误时返回 `400`。
- 模型资产缺失且自动下载关闭时返回 `503`。
- 推理异常时返回结构化 `500`，并保留日志。
- WebUI 展示清晰错误信息，不让用户直接看到堆栈。

## 测试策略

- 先对 HTTP 层做测试，使用假的转录器替身，不依赖真实模型。
- 覆盖：
  - 健康检查
  - WebUI 页面可访问
  - `text/json/verbose_json/srt` 响应格式
  - 错误场景
- 最后做容器构建验证和无模型启动验证。

## 交付物

- 新增容器服务代码
- `Dockerfile`
- `docker-compose.yml`
- 容器启动脚本与模型下载脚本
- WebUI 页面
- 自动化测试
- 使用文档
