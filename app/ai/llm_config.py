import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# 載入環境變數
load_dotenv()

def get_groq_model(model_name="llama-3.1-8b-instant", temperature=0.7):
    """
    獲取 Groq 模型實例
    
    最新可用的模型 (2025年更新)：
    🦙 Llama 系列（推薦）:
    - llama-3.3-70b-versatile: Llama 3.3 70B (最新最強)
    - llama-3.1-8b-instant: Llama 3.1 8B (快速穩定，推薦)
    - llama3-70b-8192: Llama 3 70B (經典強力)
    - llama3-8b-8192: Llama 3 8B (經典平衡)
    - deepseek-r1-distill-llama-70b: DeepSeek R1 (推理能力強)
    
    🤖 其他優秀選擇:
    - qwen-qwq-32b: Qwen QwQ 32B (中等規模，均衡)
    - mistral-saba-24b: Mistral Saba 24B (快速)
    - gemma2-9b-it: Gemma 2 9B (輕量快速)
    
    🚀 新一代 Llama 4 (實驗性):
    - meta-llama/llama-4-maverick-17b-128e-instruct: Llama 4 Maverick
    - meta-llama/llama-4-scout-17b-16e-instruct: Llama 4 Scout
    """
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not groq_api_key:
            raise ValueError("找不到 GROQ_API_KEY 環境變數，請在 .env 檔案中設定")
        
        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=None,  # 讓模型自動決定
            timeout=None,
            max_retries=2,
        )
        
    except Exception as e:
        print(f"載入 Groq 模型時出錯: {str(e)}")
        print("請確認：")
        print("1. .env 檔案中有設定 GROQ_API_KEY")
        print("2. API Key 是有效的")
        print("3. 已安裝 langchain-groq 套件")
        raise e

def get_fast_model():
    """獲取最快的模型（適合快速回應）"""
    return get_groq_model(model_name="llama-3.1-8b-instant", temperature=0.5)

def get_smart_model():
    """獲取最聰明的模型（適合複雜分析）"""
    return get_groq_model(model_name="llama-3.3-70b-versatile", temperature=0.7)

def get_balanced_model():
    """獲取平衡的模型（速度和性能兼顧）"""
    return get_groq_model(model_name="llama3-8b-8192", temperature=0.6)

def get_reasoning_model():
    """獲取推理能力強的模型（適合邏輯分析）"""
    return get_groq_model(model_name="deepseek-r1-distill-llama-70b", temperature=0.6)

def get_experimental_model():
    """獲取實驗性 Llama 4 模型（最新技術）"""
    return get_groq_model(model_name="meta-llama/llama-4-maverick-17b-128e-instruct", temperature=0.7)

def get_lightweight_model():
    """獲取輕量級模型（節省額度）"""
    return get_groq_model(model_name="gemma2-9b-it", temperature=0.6)

# 測試 Groq 連線
def test_groq_connection():
    """測試 Groq API 連線"""
    try:
        print("正在測試 Groq API 連線...")
        
        # 使用最快的模型進行測試
        llm = get_fast_model()
        
        # 簡單的測試訊息
        test_message = "請回答：1+1等於多少？只需要回答數字。"
        response = llm.invoke(test_message)
        
        print(f"✅ Groq API 連線成功！")
        print(f"測試回應: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Groq API 連線失敗: {str(e)}")
        return False

if __name__ == "__main__":
    # 測試連線
    test_groq_connection()
    
    # 顯示可用模型
    print("\n✨ 2025年最新 Groq 模型推薦:")
    print("🥇 最佳選擇:")
    print("   1. llama-3.1-8b-instant (快速穩定，日常推薦)")
    print("   2. llama-3.3-70b-versatile (最新最強)")
    print("   3. deepseek-r1-distill-llama-70b (推理專家)")
    print("\n🏃 輕量選擇:")
    print("   4. gemma2-9b-it (省額度)")
    print("   5. llama3-8b-8192 (經典穩定)")
    print("\n🧪 實驗性:")
    print("   6. meta-llama/llama-4-maverick-17b-128e-instruct (Llama 4!)")
    print("   7. qwen-qwq-32b (Qwen 推理)")