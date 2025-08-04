# Good Morning Agent 系統架構設計

## 1. 核心機能需求分析

### 1.1 系統核心功能
```
📧 資料收集層
├── 電子報收集 (專用信箱 IMAP)
├── 天氣資訊 (Weather API)
└── 新聞資訊 (News API/RSS)

🔄 處理執行層
├── 內容解析 (HTML → 結構化資料)
├── 內容清理 (去廣告、標準化)
├── AI 摘要生成 (OpenAI/Gemini)
└── 格式化輸出 (HTML Email)

⏰ 排程執行層
├── 定時觸發 (每日早上 7:00)
├── 錯誤重試機制
└── 執行狀態監控

📤 輸出配送層
├── Email 發送 (SMTP)
├── 格式渲染 (HTML Template)
└── 發送狀態追蹤
```

### 1.2 非功能性需求
- **可靠性**: 99.5% 正常運行時間
- **效能**: 處理時間 < 5 分鐘
- **擴展性**: 支援 1000+ 用戶
- **安全性**: 資料加密、API 權限控制
- **可維護性**: 容器化部署、日誌監控

## 2. GCP 雲端架構設計

### 2.1 服務架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        GCP 雲端架構                              │
├─────────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │ Cloud       │    │ Cloud        │    │ Cloud       │      │
│  │ Scheduler   │───▶│ Functions    │───▶│ Storage     │      │
│  │ (定時觸發)   │    │ (主要邏輯)    │    │ (資料存儲)   │      │
│  └─────────────┘    └──────────────┘    └─────────────┘      │
│                             │                                │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │ Cloud       │    │ Cloud        │    │ Secret      │      │
│  │ SQL         │◀───│ Run          │    │ Manager     │      │
│  │ (PostgreSQL)│    │ (API 服務)    │    │ (金鑰管理)   │      │
│  └─────────────┘    └──────────────┘    └─────────────┘      │
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │ Cloud       │    │ Cloud        │    │ Cloud       │      │
│  │ Logging     │    │ Monitoring   │    │ IAM         │      │
│  │ (日誌記錄)   │    │ (系統監控)    │    │ (權限管理)   │      │
│  └─────────────┘    └──────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 GCP 服務選型與配置

#### 主要計算服務
```yaml
Cloud Functions (Gen2):
  - Runtime: Python 3.11
  - Memory: 512MB
  - Timeout: 540s (9分鐘)
  - Trigger: Cloud Scheduler
  - 用途: 主要的資料收集和處理邏輯

Cloud Run:
  - Container: Python Flask API
  - Memory: 1GB
  - CPU: 1
  - Max Instances: 10
  - 用途: Web API 和用戶管理介面
```

#### 資料存儲服務
```yaml
Cloud SQL (PostgreSQL):
  - Version: PostgreSQL 15
  - Machine Type: db-f1-micro (MVP)
  - Storage: 10GB SSD
  - 用途: 用戶資料、電子報內容、摘要結果

Cloud Storage:
  - Bucket Class: Standard
  - Location: asia-east1 (台灣)
  - 用途: 原始郵件備份、生成的 HTML 檔案
```

#### 排程與監控
```yaml
Cloud Scheduler:
  - Schedule: "0 7 * * *" (每日早上7點)
  - Timezone: Asia/Taipei
  - Target: Cloud Functions HTTP Trigger

Cloud Monitoring:
  - Metrics: 函數執行時間、錯誤率、API 回應時間
  - Alerts: 執行失敗、處理時間過長

Cloud Logging:
  - Log Level: INFO
  - Retention: 30 days
```

### 2.3 GCP 實作架構程式碼結構

```python
# 主要 Cloud Function
import functions_framework
from google.cloud import secretmanager
from google.cloud import sql
from google.cloud import storage

@functions_framework.http
def main_processor(request):
    """主要處理邏輯"""
    try:
        # 1. 從 Secret Manager 獲取 API 金鑰
        credentials = get_secrets()
        
        # 2. 收集電子報資料
        newsletters = collect_newsletters(credentials)
        
        # 3. 收集天氣和新聞
        weather = get_weather_data()
        news = get_news_data()
        
        # 4. 生成摘要
        summary = generate_summary(newsletters, weather, news)
        
        # 5. 發送郵件
        send_email(summary)
        
        # 6. 記錄執行狀態
        log_execution_status("success")
        
        return {"status": "success"}
    
    except Exception as e:
        log_execution_status("failed", str(e))
        return {"status": "error", "message": str(e)}, 500

# 資料庫連接
def get_db_connection():
    return sqlalchemy.create_engine(
        "postgresql+pg8000://user:password@/db_name"
        "?unix_sock=/cloudsql/project:region:instance/.s.PGSQL.5432"
    )
```

## 3. 本地運行架構設計

### 3.1 本地開發架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        本地開發環境                               │
├─────────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │ Cron Job    │    │ Python       │    │ SQLite      │      │
│  │ (定時執行)   │───▶│ Application  │───▶│ Database    │      │
│  │             │    │ (主邏輯)      │    │ (本地資料)   │      │
│  └─────────────┘    └──────────────┘    └─────────────┘      │
│                             │                                │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │ Local Files │    │ Environment  │    │ Log Files   │      │
│  │ (郵件備份)   │◀───│ Variables    │    │ (執行記錄)   │      │
│  │             │    │ (.env)       │    │             │      │
│  └─────────────┘    └──────────────┘    └─────────────┘      │
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐      │
│  │ Docker      │    │ Flask        │    │ SMTP        │      │
│  │ Container   │    │ Web UI       │    │ Server      │      │
│  │ (可選)       │    │ (可選)       │    │ (郵件發送)   │      │
│  └─────────────┘    └──────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 本地運行配置

#### 目錄結構
```
good-morning-agent/
├── src/
│   ├── collectors/          # 資料收集模組
│   │   ├── newsletter.py
│   │   ├── weather.py
│   │   └── news.py
│   ├── processors/          # 資料處理模組
│   │   ├── parser.py
│   │   ├── summarizer.py
│   │   └── formatter.py
│   ├── senders/            # 輸出發送模組
│   │   └── email_sender.py
│   └── utils/              # 工具函數
│       ├── database.py
│       └── config.py
├── config/
│   ├── .env.example
│   └── config.yaml
├── data/                   # 本地資料存儲
│   ├── emails/
│   ├── summaries/
│   └── logs/
├── scripts/
│   ├── setup.sh
│   └── run_daily.py
├── tests/
├── docker/
│   └── Dockerfile
└── requirements.txt
```

#### 環境配置 (.env)
```env
# 資料庫配置
DATABASE_URL=sqlite:///data/good_morning.db

# API 金鑰
OPENAI_API_KEY=your_openai_key
WEATHER_API_KEY=your_weather_key
NEWS_API_KEY=your_news_key

# 郵件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# 專用收集信箱
NEWSLETTER_EMAIL=good-morning-newsletters@gmail.com
NEWSLETTER_PASSWORD=your_newsletter_password

# 執行配置
TIMEZONE=Asia/Taipei
DAILY_RUN_TIME=07:00
```

#### Docker 配置
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# 創建資料目錄
RUN mkdir -p data/emails data/summaries data/logs

# 設定定時任務
COPY scripts/crontab /etc/cron.d/good-morning-agent
RUN chmod 0644 /etc/cron.d/good-morning-agent
RUN crontab /etc/cron.d/good-morning-agent

CMD ["python", "scripts/run_daily.py"]
```

## 4. 成本與擴展性評估

### 4.1 GCP 成本估算

#### MVP 階段 (單一用戶)
```
Cloud Functions:
- 執行次數: 30次/月 (每日1次)
- 執行時間: 平均3分鐘
- Memory: 512MB
- 月費用: ~$0.10

Cloud SQL (db-f1-micro):
- 月費用: ~$9.37

Cloud Storage:
- 存儲: 1GB
- 月費用: ~$0.03

Cloud Scheduler:
- 月費用: $0.10/job = $0.10

總計: ~$9.60/月
```

#### 生產階段 (100用戶)
```
Cloud Functions:
- 執行次數: 3,000次/月
- 月費用: ~$10.50

Cloud SQL (db-g1-small):
- 月費用: ~$46.84

Cloud Run (API 服務):
- 月費用: ~$7.00

其他服務: ~$5.00

總計: ~$69.34/月 (每用戶 $0.69/月)
```

#### 擴展階段 (1000用戶)
```
多區域部署: ~$200/月
負載均衡: ~$18/月
監控告警: ~$50/月
資料備份: ~$30/月

總計: ~$300-500/月 (每用戶 $0.30-0.50/月)
```

### 4.2 本地運行成本

```
硬體需求:
- CPU: 2 核心
- Memory: 4GB
- Storage: 20GB
- 月電費: ~$5-10

API 服務費用:
- OpenAI API: ~$10-30/月
- Weather API: 免費額度內
- News API: 免費額度內

總成本: ~$15-40/月
```

### 4.3 擴展性對比分析

| 指標 | 本地運行 | GCP 雲端 |
|------|----------|----------|
| **初期成本** | 低 ($15/月) | 中 ($10/月) |
| **擴展成本** | 高 (需要更多硬體) | 線性成長 |
| **維護難度** | 高 (需要自行維護) | 低 (託管服務) |
| **可靠性** | 中 (依賴本地網路) | 高 (99.9% SLA) |
| **擴展速度** | 慢 (需要硬體升級) | 快 (自動擴展) |
| **開發複雜度** | 中 | 高 (學習 GCP 服務) |

## 5. 開發優先級建議

### 5.1 MVP 開發階段 (推薦：本地運行)

**理由**:
- 開發成本最低，學習曲線平緩
- 快速驗證產品概念
- 不需要掌握 GCP 複雜服務
- 資料完全私有，符合隱私需求

**技術棧**:
```python
# 簡單的 Python 腳本
Python 3.11
├── imaplib (郵件收集)
├── requests (API 調用)  
├── sqlite3 (資料存儲)
├── smtplib (郵件發送)
├── schedule (定時執行)
└── jinja2 (HTML 模板)
```

### 5.2 生產階段 (推薦：GCP 雲端)

**觸發條件**:
- 用戶數量 > 10 人
- 需要 24/7 穩定運行
- 需要更好的監控和告警
- 希望降低維護工作量

**遷移策略**:
1. **Week 1**: 設定 GCP 專案，遷移資料庫到 Cloud SQL
2. **Week 2**: 重構代碼為 Cloud Functions
3. **Week 3**: 設定監控、告警、備份機制
4. **Week 4**: 灰度測試，逐步切換用戶

### 5.3 混合架構 (長期方案)

```python
# 配置驅動的部署
class DeploymentConfig:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'local')
        
        if self.environment == 'local':
            self.database = SQLiteDatabase()
            self.scheduler = CronScheduler()
            self.storage = LocalFileStorage()
        elif self.environment == 'gcp':
            self.database = CloudSQLDatabase()
            self.scheduler = CloudScheduler()
            self.storage = CloudStorage()
```

## 6. 架構決策建議

### 6.1 MVP 階段：本地運行優先

**開發時程**: 2-3 週
**目標**: 驗證產品概念，單用戶使用

**技術決策**:
```yaml
資料庫: SQLite (簡單、免維護)
部署: 本地 Python 腳本 + Cron
監控: 簡單的 log 文件
備份: Git + 本地文件系統
成本: ~$20/月 (主要是 API 費用)
```

### 6.2 擴展階段：GCP 雲端遷移

**觸發條件**: 驗證成功，需要多用戶支援
**遷移時程**: 3-4 週

**技術決策**:
```yaml
計算: Cloud Functions + Cloud Run
資料庫: Cloud SQL (PostgreSQL)
存儲: Cloud Storage
監控: Cloud Monitoring + Logging
部署: Infrastructure as Code (Terraform)
成本: ~$0.50/用戶/月
```

### 6.3 建議實施路徑

```
Phase 1 (MVP): 本地運行
├── 快速開發驗證概念
├── 成本控制在 $20/月內
└── 完成核心功能開發

Phase 2 (遷移): 雲端部署  
├── 重構代碼適應雲端服務
├── 建立 CI/CD 流程
└── 支援多用戶

Phase 3 (優化): 生產優化
├── 效能調優
├── 成本優化
└── 功能擴展
```

**你對這個分階段的架構規劃有什麼想法？建議先從本地 MVP 開始，還是直接跳到 GCP 雲端？**

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "\u5206\u6790\u6838\u5fc3\u904b\u884c\u6a5f\u80fd\u9700\u6c42", "status": "completed", "priority": "high"}, {"id": "2", "content": "\u8a2d\u8a08 GCP \u96f2\u7aef\u67b6\u69cb", "status": "completed", "priority": "high"}, {"id": "3", "content": "\u8a2d\u8a08\u672c\u5730\u904b\u884c\u67b6\u69cb", "status": "completed", "priority": "high"}, {"id": "4", "content": "\u8a55\u4f30\u6210\u672c\u548c\u64f4\u5c55\u6027", "status": "completed", "priority": "high"}, {"id": "5", "content": "\u5236\u5b9a\u958b\u767c\u512a\u5148\u7d1a\u5efa\u8b70", "status": "completed", "priority": "medium"}, {"id": "6", "content": "\u64b0\u5beb\u67b6\u69cb\u8a2d\u8a08\u6587\u4ef6", "status": "completed", "priority": "high"}]