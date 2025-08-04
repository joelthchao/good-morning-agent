# Good Morning Agent 關鍵技術實作指南

## 系統架構概覽
根據前面的設計文件，系統有 4 個關鍵節點：
1. **Email 讀取** - 從專用信箱收集電子報
2. **內容處理** - 解析、清理、結構化資料
3. **AI 摘要生成** - 呼叫 AI 服務產生深度摘要
4. **Email 發送** - 將摘要推送給用戶

---

## 1. Email 讀取技術細節

### 1.1 IMAP 連接與認證

**使用專用收集信箱方案**，避免隱私風險：

```python
import imaplib
import email
from email.header import decode_header
import os
from typing import List, Dict

class NewsletterCollector:
    def __init__(self):
        self.imap_server = "imap.gmail.com"
        self.email = os.getenv("NEWSLETTER_EMAIL")  # good-morning-newsletters@gmail.com
        self.password = os.getenv("NEWSLETTER_APP_PASSWORD")  # Gmail App 專用密碼
        self.mail = None
    
    def connect(self):
        """建立 IMAP 連接"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email, self.password)
            print(f"✅ 成功連接到 {self.email}")
            return True
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
            return False
    
    def get_newsletters_from_today(self) -> List[Dict]:
        """獲取今日電子報"""
        if not self.mail:
            if not self.connect():
                return []
        
        # 選擇收件匣
        self.mail.select("inbox")
        
        # 搜尋今日郵件
        import datetime
        today = datetime.date.today().strftime("%d-b-%Y")  # 格式: 02-Aug-2025
        
        # 搜尋特定寄件者的今日郵件
        search_criteria = f'(SINCE "{today}" FROM "newsletter@tldr.tech")'
        status, messages = self.mail.search(None, search_criteria)
        
        newsletters = []
        if status == "OK":
            for msg_id in messages[0].split():
                newsletter = self._parse_email(msg_id)
                if newsletter:
                    newsletters.append(newsletter)
        
        return newsletters
    
    def _parse_email(self, msg_id) -> Dict:
        """解析單封郵件"""
        try:
            # 獲取郵件內容
            status, msg_data = self.mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                return None
            
            # 解析郵件
            email_msg = email.message_from_bytes(msg_data[0][1])
            
            # 提取基本資訊
            subject = self._decode_header(email_msg["Subject"])
            sender = email_msg["From"]
            date = email_msg["Date"]
            
            # 提取郵件內容
            content = self._extract_content(email_msg)
            
            return {
                "id": msg_id.decode(),
                "subject": subject,
                "sender": sender,
                "date": date,
                "content": content,
                "source": self._identify_newsletter_source(sender)
            }
            
        except Exception as e:
            print(f"❌ 解析郵件失敗: {e}")
            return None
    
    def _decode_header(self, header):
        """解碼郵件標題"""
        if header:
            decoded = decode_header(header)[0]
            if isinstance(decoded[0], bytes):
                return decoded[0].decode(decoded[1] or 'utf-8')
            return decoded[0]
        return ""
    
    def _extract_content(self, email_msg):
        """提取郵件內容"""
        content = {"text": "", "html": ""}
        
        if email_msg.is_multipart():
            for part in email_msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    content["text"] = part.get_payload(decode=True).decode()
                elif content_type == "text/html":
                    content["html"] = part.get_payload(decode=True).decode()
        else:
            if email_msg.get_content_type() == "text/html":
                content["html"] = email_msg.get_payload(decode=True).decode()
            else:
                content["text"] = email_msg.get_payload(decode=True).decode()
        
        return content
    
    def _identify_newsletter_source(self, sender) -> str:
        """識別電子報來源"""
        source_map = {
            "newsletter@tldr.tech": "tldr",
            "noreply@deeplearningweekly.com": "deep_learning_weekly",
            "newsletter@pragmatic-engineer.com": "pragmatic_engineer"
        }
        
        for email_pattern, source in source_map.items():
            if email_pattern in sender:
                return source
        
        return "unknown"
```

### 1.2 關鍵實作要點

**Gmail App 密碼設定**：
1. Gmail 帳號 → 安全性 → 兩步驟驗證
2. 生成「應用程式密碼」用於 IMAP 存取
3. 避免使用主密碼，提高安全性

**錯誤處理**：
```python
def safe_email_operation(self, operation):
    """安全的郵件操作包裝器"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return operation()
        except imaplib.IMAP4.abort:
            print(f"📧 IMAP 連接中斷，重試 {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)  # 指數退避
            self.connect()
        except Exception as e:
            print(f"❌ 郵件操作失敗: {e}")
            if attempt == max_retries - 1:
                raise
```

---

## 2. Email 發送技術細節

### 2.1 SMTP 發送設定

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
import os

class EmailSender:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.getenv("SENDER_EMAIL")  # 發送者郵箱
        self.password = os.getenv("SENDER_APP_PASSWORD")
    
    def send_morning_digest(self, recipient: str, digest_data: Dict):
        """發送晨間摘要"""
        try:
            # 建立 SMTP 連接
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # 啟用 TLS 加密
            server.login(self.email, self.password)
            
            # 創建郵件
            msg = self._create_email_message(recipient, digest_data)
            
            # 發送郵件
            server.send_message(msg)
            server.quit()
            
            print(f"✅ 成功發送摘要給 {recipient}")
            return True
            
        except Exception as e:
            print(f"❌ 郵件發送失敗: {e}")
            return False
    
    def _create_email_message(self, recipient: str, digest_data: Dict) -> MIMEMultipart:
        """創建郵件內容"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🌅 Good Morning! {digest_data['date']}"
        msg["From"] = self.email
        msg["To"] = recipient
        
        # 生成 HTML 內容
        html_content = self._generate_html_content(digest_data)
        
        # 生成純文字內容（降級方案）
        text_content = self._generate_text_content(digest_data)
        
        # 添加到郵件
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        return msg
    
    def _generate_html_content(self, digest_data: Dict) -> str:
        """生成 HTML 郵件內容"""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Good Morning Digest</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }
                .header { background: #f8f9fa; padding: 20px; text-align: center; }
                .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
                .newsletter-item { margin: 15px 0; padding: 10px; background: #f8f9fa; }
                .read-time { color: #6c757d; font-size: 0.9em; }
                .link { color: #007bff; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌅 Good Morning!</h1>
                <p>{{ date }}</p>
            </div>
            
            <div class="section">
                <h2>📧 電子報精華</h2>
                {% for newsletter in newsletters %}
                <div class="newsletter-item">
                    <h3>{{ newsletter.source_name }}</h3>
                    <p>{{ newsletter.summary }}</p>
                    <a href="{{ newsletter.original_link }}" class="link">閱讀原文 →</a>
                </div>
                {% endfor %}
            </div>
            
            <div class="section">
                <h2>🌤️ 今日天氣</h2>
                <p>{{ weather.description }}, {{ weather.temperature }}°C</p>
            </div>
            
            <div class="section">
                <h2>📰 新聞速覽</h2>
                {% for news in news_items %}
                <div class="newsletter-item">
                    <h4>{{ news.title }}</h4>
                    <p>{{ news.summary }}</p>
                    <a href="{{ news.link }}" class="link">了解更多 →</a>
                </div>
                {% endfor %}
            </div>
            
            <div class="footer">
                <p class="read-time">💡 預估閱讀時間：{{ estimated_read_time }} 分鐘</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(**digest_data)
```

### 2.2 關鍵發送要點

**避免被標記為垃圾郵件**：
```python
def setup_email_headers(self, msg: MIMEMultipart):
    """設定防垃圾郵件標頭"""
    msg["X-Mailer"] = "Good Morning Agent v1.0"
    msg["X-Priority"] = "3"  # 正常優先級
    msg["Reply-To"] = self.email
    
    # SPF/DKIM 設定（需要在 DNS 設定）
    # 使用 Gmail SMTP 會自動處理部分設定
```

**發送頻率控制**：
```python
import time
import random

def send_with_rate_limit(self, recipients: List[str], digest_data: Dict):
    """限制發送頻率避免被封鎖"""
    for recipient in recipients:
        self.send_morning_digest(recipient, digest_data)
        # 隨機延遲 1-3 秒，模擬人工發送
        time.sleep(random.uniform(1, 3))
```

---

## 3. AI Agent 整合技術細節

### 3.1 OpenAI API 整合

```python
import openai
from typing import List, Dict
import json

class AIContentSummarizer:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"  # 或 "gpt-3.5-turbo" 節省成本
        
    def summarize_newsletters(self, newsletters: List[Dict]) -> List[Dict]:
        """對電子報進行深度摘要"""
        summaries = []
        
        for newsletter in newsletters:
            try:
                summary = self._generate_newsletter_summary(newsletter)
                summaries.append({
                    "source": newsletter["source"],
                    "source_name": self._get_source_display_name(newsletter["source"]),
                    "summary": summary["summary"],
                    "key_points": summary["key_points"],
                    "original_link": summary.get("original_link", ""),
                    "importance_score": summary.get("importance_score", 3)
                })
            except Exception as e:
                print(f"❌ 摘要生成失敗 {newsletter['source']}: {e}")
                # 降級方案：使用原始內容
                summaries.append(self._create_fallback_summary(newsletter))
        
        return summaries
    
    def _generate_newsletter_summary(self, newsletter: Dict) -> Dict:
        """為單個電子報生成摘要"""
        
        # 提取 HTML 內容的純文字
        content = self._extract_text_from_html(newsletter["content"]["html"])
        
        prompt = f"""
        請為以下電子報內容生成深度摘要，重點關注：
        1. 核心觀點和重要趨勢
        2. 對讀者的實際影響
        3. 可採取的行動建議
        
        電子報來源：{newsletter["source"]}
        標題：{newsletter["subject"]}
        內容：{content[:3000]}  # 限制長度避免超過 token 限制
        
        請以 JSON 格式回覆：
        {{
            "summary": "200字以內的深度摘要，解釋為什麼這個內容重要",
            "key_points": ["重點1", "重點2", "重點3"],
            "importance_score": 1-5的重要性評分,
            "original_link": "如果能從內容中提取到原文連結的話"
        }}
        """
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一個專業的資訊摘要專家，專長於將複雜的電子報內容轉化為易懂的深度分析。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 降低隨機性，提高一致性
            max_tokens=500
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # 如果 AI 沒有返回有效 JSON，手動解析
            return self._parse_ai_response(response.choices[0].message.content)
    
    def _extract_text_from_html(self, html: str) -> str:
        """從 HTML 提取純文字"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除不需要的元素
        for element in soup(['script', 'style', 'nav', 'footer', 'ads']):
            element.decompose()
        
        # 提取純文字
        text = soup.get_text()
        
        # 清理文字
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def generate_weather_context(self, weather_data: Dict) -> str:
        """為天氣資訊生成友善的描述"""
        prompt = f"""
        請將以下天氣資訊轉換為親切、實用的天氣提醒：
        
        溫度：{weather_data.get('temperature', 'N/A')}°C
        天氣狀況：{weather_data.get('description', 'N/A')}
        降雨機率：{weather_data.get('rain_probability', 'N/A')}%
        
        請生成一段50字以內的友善提醒，包含穿衣建議或外出建議。
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # 簡單任務使用便宜的模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=100
        )
        
        return response.choices[0].message.content
```

### 3.2 成本控制與優化

```python
class CostOptimizedAI:
    def __init__(self):
        self.daily_token_limit = 10000  # 每日 token 限制
        self.current_usage = 0
        
    def check_usage_limit(self) -> bool:
        """檢查使用量限制"""
        return self.current_usage < self.daily_token_limit
    
    def estimate_tokens(self, text: str) -> int:
        """估算文字的 token 數量"""
        # 粗略估算：1 token ≈ 4 個字元（英文）或 1.5 個中文字
        return len(text) // 3
    
    def batch_summarize(self, newsletters: List[Dict]) -> List[Dict]:
        """批次處理以減少 API 調用次數"""
        if not self.check_usage_limit():
            print("⚠️ 已達每日 AI 使用限制，使用降級方案")
            return [self._create_fallback_summary(n) for n in newsletters]
        
        # 將多個短的電子報合併處理
        batch_prompt = self._create_batch_prompt(newsletters)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # 使用較便宜的模型
                messages=[{"role": "user", "content": batch_prompt}],
                temperature=0.3
            )
            
            return self._parse_batch_response(response.choices[0].message.content)
            
        except Exception as e:
            print(f"❌ 批次 AI 處理失敗: {e}")
            return [self._create_fallback_summary(n) for n in newsletters]
```

---

## 4. 關鍵技術決策總結

### 4.1 本地 MVP 技術棧確認

```python
# requirements.txt
imaplib3==0.9.3      # 改良版 IMAP 客戶端
beautifulsoup4==4.12.2  # HTML 解析
jinja2==3.1.2        # 郵件模板
openai==0.28.1       # AI 摘要
requests==2.31.0     # API 調用
schedule==1.2.0      # 定時任務
python-dotenv==1.0.0 # 環境變數管理
sqlite3              # 內建資料庫
```

### 4.2 關鍵配置檔案

**.env 範例**：
```env
# 電子報收集信箱
NEWSLETTER_EMAIL=good-morning-newsletters@gmail.com
NEWSLETTER_APP_PASSWORD=your_16_digit_app_password

# 發送信箱
SENDER_EMAIL=your_personal_email@gmail.com
SENDER_APP_PASSWORD=your_sender_app_password

# AI 服務
OPENAI_API_KEY=sk-your_openai_key

# 其他 API
WEATHER_API_KEY=your_weather_api_key
NEWS_API_KEY=your_news_api_key

# 系統設定
RECIPIENT_EMAIL=your_email@gmail.com
DAILY_RUN_TIME=07:00
TIMEZONE=Asia/Taipei
```

### 4.3 資料流程確認

```
1. 定時觸發 (7:00 AM)
   ↓
2. 連接專用信箱 (IMAP)
   ↓
3. 收集今日電子報 + 天氣 + 新聞
   ↓
4. 內容解析與清理 (BeautifulSoup)
   ↓
5. AI 深度摘要生成 (OpenAI)
   ↓
6. HTML 郵件格式化 (Jinja2)
   ↓
7. 發送摘要郵件 (SMTP)
   ↓
8. 記錄執行狀態 (SQLite)
```

---

## 5. 立即可執行的第一步

**建議先實作一個最簡單的版本測試這些關鍵節點**：

1. **測試 IMAP 連接**：確認能讀取專用信箱
2. **測試 SMTP 發送**：確認能發送基本郵件
3. **測試 AI 摘要**：確認 OpenAI API 能正常工作
4. **整合測試**：端到端的基本流程

這樣你就能驗證所有關鍵技術點都能正常工作，然後再逐步完善功能。

**你想從哪個技術節點開始實作？建議先測試 Email 讀取，因為這是資料源的基礎。**

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Review \u73fe\u6709\u8a2d\u8a08\u6587\u4ef6\u7684\u95dc\u9375\u7bc0\u9ede", "status": "completed", "priority": "high"}, {"id": "2", "content": "\u6df1\u5165\u5206\u6790 Email \u8b80\u53d6\u6280\u8853\u7d30\u7bc0", "status": "completed", "priority": "high"}, {"id": "3", "content": "\u6df1\u5165\u5206\u6790 Email \u767c\u9001\u6280\u8853\u7d30\u7bc0", "status": "completed", "priority": "high"}, {"id": "4", "content": "\u6df1\u5165\u5206\u6790 AI Agent \u6574\u5408\u65b9\u5f0f", "status": "completed", "priority": "high"}, {"id": "5", "content": "\u6574\u7406\u95dc\u9375\u6280\u8853\u5be6\u4f5c\u8981\u9ede", "status": "completed", "priority": "high"}]