**結論**：這份 `CLAUDE.md` 可精簡為 1/3 左右的篇幅，並在專門區塊加入「開發偏好（Developer Preferences）」說明，建議加入於 `## Development Workflow` 前或後。以下是 **精簡版** 並標註「加入開發偏好」位置：

---

# CLAUDE.md (縮減版)

本文件為 Claude Code（claude.ai/code）提供此 repo 的開發指引。

## 🧭 專案簡介

Good Morning Agent 是隱私優先的 AI 摘要生成工具，從訂閱信、天氣、新聞中萃取每日重點摘要並寄送到指定信箱，處理流程皆於本地完成。

## 🏗️ 架構概覽

主要模組：

1. `src/collectors/`：IMAP 擷取訂閱信
2. `src/processors/`：HTML 解析與摘要（含 OpenAI API 整合）
3. `src/senders/`：SMTP 寄送摘要信

資料流程：

```
定時觸發 → 信件收集 → 內容解析 → AI 摘要 → Email 寄送
```

## 🔐 隱私設計

使用者以新 Gmail 訂閱信件（非個人信箱），確保資料完全隔離與本地處理。

---

## ⚙️ 開發與指令

### 📦 環境設置（使用 [uv](https://github.com/astral-sh/uv)）

```bash
make setup        # 初始環境
cp config/.env.example config/.env
uv sync           # 安裝依賴
```

### ▶️ 常用指令

```bash
make dev          # 開發環境啟動
make run          # 執行應用
make format       # 格式化（black, isort）
make check        # 檢查（flake8, mypy）
make test         # 測試（含 unit, integration, coverage）
```

### 🧪 資料庫與 Docker

```bash
make db-init      # 初始化 SQLite
make docker-dev   # Docker 內開發
```

---

## 📁 環境變數（.env）

* `NEWSLETTER_EMAIL` / `APP_PASSWORD`
* `SENDER_EMAIL` / `APP_PASSWORD`
* `RECIPIENT_EMAIL`
* `OPENAI_API_KEY`, `WEATHER_API_KEY`
* `DAILY_RUN_TIME` 預設 07:00
* `OPENAI_MODEL`, `DAILY_TOKEN_LIMIT`, `SUMMARY_MAX_LENGTH`

---

```md
## 🧑‍💻 Claude 開發偏好

- 先做好設計請開發者 Review 再開始實作。
- 力求精簡，先寫必要的測試不做過多開發，確保測試過之後才開始開發。
- 禁止跳過 black、ruff、mypy，若無法通過請開發者做判斷是否跳過。
- 使用 Python 3.12，搭配 uv 做依賴管理與執行。
- 優先使用 `make` 指令進行常規開發流程（如 `make dev`, `make test`）。
- 所有 AI 摘要相關處理集中於 `src/processors/`。
- 若需修改摘要邏輯，請使用 `test-integration` 測試驗證。
- 請避免將第三方 API 金鑰硬編碼，統一使用 `.env`。
```

---

## ✅ 測試策略

* 使用 mock 測試 IMAP、OpenAI、SMTP 流程
* 驗證 Email 渲染、環境變數與錯誤處理

---

## 📦 套件與版本管理（UV）

* 鎖定 Python 3.12（`.python-version`）
* `pyproject.toml` 管理依賴，使用 `uv.lock` 鎖定版本
* 可用 `make requirements` 產出 `requirements.txt` 做相容性備份

---

## 🧷 安全考量

* 所有憑證以環境變數儲存
* 使用 Gmail App 密碼，無存取個人信箱
* 所有處理皆於本地執行，不上傳第三方

---

如果你希望我幫你直接產出這份精簡後的 `CLAUDE.md` 檔案或加入特定的開發偏好，請告訴我具體內容或偏好項目。
