# 電子報資料源獲取設計文件

## 1. 設計目標

### 1.1 核心需求
- **隱私優先**: 最小化存取用戶個人資料的風險
- **內容完整**: 獲取完整的電子報內容用於深度摘要
- **技術簡單**: MVP 階段實作複雜度可控
- **擴展彈性**: 支援未來多用戶和多資料源擴展

### 1.2 目標電子報清單
以下為初期需要支援的電子報：
- **tl;dr** - 科技新聞摘要
- **Deep Learning Weekly** - AI/ML 技術週報
- **Pragmatic Engineer** - 軟體工程實務
- **其他**: 依據用戶需求逐步增加

## 2. 技術方案分析

### 2.1 方案評估矩陣

| 方案 | 實作難度 | 隱私風險 | 擴展性 | 內容完整度 | MVP適用性 |
|------|----------|----------|--------|------------|-----------|
| Gmail API 直接讀取 | ⭐⭐⭐ | ❌ 高 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| IMAP 協議讀取 | ⭐⭐⭐ | ❌ 高 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| Email 轉發收集 | ⭐⭐ | ⚠️ 中 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ |
| **專用收集信箱** | **⭐** | **✅ 低** | **⭐⭐⭐⭐** | **⭐⭐⭐⭐** | **✅** |
| RSS/公開源替代 | ⭐⭐ | ✅ 無 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⚠️ |

### 2.2 詳細技術分析

#### 方案A: Gmail API 直接讀取
```python
# 技術實作概要
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def get_newsletters_from_gmail(credentials):
    service = build('gmail', 'v1', credentials=credentials)
    # 需要 'https://www.googleapis.com/auth/gmail.readonly' 權限
    query = 'from:(newsletter@tldr.tech OR noreply@deeplearningweekly.com)'
    results = service.users().messages().list(userId='me', q=query).execute()
```

**風險評估**:
- **權限過大**: 需要讀取用戶所有郵件的權限
- **隱私疑慮**: 用戶擔心個人郵件被存取
- **合規問題**: GDPR/個資法合規困難

**不建議用於 MVP**

#### 方案B: IMAP 協議讀取
```python
# 技術實作概要
import imaplib
import email

def fetch_from_imap(username, password, host='imap.gmail.com'):
    mail = imaplib.IMAP4_SSL(host)
    mail.login(username, password)
    mail.select('inbox')
    # 搜尋特定寄件者
    status, messages = mail.search(None, 'FROM "newsletter@tldr.tech"')
```

**風險評估**:
- **認證風險**: 需要存儲用戶郵箱密碼
- **安全複雜**: 加密存儲、兩步驗證處理
- **維護困難**: 各郵件服務商設定差異大

**不建議用於 MVP**

#### 方案C: Email 轉發收集
**實作流程**:
1. 用戶在 Gmail 中設定篩選器
2. 符合條件的郵件自動轉發到系統信箱
3. 系統統一處理轉發的郵件

**設定範例** (Gmail):
```
篩選條件: from:(newsletter@tldr.tech)
動作: 轉發到 user1-forwards@good-morning-agent.com
```

**挑戰**:
- 用戶設定工作量大
- 轉發規則維護複雜
- 仍存在隱私疑慮

**可作為備選方案**

#### 方案D: 專用收集信箱 ⭐ (推薦)
**架構設計**:
```
用戶A: user-a-newsletters@gmail.com
用戶B: user-b-newsletters@gmail.com
系統: 定期從各專用信箱讀取內容
```

**實作步驟**:
1. 為每個用戶創建專用 Gmail 帳號
2. 使用專用帳號重新訂閱目標電子報
3. 使用 Gmail API 或 IMAP 讀取專用信箱
4. 解析郵件內容並進行摘要處理

**程式架構**:
```python
class NewsletterCollector:
    def __init__(self, user_id):
        self.dedicated_email = f"user-{user_id}-newsletters@gmail.com"
        self.imap_client = None
    
    def fetch_newsletters(self):
        # 從專用信箱獲取電子報
        newsletters = []
        for sender in self.target_senders:
            messages = self._fetch_from_sender(sender)
            newsletters.extend(messages)
        return newsletters
    
    def _fetch_from_sender(self, sender):
        # IMAP 實作細節
        pass
```

**優勢**:
- **零隱私風險**: 不涉及用戶個人信箱
- **設定簡單**: 只需重新訂閱（一次性工作）
- **完全隔離**: 每個用戶獨立的資料源
- **易於擴展**: 新增用戶只需創建新信箱

#### 方案E: RSS/公開源替代
**資源調查結果**:
```
✅ tl;dr: 有網站版本 (https://tldr.tech/)
❓ Deep Learning Weekly: 需確認RSS可用性
✅ Pragmatic Engineer: 有部分公開文章
❓ 其他電子報: 逐一調查中
```

**實作範例**:
```python
import feedparser

def fetch_rss_content(rss_url):
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries:
        articles.append({
            'title': entry.title,
            'content': entry.summary,
            'link': entry.link,
            'published': entry.published
        })
    return articles
```

**限制**:
- 並非所有電子報都有 RSS
- 內容可能不完整（缺少訂閱者專屬內容）
- 更新頻率可能不一致

## 3. MVP 實施方案

### 3.1 選定方案: 專用收集信箱
基於以上分析，**專用收集信箱方案**最適合 MVP 階段：
- 隱私風險最低
- 實作複雜度最簡單
- 內容獲取最完整
- 擴展性良好

### 3.2 MVP 技術架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   電子報來源    │───▶│    專用收集信箱    │───▶│   內容解析器    │
│ • tl;dr        │    │ user-newsletters  │    │ • HTML解析     │
│ • DL Weekly    │    │ @gmail.com       │    │ • 內容提取     │
│ • Pragmatic    │    │                  │    │ • 格式標準化   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   摘要生成器    │◀───│    內容儲存      │◀───│   內容清理器    │
│ • AI摘要       │    │ • 原始內容       │    │ • 廣告移除     │
│ • 關鍵字提取   │    │ • 處理狀態       │    │ • 格式統一     │
│ • 重點標記     │    │ • 摘要結果       │    │ • 連結處理     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 3.3 實作計劃

#### Phase 1: 基礎設施 (Week 1)
1. **建立專用收集信箱**
   - 創建 `good-morning-newsletters@gmail.com`
   - 設定 Gmail API 或 IMAP 存取權限
   - 實作基礎郵件讀取功能

2. **電子報訂閱**
   - 重新訂閱 tl;dr
   - 重新訂閱 Deep Learning Weekly
   - 重新訂閱 Pragmatic Engineer

#### Phase 2: 內容處理 (Week 2)
1. **郵件解析器開發**
   ```python
   class EmailParser:
       def parse_newsletter(self, email_content):
           # HTML 解析
           # 內容提取
           # 結構化資料輸出
           pass
   ```

2. **內容清理和標準化**
   - 移除廣告內容
   - 統一格式
   - 提取核心文章

#### Phase 3: 摘要生成 (Week 3)
1. **摘要演算法實作**
   - 整合 OpenAI API 或本地模型
   - 設計摘要 prompt
   - 實作批次處理

2. **測試和優化**
   - 測試不同電子報的解析效果
   - 調整摘要品質
   - 效能優化

### 3.4 資料存儲設計

```sql
-- 電子報原始資料表
CREATE TABLE newsletters (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,  -- 'tldr', 'deep_learning_weekly'
    subject VARCHAR(500),
    content TEXT,
    html_content TEXT,
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'  -- 'pending', 'processed', 'failed'
);

-- 摘要結果表
CREATE TABLE newsletter_summaries (
    id SERIAL PRIMARY KEY,
    newsletter_id INTEGER REFERENCES newsletters(id),
    summary TEXT,
    key_points TEXT[],
    original_links TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 4. 擴展階段架構

### 4.1 多用戶支援架構

```python
class MultiUserNewsletterSystem:
    def __init__(self):
        self.user_configs = {}  # 用戶配置
        self.collectors = {}    # 各用戶的收集器
    
    def add_user(self, user_id, newsletter_preferences):
        # 為新用戶創建專用信箱
        dedicated_email = f"user-{user_id}-newsletters@gmail.com"
        self.collectors[user_id] = NewsletterCollector(dedicated_email)
        
        # 根據偏好訂閱電子報
        self._subscribe_newsletters(user_id, newsletter_preferences)
    
    def process_user_newsletters(self, user_id):
        collector = self.collectors[user_id]
        newsletters = collector.fetch_newsletters()
        summaries = self._generate_summaries(newsletters)
        return summaries
```

### 4.2 混合資料源架構

```python
class NewsletterSourceManager:
    def __init__(self):
        self.sources = {
            'email': EmailSource(),
            'rss': RSSSource(),
            'web': WebScrapingSource()
        }
    
    def fetch_content(self, source_config):
        source_type = source_config['type']
        source = self.sources[source_type]
        return source.fetch(source_config)
```

## 5. 風險評估與緩解

### 5.1 技術風險
| 風險 | 影響程度 | 機率 | 緩解措施 |
|------|----------|------|----------|
| Gmail API 限制 | 高 | 中 | 使用多個 API key，實作降級方案 |
| 電子報格式變更 | 中 | 高 | 建立彈性解析器，監控解析失敗 |
| 郵件被標記為垃圾 | 中 | 中 | 定期檢查，手動確認訂閱狀態 |

### 5.2 法律風險
| 風險 | 評估 | 緩解措施 |
|------|------|----------|
| 版權問題 | 低 | 僅提供摘要，保留原文連結 |
| 服務條款違反 | 低 | 使用正常訂閱方式，不進行爬蟲 |
| 隱私法規 | 極低 | 不收集用戶個人資料 |

### 5.3 營運風險
- **擴展性**: 專用信箱方案在大量用戶時的管理複雜度
- **成本**: 多個 Gmail 帳號的管理成本
- **維護**: 電子報訂閱狀態的定期檢查需求

## 6. 結論與建議

### 6.1 MVP 實施建議
1. **立即開始**: 專用收集信箱方案風險低，可立即實施
2. **逐步擴展**: 先支援 3-5 個主要電子報，驗證效果後再擴展
3. **品質優先**: 專注於摘要品質而非資料源數量

### 6.2 長期發展方向
1. **混合架構**: 結合 Email、RSS、Web 多種資料源
2. **用戶自定義**: 允許用戶選擇關注的電子報類型
3. **AI 優化**: 使用機器學習改善摘要品質和個人化

### 6.3 成功指標
- **技術**: 每日成功獲取電子報 > 95%
- **品質**: 摘要準確度和有用性用戶滿意度 > 4/5
- **擴展**: 支援 10+ 電子報，處理時間 < 10分鐘

---

*文檔版本: 1.0*  
*建立日期: 2025-08-02*  
*負責人: Good Morning Agent 開發團隊*