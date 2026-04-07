# WebUI 与 SRT 打磨 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Docker 版 Fun-ASR-Nano 服务具备更好的 WebUI、自然分段的 SRT、前端下载能力和清晰的容器互调说明。

**Architecture:** 保留现有 HTTP API 与字符级原始时间戳，在格式化层新增字幕聚合输出 `subtitle_segments`，由 WebUI 使用 `verbose_json` 渲染更友好的结果卡片和下载按钮。部署层仅补充 `expose` 与文档，不引入额外服务端状态。

**Tech Stack:** FastAPI, Jinja2, 原生前端 JS, pytest, Docker Compose

---

### Task 1: 为字幕聚合补测试

**Files:**
- Create: `tests/test_formatters.py`
- Modify: `tests/test_web_app.py`

- [ ] 写失败测试，覆盖字符级时间戳聚合为自然字幕段、SRT 基于聚合段渲染、`verbose_json` 返回新增字段。
- [ ] 运行相关测试并确认先失败。

### Task 2: 实现字幕聚合与结果结构

**Files:**
- Modify: `capsweb/contracts.py`
- Modify: `capsweb/formatters.py`
- Modify: `capsweb/transcriber.py`

- [ ] 在结果契约中新增 `subtitle_segments`。
- [ ] 在格式化层实现聚合函数与新的 SRT 渲染流程。
- [ ] 更新转录器，把原始片段与字幕片段同时写入结果对象。
- [ ] 运行 Task 1 新增测试并确认转绿。

### Task 3: 重做 WebUI 结果区和下载交互

**Files:**
- Modify: `capsweb/templates/index.html`
- Modify: `tests/test_web_app.py`

- [ ] 写失败测试，覆盖界面中存在结果区升级后的关键元素和下载入口。
- [ ] 重新组织页面布局、结果摘要、字幕预览和下载按钮。
- [ ] 在前端使用 Blob 下载文本、JSON、SRT。
- [ ] 运行 Web 相关测试确认通过。

### Task 4: 明确容器互调入口与部署说明

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docs/docker-webui.md`
- Modify: `readme.md`

- [ ] 为服务增加更明确的容器内暴露表达。
- [ ] 文档补充宿主机调用、同网络容器调用、健康检查和下载能力说明。
- [ ] 保持示例与当前接口返回结构一致。

### Task 5: 整体清查与验证

**Files:**
- Modify: `capsweb/app.py`（如需）
- Modify: 其他被本轮修改的文件

- [ ] 清理重复逻辑和低信噪比实现，确保结果数据流职责清晰。
- [ ] 运行全部测试。
- [ ] 重建并启动 Docker 容器。
- [ ] 用真实 HTTP 请求验证：
  - `GET /healthz`
  - `POST /v1/audio/transcriptions` 返回 `verbose_json`
  - `POST /api/transcriptions` 返回 `srt`
- [ ] 将最终行为写入文档说明。
