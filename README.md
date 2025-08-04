# Good Morning Agent 🌅

每天早上自動生成個人化資訊摘要的智能助手，將電子報、天氣、新聞整合成 10 分鐘的深度閱讀體驗。

## 📋 專案概述

Good Morning Agent 是一個隱私優先的個人資訊彙整工具，透過以下方式解決資訊過載問題：

- **📧 電子報深度摘要**：AI 分析你訂閱的電子報，提供 200 字深度解析
- **🌤️ 天氣資訊**：當日天氣狀況和穿衣建議
- **📰 新聞精華**：重要新聞的影響分析，幫助你決定是否深入閱讀
- **📱 手機友善**：自動發送 HTML 郵件，早上起床即可瀏覽

## 🎯 核心特色

### 隱私優先設計
- 使用專用收集信箱，不存取個人郵箱
- 所有資料本地處理，不上傳第三方
- 完全開源，可自主部署

### 深度內容理解
- 不只是標題列表，而是 AI 深度分析的精華摘要
- 提供足夠資訊讓你決定是否閱讀原文
- 預估閱讀時間 10 分鐘，資訊密度高

### 技術簡單可靠
- 本地 Python 腳本，無複雜依賴
- 支援本地運行和雲端部署
- 模組化設計，易於擴展

## 📁 專案結構

```
good-morning-agent/
├── docs/                           # 設計文件
│   ├── PRD.md                      # 產品需求文件
│   ├── newsletter-data-source-design.md  # 資料源設計
│   ├── system-architecture-design.md     # 系統架構設計
│   └── technical-implementation-guide.md # 技術實作指南
├── src/                            # 原始碼（待實作）
│   ├── collectors/                 # 資料收集模組
│   ├── processors/                 # 內容處理模組
│   ├── senders/                    # 郵件發送模組
│   └── utils/                      # 工具函數
├── config/                         # 配置文件（待實作）
├── tests/                          # 測試文件（待實作）
└── README.md                       # 本文件
```

## 🚀 快速開始

### 前置需求

- Python 3.11+
- Gmail 帳號（用於專用收集信箱）
- OpenAI API Key（用於 AI 摘要）

### 安裝步驟

```bash
# 1. 克隆專案
git clone https://github.com/your-username/good-morning-agent.git
cd good-morning-agent

# 2. 安裝依賴（待實作）
pip install -r requirements.txt

# 3. 設置環境變數（待實作）
cp config/.env.example config/.env
# 編輯 .env 文件，填入你的 API keys

# 4. 執行測試（待實作）
python src/main.py --test

# 5. 設置定時任務（待實作）
python scripts/setup_cron.py
```

## 📊 功能實作狀態

### ✅ 已完成
- [x] 需求分析和產品設計
- [x] 技術架構設計
- [x] 資料源獲取方案設計
- [x] 核心技術實作指南

### 🚧 進行中
- [ ] 核心功能實作
- [ ] 測試框架建立

### 📋 待實作
- [ ] IMAP 電子報收集模組
- [ ] AI 摘要生成模組
- [ ] HTML 郵件發送模組
- [ ] 定時任務設定
- [ ] 錯誤處理和監控
- [ ] 用戶配置介面
- [ ] 部署腳本

## 🏗️ 技術架構

### MVP 本地架構
```
定時觸發 → 電子報收集 → 內容解析 → AI 摘要 → 郵件發送
    ↓           ↓           ↓         ↓        ↓
  Cron Job    IMAP     BeautifulSoup  OpenAI   SMTP
```

### 支援的電子報
- **tl;dr** - 科技新聞摘要
- **Deep Learning Weekly** - AI/ML 技術週報  
- **Pragmatic Engineer** - 軟體工程實務
- 更多電子報持續增加中...

## 💰 成本估算

### 本地運行（推薦）
- OpenAI API: ~$10-30/月
- 其他 API: 免費額度內
- 總計: **~$15-40/月**

### 雲端部署（GCP）
- 單用戶: ~$10/月
- 多用戶: ~$0.50/用戶/月

## 🤝 貢獻指南

1. Fork 本專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

## 🙏 致謝

- 感謝所有提供優質電子報的創作者
- 感謝開源社群的技術支持

## 📞 聯絡

如有問題或建議，請：
- 開啟 [Issue](https://github.com/your-username/good-morning-agent/issues)
- 發送郵件至 your-email@example.com

---

⭐ 如果這個專案對你有幫助，請給個 Star！

*讓每個早晨都從優質資訊開始* 🌅