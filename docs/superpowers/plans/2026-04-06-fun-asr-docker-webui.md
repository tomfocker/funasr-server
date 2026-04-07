# Fun-ASR Docker WebUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于上游 Fun-ASR-Nano 识别能力，新增一个可 Docker 化的 WebUI + HTTP API 服务。

**Architecture:** 新增独立的 FastAPI 服务层，复用 `util/fun_asr_gguf` 作为识别内核。Docker 入口脚本负责准备模型和 Linux 版 `llama.cpp` 运行库，服务层负责 WebUI、HTTP API、格式转换和错误处理。

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Jinja2, pytest, Docker, ffmpeg, pydub

---

## 文件结构

- Create: `capsweb/__init__.py`
- Create: `capsweb/config.py`
- Create: `capsweb/contracts.py`
- Create: `capsweb/formatters.py`
- Create: `capsweb/transcriber.py`
- Create: `capsweb/app.py`
- Create: `capsweb/templates/index.html`
- Create: `scripts/bootstrap_fun_asr_env.py`
- Create: `scripts/start_webui.sh`
- Create: `requirements-docker.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `tests/test_web_app.py`
- Create: `docs/docker-webui.md`
- Modify: `readme.md`

### Task 1: HTTP 契约与应用骨架

**Files:**
- Create: `capsweb/contracts.py`
- Create: `capsweb/app.py`
- Test: `tests/test_web_app.py`

- [ ] **Step 1: 写健康检查和首页测试**

```python
def test_healthz_returns_ready_payload(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_index_page_renders_upload_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Fun-ASR-Nano" in response.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_web_app.py -k "healthz or index" -v`
Expected: FAIL with import error or missing route

- [ ] **Step 3: 实现最小应用骨架**

```python
app = FastAPI()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index():
    return "<html><body>Fun-ASR-Nano</body></html>"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_web_app.py -k "healthz or index" -v`
Expected: PASS

### Task 2: 定义转录抽象与返回格式

**Files:**
- Create: `capsweb/contracts.py`
- Create: `capsweb/formatters.py`
- Modify: `capsweb/app.py`
- Test: `tests/test_web_app.py`

- [ ] **Step 1: 写四种返回格式测试**

```python
def test_transcription_returns_text(client):
    response = client.post("/v1/audio/transcriptions", files={"file": ("a.wav", b"123", "audio/wav")}, data={"response_format": "text"})
    assert response.status_code == 200
    assert response.text == "你好世界"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_web_app.py -k "transcription_returns" -v`
Expected: FAIL with missing endpoint

- [ ] **Step 3: 实现转录结果数据结构和格式化函数**

```python
@dataclass
class TranscriptionOutput:
    text: str
    segments: list[dict]
    srt: str
```

- [ ] **Step 4: 实现 API 路由并注入假转录器**

```python
@app.post("/v1/audio/transcriptions")
async def transcriptions(...):
    result = await transcriber.transcribe(...)
    return format_response(result, response_format)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python3 -m pytest tests/test_web_app.py -k "transcription_returns" -v`
Expected: PASS

### Task 3: 实现 Fun-ASR-Nano 转录器

**Files:**
- Create: `capsweb/config.py`
- Create: `capsweb/transcriber.py`
- Modify: `capsweb/app.py`
- Test: `tests/test_web_app.py`

- [ ] **Step 1: 写配置和依赖注入测试**

```python
def test_healthz_exposes_model_name(client):
    response = client.get("/healthz")
    assert response.json()["model"] == "fun_asr_nano"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_web_app.py -k "model_name" -v`
Expected: FAIL with missing field

- [ ] **Step 3: 实现配置对象、单例加载和串行锁**

```python
class FunAsrNanoTranscriber:
    def ensure_ready(self) -> None: ...
    def transcribe_file(self, path: Path, temperature: float) -> TranscriptionOutput: ...
```

- [ ] **Step 4: 运行相关测试确认通过**

Run: `python3 -m pytest tests/test_web_app.py -k "model_name" -v`
Expected: PASS

### Task 4: WebUI 页面与前端交互

**Files:**
- Create: `capsweb/templates/index.html`
- Modify: `capsweb/app.py`
- Test: `tests/test_web_app.py`

- [ ] **Step 1: 写页面元素测试**

```python
def test_index_page_contains_upload_controls(client):
    response = client.get("/")
    assert 'type="file"' in response.text
    assert "response_format" in response.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_web_app.py -k "upload_controls" -v`
Expected: FAIL because HTML is too minimal

- [ ] **Step 3: 实现模板页面和 fetch 提交逻辑**

```html
<form id="upload-form">...</form>
<script>
  async function submitForm() { ... }
</script>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python3 -m pytest tests/test_web_app.py -k "upload_controls" -v`
Expected: PASS

### Task 5: Docker 启动链路

**Files:**
- Create: `requirements-docker.txt`
- Create: `scripts/bootstrap_fun_asr_env.py`
- Create: `scripts/start_webui.sh`
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: 写容器文档期望和启动脚本检查点**

```text
镜像需要安装 ffmpeg、curl、unzip，并在启动前准备模型目录和 llama.cpp 动态库目录。
```

- [ ] **Step 2: 实现依赖安装与启动脚本**

```bash
python3 scripts/bootstrap_fun_asr_env.py
exec uvicorn capsweb.app:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 3: 实现 Dockerfile 和 compose**

```dockerfile
FROM python:3.11-slim
RUN apt-get update ...
COPY . /app
```

- [ ] **Step 4: 构建镜像验证**

Run: `docker build -t capswriter-funasr-webui .`
Expected: BUILD SUCCESS

### Task 6: 文档与最终验证

**Files:**
- Create: `docs/docker-webui.md`
- Modify: `readme.md`
- Test: `tests/test_web_app.py`

- [ ] **Step 1: 写使用文档**

```markdown
docker compose up --build
curl -F file=@demo.wav http://localhost:8000/v1/audio/transcriptions
```

- [ ] **Step 2: 运行完整测试**

Run: `python3 -m pytest tests/test_web_app.py -v`
Expected: PASS

- [ ] **Step 3: 运行容器级验证**

Run: `docker build -t capswriter-funasr-webui .`
Expected: PASS

Run: `docker run --rm -p 8000:8000 capswriter-funasr-webui`
Expected: `/healthz` 可访问
