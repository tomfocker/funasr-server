# funasr-server

一个面向 Docker 部署的 `Fun-ASR-Nano` HTTP 识别服务。

这个仓库现在的目标很明确：

- 提供稳定的语音识别 API
- 提供健康检查和 OpenAPI 文档
- 支持本地模型挂载或首次启动自动下载模型
- 作为独立后端，与纯前端 `video-cuter` 或整合版 bundle 配合使用

## 项目定位

`funasr-server` 是从 `CapsWriter-Offline` 的代码基础上演化出来的独立后端项目。

当前仓库只维护服务端能力，不再承担：

- Windows 桌面输入工具定位
- 客户端快捷键录音体验
- 本地托盘交互
- 网页前端工作台

换句话说，这里现在是一个“纯后端服务仓库”。

## 与原项目的关系

这个仓库和原始参考项目 [`HaujetZhao/CapsWriter-Offline`](https://github.com/HaujetZhao/CapsWriter-Offline) 仍然有代码血缘关系，但产品方向已经拆开了。

我们保留了那些对当前项目仍然有价值的内容，例如：

- Fun-ASR 推理相关代码
- 底层共享库加载逻辑
- 部分音频、文本、热词、工具链实现

之所以保留这些代码和提交历史，是因为它们对现在的服务项目仍然有实际帮助，没必要为了“看起来全新”而把成熟实现和历史证据全部抹掉。

## 为什么会看到原项目关联和多个贡献者

如果你在 GitHub 上看到本仓库仍然带有多个贡献者，这通常是因为：

- 当前仓库继承了早期提交历史
- GitHub 的 `Contributors` 统计基于 commit 作者历史
- 这代表代码历史来源，不代表当前产品仍然和原项目强绑定

所以现在可以这样理解：

- 历史上：它来源于 `CapsWriter-Offline`
- 现在：它作为 `funasr-server` 独立维护

## 当前能力

- `GET /`：服务摘要
- `GET /healthz`：健康检查
- `GET /docs`：OpenAPI 文档
- `POST /v1/audio/transcriptions`：OpenAI 风格转录接口
- `POST /api/transcriptions`：简洁别名接口

支持输出格式：

- `text`
- `json`
- `verbose_json`
- `srt`

其中 `verbose_json` 会返回：

- `text`
- `segments`
- `subtitle_segments`
- `srt`
- `model`
- `timings`

## 模型策略

当前版本刻意只支持一个最合适的模型：

- `Fun-ASR-Nano`

默认策略是：

- 主镜像不内置模型
- 如果本地已有模型，则优先直接使用
- 如果没有模型，则容器首次启动时自动下载

这样做的好处是：

- 镜像更轻
- 模型可独立复用
- 更新更灵活
- 对 Docker 部署更友好

## 快速开始

### Docker Compose

```bash
docker compose up --build
```

启动后访问：

- `http://localhost:8000/`：服务摘要
- `http://localhost:8000/healthz`：健康检查
- `http://localhost:8000/docs`：OpenAPI 文档

### 调用示例

纯文本：

```bash
curl -F file=@sample.wav \
     -F response_format=text \
     http://localhost:8000/v1/audio/transcriptions
```

详细 JSON：

```bash
curl -F file=@sample.wav \
     -F response_format=verbose_json \
     http://localhost:8000/v1/audio/transcriptions
```

SRT：

```bash
curl -F file=@sample.wav \
     -F response_format=srt \
     http://localhost:8000/api/transcriptions
```

## 目录说明

- `capsweb/`
  - 当前服务层核心实现
- `util/fun_asr_gguf/`
  - Fun-ASR-Nano 推理相关实现
- `scripts/start_api_service.sh`
  - Docker 启动入口
- `Dockerfile`
  - 服务镜像构建
- `docker-compose.yml`
  - 本地部署入口
- `docs/docker-api-service.md`
  - Docker API 服务使用说明

## 与其他仓库的分工

- `video-cuter`
  - 纯前端视频裁剪工具
- `funasr-server`
  - 纯后端语音识别服务
- 整合版 bundle 仓库
  - 用 `docker compose` 把前端和后端组合成完整体验

## 测试

运行全部测试：

```bash
./.venv/bin/python -m pytest -q
```

## 致谢

本仓库的底层实现基础来自这些优秀项目：

- [HaujetZhao/CapsWriter-Offline](https://github.com/HaujetZhao/CapsWriter-Offline)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)
- [Sherpa-ONNX](https://github.com/k2-fsa/sherpa-onnx)

当前仓库在此基础上继续收缩模型范围、重组服务边界，并朝独立的 Docker API 服务方向维护。
