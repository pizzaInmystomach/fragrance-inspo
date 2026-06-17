import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer, got: {value}") from error


def get_gemini_model(model_name=None, temperature=0.7, max_tokens=None):
    """Create a Gemini chat model using the Google AI Studio API."""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError(
            "找不到 GEMINI_API_KEY 環境變數，請在 .env 檔案中設定"
        )

    selected_model = model_name or os.getenv(
        "GEMINI_BALANCED_MODEL", "gemini-2.5-flash"
    )

    try:
        return ChatGoogleGenerativeAI(
            model=selected_model,
            google_api_key=gemini_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=120,
            max_retries=2,
        )
    except Exception as error:
        print(f"載入 Gemini 模型時出錯: {error}")
        print("請確認：")
        print("1. .env 檔案中有設定 GEMINI_API_KEY")
        print("2. API Key 是有效的")
        print("3. 已安裝 langchain-google-genai 套件")
        raise


def get_fast_model():
    """Return the low-latency model used for lightweight parsing."""
    return get_gemini_model(
        model_name=os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash-lite"),
        temperature=0.5,
        max_tokens=_env_int("GEMINI_FAST_MAX_TOKENS", 300),
    )


def get_smart_model():
    """Return the higher-quality model used for complex analysis."""
    return get_gemini_model(
        model_name=os.getenv("GEMINI_SMART_MODEL", "gemini-2.5-pro"),
        temperature=0.7,
        max_tokens=_env_int("GEMINI_SMART_MAX_TOKENS", 500),
    )


def get_balanced_model():
    """Return the default price-performance model."""
    return get_gemini_model(
        model_name=os.getenv("GEMINI_BALANCED_MODEL", "gemini-2.5-flash"),
        temperature=0.6,
        max_tokens=_env_int("GEMINI_BALANCED_MAX_TOKENS", 400),
    )


def get_reasoning_model():
    return get_smart_model()


def get_experimental_model():
    return get_gemini_model(
        model_name=os.getenv("GEMINI_EXPERIMENTAL_MODEL", "gemini-3-flash-preview"),
        temperature=0.7,
        max_tokens=_env_int("GEMINI_EXPERIMENTAL_MAX_TOKENS", 600),
    )


def get_lightweight_model():
    return get_fast_model()


def test_gemini_connection():
    """Make a minimal request to verify the configured Gemini credentials."""
    try:
        print("正在測試 Gemini API 連線...")
        response = get_fast_model().invoke("Reply with only the number: 1+1")
        print("Gemini API 連線成功")
        print(f"測試回應: {response.content}")
        return True
    except Exception as error:
        print(f"Gemini API 連線失敗: {error}")
        return False


if __name__ == "__main__":
    test_gemini_connection()
