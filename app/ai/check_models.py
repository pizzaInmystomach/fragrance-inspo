#!/usr/bin/env python3

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


MODELS = (
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
)


def check_available_models():
    """Test the Gemini models configured for this application."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("找不到 GEMINI_API_KEY 環境變數")
        return []

    working_models = []
    for model_name in MODELS:
        try:
            print(f"測試 {model_name}...", end=" ", flush=True)
            model = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0,
                max_retries=0,
            )
            model.invoke("Reply with only: OK")
            print("可用")
            working_models.append(model_name)
        except Exception as error:
            print(f"不可用: {str(error)[:120]}")

    return working_models


if __name__ == "__main__":
    print("=== Gemini 模型檢查工具 ===")
    available = check_available_models()
    print(f"\n可用模型: {', '.join(available) if available else 'none'}")
