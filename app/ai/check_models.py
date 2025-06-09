#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
檢查 Groq 目前可用的模型
"""

import os
from dotenv import load_dotenv
from groq import Groq

def check_available_models():
    """檢查 Groq 目前可用的模型"""
    load_dotenv()
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ 找不到 GROQ_API_KEY 環境變數")
        return
    
    try:
        client = Groq(api_key=groq_api_key)
        
        print("🔍 正在查詢 Groq 可用模型...")
        
        # 獲取模型列表
        models = client.models.list()
        
        print(f"\n✅ 找到 {len(models.data)} 個可用模型:\n")
        
        # 按類型分組顯示
        llama_models = []
        gemma_models = []
        other_models = []
        
        for model in models.data:
            model_id = model.id
            if "llama" in model_id.lower():
                llama_models.append(model_id)
            elif "gemma" in model_id.lower():
                gemma_models.append(model_id)
            else:
                other_models.append(model_id)
        
        if llama_models:
            print("🦙 Llama 系列模型:")
            for model in sorted(llama_models):
                print(f"   - {model}")
        
        if gemma_models:
            print("\n💎 Gemma 系列模型:")
            for model in sorted(gemma_models):
                print(f"   - {model}")
        
        if other_models:
            print("\n🔧 其他模型:")
            for model in sorted(other_models):
                print(f"   - {model}")
        
        # 推薦模型
        print("\n🎯 推薦模型配置:")
        recommended_models = {
            "快速開發": "llama-3.1-8b-instant",
            "生產環境": "llama-3.1-8b-instant", 
            "最佳品質": "llama-3.1-70b-versatile",
            "輕量選擇": "gemma2-9b-it"
        }
        
        for use_case, model in recommended_models.items():
            available = "✅" if model in [m.id for m in models.data] else "❌"
            print(f"   {use_case}: {model} {available}")
            
        return [model.id for model in models.data]
        
    except Exception as e:
        print(f"❌ 查詢模型失敗: {str(e)}")
        return []

def test_specific_models():
    """測試特定模型是否可用"""
    load_dotenv()
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ 找不到 GROQ_API_KEY 環境變數")
        return
    
    # 要測試的模型列表
    test_models = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile", 
        "gemma2-9b-it",
        "gemma-7b-it",
        "llama3-groq-8b-8192-tool-use-preview",
        "llama3-groq-70b-8192-tool-use-preview"
    ]
    
    try:
        from langchain_groq import ChatGroq
        
        print("\n🧪 測試模型可用性...")
        
        working_models = []
        
        for model_name in test_models:
            try:
                print(f"測試 {model_name}...", end=" ")
                
                llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name=model_name,
                    temperature=0.1,
                    max_tokens=10
                )
                
                response = llm.invoke("Hello")
                print("✅ 可用")
                working_models.append(model_name)
                
            except Exception as e:
                if "decommissioned" in str(e).lower():
                    print("❌ 已停用")
                elif "invalid" in str(e).lower():
                    print("❌ 無效")
                else:
                    print(f"❌ 錯誤: {str(e)[:50]}")
        
        print(f"\n✅ 可用模型總計: {len(working_models)}")
        for model in working_models:
            print(f"   - {model}")
            
        return working_models
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return []

if __name__ == "__main__":
    print("=== Groq 模型檢查工具 ===\n")
    
    # 檢查所有可用模型
    all_models = check_available_models()
    
    # 測試特定模型
    working_models = test_specific_models()
    
    if working_models:
        print(f"\n🎉 建議更新 llm_config.py 使用以下模型:")
        print(f"   預設模型: {working_models[0]}")
        print(f"   高級模型: {working_models[-1] if len(working_models) > 1 else working_models[0]}")
    else:
        print("\n⚠️  沒有找到可用的模型，請檢查 API Key 或聯繫 Groq 支援")