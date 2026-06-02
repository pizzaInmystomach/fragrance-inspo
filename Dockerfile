FROM python:3.13-slim

WORKDIR /app

# 安裝 Tantivy 與 LanceDB 編譯可能需要的基礎系統套件，編譯完後自動清理以縮減映像檔體積
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案所有內容（包含階段三生成的 lancedb_data 目錄）
COPY . .

# 曝露 FastAPI 預設埠
EXPOSE 8000

# 設定預設環境變數，導向 Mac 宿主機的 Ollama 連接埠
ENV OLLAMA_HOST=http://host.docker.internal:11434

# 啟動 Uvicorn 伺服器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]