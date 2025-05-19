# Fragrance Inspo 香氣靈感

Fragrance Inspo 是一個創新的香水推薦應用，基於角色分析來推薦香水。使用者可以輸入任何角色名稱（名人、影視作品角色、二次元角色等），系統會分析該角色的個性特點，然後推薦與之匹配的香水。

## 特色功能

- 根據角色個性分析推薦香水
- 提供香水的詳細資訊（前調、中調、後調、主要香調）
- 解釋推薦原因，連結角色特質與香水特點
- 描述香水的氛圍感受
- 保存搜尋歷史，方便重複查詢

## 技術架構

- **後端**：Python Flask API
- **AI 模型**：使用 Ollama 與 LangChain 進行角色分析與香水推薦
- **資料庫**：MongoDB 儲存角色與推薦結果
- **前端**：HTML, CSS, JavaScript
- **部署**：GitHub Pages

## 安裝與設置

### 前提條件

- Python 3.8+
- MongoDB
- Node.js (用於後續部署)
- Ollama

### 後端設置

1. 複製專案
```bash
git clone https://github.com/yourusername/fragrance-inspo.git
cd fragrance-inspo
```

2. 安裝依賴
```bash
pip install -r requirements.txt
```

3. 設定環境變數（可選，或直接修改 config.py）
```bash
export MONGO_URI="mongodb://localhost:27017/"
export DB_NAME="fragrance_inspo"
export OLLAMA_HOST="http://localhost:11434"
export OLLAMA_MODEL="llama3"
```

4. 啟動後端
```bash
cd backend
python app.py
```

現在後端應該已經在 http://localhost:5000 上運行。

### 前端設置

前端是靜態檔案，可以直接從檔案系統打開，或是使用簡單的 HTTP 伺服器：

```bash
cd frontend
python -m http.server
```

然後訪問 http://localhost:8000

## 部署到 GitHub Pages

1. 創建一個新的 GitHub 倉庫

2. 在 `frontend/js/api.js` 中更新 API URL 為你的後端服務地址

3. 將前端檔案推送到 GitHub 倉庫

4. 在倉庫設定中啟用 GitHub Pages，選擇主分支作為來源

## 後端部署建議

後端可以部署到多種雲端服務：

- **Heroku**：適合小型應用
- **Render**：提供免費方案
- **AWS Lambda**：無伺服器架構
- **Google Cloud Run**：容器化部署

記得更新 MongoDB 連接字串，以及確保 Ollama 服務可用。

## 使用方法

1. 訪問網站首頁
2. 在搜尋框中輸入角色名稱
3. 點擊「尋找香氣」按鈕
4. 等待系統分析並生成推薦
5. 瀏覽角色分析與推薦的香水
6. 查看之前的搜尋歷史，一鍵重新搜尋

## 貢獻指南

歡迎貢獻！如果你想改進這個專案，請遵循以下步驟：

1. Fork 這個專案
2. 創建你的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的改動 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開一個 Pull Request

## 授權

MIT 授權 - 詳見 LICENSE 檔案

## 連絡方式

有問題或建議？請開一個 issue 或聯絡專案維護者。

---

*這個專案是使用 AI 技術來尋找你的香氣靈感，幫助你找到與喜愛角色相符的香水。*