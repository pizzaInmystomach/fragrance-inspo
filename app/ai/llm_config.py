from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

# 簡單的 Ollama 模型設定
def get_llm(model_name="llama3", temperature=0.7):
    """獲取 Ollama 模型實例"""
    try:
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434"
        )
    except Exception as e:
        print(f"載入模型時出錯: {str(e)}")
        # 使用最基本的模型作為備用
        return ChatOllama(model="llama2", temperature=0.5)

# 預設模型實例
CHARACTER_MODEL = get_llm(model_name="llama2", temperature=0.7)