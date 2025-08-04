# Testing Guide for Good Morning Agent

這份指南說明如何執行 Good Morning Agent 的測試套件，包括單元測試、整合測試和端到端測試。

## 📋 測試架構概述

### 測試層次
1. **單元測試 (Unit Tests)** - 快速、隔離的元件測試
2. **整合測試 (Integration Tests)** - 元件間交互測試
3. **端到端測試 (E2E Tests)** - 完整流程測試

### 測試目錄結構
```
tests/
├── conftest.py                    # pytest 配置和共用 fixtures
├── .env.test                      # 測試環境變數
├── run_tests.py                   # 測試執行腳本
├── data/
│   └── fixtures/
│       └── sample_newsletters.py  # 測試資料
├── unit/                          # 單元測試
│   └── collectors/
│       └── test_email_reader.py
├── integration/                   # 整合測試
│   └── test_email_collection_integration.py
└── e2e/                          # 端到端測試
    └── test_full_pipeline.py
```

## 🚀 快速開始

### 1. 安裝測試依賴

```bash
# 使用 make 命令（推薦）
make setup

# 或手動安裝
uv sync --dev
```

### 2. 執行單元測試

```bash
# 使用 make 命令
make test

# 使用 pytest 直接執行
python -m pytest tests/unit/ -v

# 使用測試腳本
python tests/run_tests.py --unit
```

## 🧪 測試類型詳解

### 單元測試 (Unit Tests)
- **目的**: 測試單一元件的功能
- **特點**: 快速執行，使用 Mock 隔離外部依賴
- **執行時間**: < 30 秒

```bash
# 執行所有單元測試
make test

# 執行特定模組測試
python -m pytest tests/unit/collectors/test_email_reader.py -v

# 跳過慢速測試
python -m pytest tests/unit/ -m "not slow" -v
```

### 整合測試 (Integration Tests)
- **目的**: 測試元件間的交互
- **特點**: 需要部分真實服務（測試用 Gmail 帳號）
- **執行時間**: 1-5 分鐘

**前置需求**: 設定測試用 Gmail 帳號

```bash
# 設定整合測試環境變數
export INTEGRATION_COLLECTION_EMAIL="your.test.collector@gmail.com"
export INTEGRATION_EMAIL_PASSWORD="your_app_password"

# 執行整合測試
python tests/run_tests.py --integration
```

### 端到端測試 (E2E Tests)
- **目的**: 測試完整的業務流程
- **特點**: 需要所有真實服務（Gmail + OpenAI API）
- **執行時間**: 5-15 分鐘

**前置需求**: 完整的服務設定

```bash
# 設定所有必要的環境變數
export INTEGRATION_COLLECTION_EMAIL="your.test.collector@gmail.com"
export INTEGRATION_EMAIL_PASSWORD="your_app_password"
export INTEGRATION_OPENAI_API_KEY="your_openai_api_key"
export INTEGRATION_SENDER_EMAIL="your.test.sender@gmail.com"
export INTEGRATION_SENDER_PASSWORD="your_sender_app_password"

# 執行端到端測試
python tests/run_tests.py --e2e
```

## 📊 測試覆蓋率

### 執行覆蓋率報告

```bash
# 生成 HTML 覆蓋率報告
make coverage

# 或使用測試腳本
python tests/run_tests.py --coverage

# 查看覆蓋率報告
open htmlcov/index.html
```

### 覆蓋率目標
- **最低要求**: 80%
- **目標**: 90%+
- **核心模組**: 95%+

## 🛠️ 手動準備需求

### 測試用 Gmail 帳號設定

1. **建立專用測試帳號**
   ```
   收集信箱: your.test.collector@gmail.com
   發送信箱: your.test.sender@gmail.com  
   ```

2. **啟用 2FA 和應用程式密碼**
   - 到 Google 帳號設定
   - 啟用兩步驟驗證
   - 生成應用程式密碼

3. **訂閱測試電子報**
   - 使用收集信箱訂閱 2-3 個電子報
   - 建議: TLDR, Deep Learning Weekly, Pragmatic Engineer

4. **設定環境變數**
   ```bash
   # 複製範本
   cp tests/.env.test tests/.env.local
   
   # 編輯實際的憑證
   vim tests/.env.local
   ```

### OpenAI API 設定

1. **取得 API Key**
   - 到 OpenAI Platform 申請
   - 設定使用額度限制

2. **設定環境變數**
   ```bash
   export INTEGRATION_OPENAI_API_KEY="sk-..."
   ```

## 🏃‍♂️ 測試執行指令

### 常用指令

```bash
# 快速單元測試
make test

# 完整測試套件
make test-all

# 測試 + 程式碼品質檢查
make check

# 單獨執行各種測試
python tests/run_tests.py --unit        # 單元測試
python tests/run_tests.py --integration # 整合測試  
python tests/run_tests.py --e2e         # 端到端測試
python tests/run_tests.py --all         # 所有測試
python tests/run_tests.py --coverage    # 覆蓋率測試
python tests/run_tests.py --lint        # 程式碼品質檢查
```

### Pytest 標記

```bash
# 執行特定標記的測試
python -m pytest -m "unit"        # 單元測試
python -m pytest -m "integration" # 整合測試
python -m pytest -m "e2e"         # 端到端測試
python -m pytest -m "slow"        # 慢速測試
python -m pytest -m "not slow"    # 跳過慢速測試
```

## 🔍 除錯測試

### 常見問題

1. **IMAP 連線失敗**
   ```bash
   # 檢查憑證
   echo $INTEGRATION_EMAIL_PASSWORD
   
   # 測試 IMAP 連線
   python -c "import imaplib; imaplib.IMAP4_SSL('imap.gmail.com', 993)"
   ```

2. **OpenAI API 錯誤**
   ```bash
   # 檢查 API Key 
   echo $INTEGRATION_OPENAI_API_KEY
   
   # 測試 API 呼叫
   curl -H "Authorization: Bearer $INTEGRATION_OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

3. **測試資料問題**
   ```bash
   # 檢查測試資料檔案
   python -c "from tests.data.fixtures.sample_newsletters import ALL_SAMPLE_NEWSLETTERS; print(len(ALL_SAMPLE_NEWSLETTERS))"
   ```

### 詳細除錯

```bash
# 啟用詳細輸出
python -m pytest tests/ -v -s --tb=long

# 執行特定測試
python -m pytest tests/unit/collectors/test_email_reader.py::TestEmailReaderConnection::test_imap_connection_success -v -s

# 使用 pdb 除錯器
python -m pytest tests/ --pdb
```

## 📝 撰寫測試

### 測試命名慣例

```python
class TestEmailReader:           # 測試類別以 Test 開頭
    def test_connection_success(self):  # 測試方法以 test_ 開頭
        pass
        
    def test_connection_failure(self):  # 描述性的測試名稱
        pass
```

### 使用 Fixtures

```python
def test_email_parsing(self, sample_email_data, mock_imap_connection):
    """使用 conftest.py 中定義的 fixtures"""
    # 測試程式碼
    pass
```

### 標記測試

```python
@pytest.mark.slow
def test_large_dataset_processing(self):
    """標記為慢速測試"""
    pass

@pytest.mark.integration  
def test_real_api_integration(self, require_api_keys):
    """標記為整合測試"""
    pass
```

## 🎯 最佳實務

1. **測試隔離**: 每個測試應該獨立執行
2. **描述性命名**: 測試名稱應該清楚描述測試內容
3. **適當標記**: 使用標記分類不同類型的測試
4. **Mock 外部服務**: 單元測試應該 Mock 所有外部依賴
5. **測試邊界條件**: 測試正常情況和錯誤情況
6. **保持測試簡單**: 一個測試專注測試一個功能

## 📚 延伸閱讀

- [Pytest 官方文件](https://docs.pytest.org/)
- [Python Mock 使用指南](https://docs.python.org/3/library/unittest.mock.html)
- [測試驅動開發 (TDD) 最佳實務](https://testdriven.io/blog/modern-tdd/)

---

## 📞 問題回報

如果在測試過程中遇到問題，請：
1. 檢查本指南的除錯章節
2. 確認環境變數設定正確
3. 查看 GitHub Issues 或建立新的 Issue