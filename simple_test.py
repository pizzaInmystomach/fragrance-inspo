#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試智能輸入解析功能
"""

import sys
import os

# 添加路徑以便導入模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.ai.analyzer import CharacterAnalyzer
    from app.data_handler import DataHandler
    print("✅ 成功導入模組")
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確認你在正確的目錄中運行此腳本")
    sys.exit(1)

def test_input_parsing():
    """測試各種輸入情況"""
    
    analyzer = CharacterAnalyzer()
    
    # 測試案例
    test_cases = [
        # 成功案例
        "I want to smell like Harry Potter",
        "Hermione Granger",
        "What fragrance would Daisy Buchanan wear?",
        "Find me a perfume for James Bond",
        "妙麗",
        "哈利波特",
        
        # 需要澄清的案例
        "Someone brave",
        "A smart character",
        "I want to smell like someone intelligent",
        "Find me a perfume for a mysterious person",
        
        # 無關內容
        "Hello",
        "Have a nice day",
        "Thank you",
        "How are you?",
        "Good morning",
        
        # 邊界案例
        "smell like",
        "Batman",  # 不在預設列表中的角色
        "Elizabeth Bennet",  # 經典文學角色
        "Ron",  # 簡短名字
    ]
    
    print("=== 智能輸入解析測試 ===\n")
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"測試 {i}: '{test_input}'")
        print("-" * 50)
        
        try:
            result = analyzer.parse_user_input(test_input)
            
            if result:
                print(f"狀態: {result.get('status')}")
                print(f"角色名稱: {result.get('character_name')}")
                print(f"來源: {result.get('source')}")
                print(f"意圖: {result.get('intent')}")
                print(f"回應訊息: {result.get('message')}")
                
                # 如果成功識別角色，測試完整流程
                if result.get('status') == 'success' and result.get('character_name'):
                    print(f"\n✅ 成功識別角色，測試完整分析流程...")
                    character_analysis = analyzer.analyze_character(
                        result['character_name'], 
                        result.get('source', '')
                    )
                    print(f"角色特質: {character_analysis.get('traits', [])[:3]}")
                    print(f"風格: {character_analysis.get('style', [])}")
                
            else:
                print("❌ 解析失敗")
                
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
        
        print("\n" + "="*60 + "\n")

def test_complete_smart_flow():
    """測試完整的智能推薦流程"""
    print("=== 完整智能推薦流程測試 ===\n")
    
    try:
        # 初始化
        analyzer = CharacterAnalyzer()
        data_handler = DataHandler()
        
        # 測試資料庫連線
        test_result = data_handler.test_connection()
        if not test_result["success"]:
            print(f"資料庫連線失敗: {test_result['error']}")
            return
        
        # 獲取香水資料
        fragrances = data_handler.get_all_fragrances(limit=10)
        if not fragrances:
            print("無法獲取香水資料")
            return
        
        print(f"已獲取 {len(fragrances)} 筆香水資料\n")
        
        # 測試不同的輸入
        test_inputs = [
            "I want to smell like Hermione Granger",
            "Harry Potter",
            "Hello there",
            "Someone mysterious"
        ]
        
        for test_input in test_inputs:
            print(f"🔍 測試輸入: '{test_input}'")
            print("-" * 40)
            
            # 第1步：解析輸入
            parse_result = analyzer.parse_user_input(test_input)
            
            if not parse_result:
                print("❌ 輸入解析失敗")
                continue
            
            print(f"解析狀態: {parse_result.get('status')}")
            print(f"回應訊息: {parse_result.get('message')}")
            
            # 如果需要澄清或無效，跳過
            if parse_result.get('status') != 'success':
                print("⚠️ 需要更多資訊，跳過推薦流程\n")
                continue
            
            character_name = parse_result.get('character_name')
            source = parse_result.get('source', '')
            
            print(f"識別角色: {character_name}")
            print(f"來源: {source}")
            
            # 第2步：角色分析
            character_analysis = analyzer.analyze_character(character_name, source)
            print(f"角色特質: {character_analysis.get('traits', [])}")
            print(f"風格: {character_analysis.get('style', [])}")
            
            # 第3步：香水匹配
            match_result = analyzer.match_fragrances(
                character_analysis, 
                fragrances, 
                num_recommendations=3
            )
            
            if match_result and match_result.get("recommendations"):
                recommendations = match_result["recommendations"]
                print(f"\n🌹 為 {character_name} 推薦的香水:")
                
                for rec in recommendations:
                    fragrance = rec["fragrance"]
                    print(f"  • {fragrance.get('Name')} by {fragrance.get('Brand')}")
                    print(f"    理由: {rec['rationale'][:80]}...")
            else:
                print("❌ 未能生成推薦")
            
            print("\n" + "="*50 + "\n")
        
        # 關閉連線
        data_handler.close_connection()
        print("✅ 測試完成")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")

def test_api_simulation():
    """模擬 API 請求測試"""
    print("=== API 模擬測試 ===\n")
    
    # 模擬前端可能發送的請求
    api_test_cases = [
        {
            "user_input": "I want to smell like Harry Potter",
            "expected_status": "success",
            "description": "完整的角色請求"
        },
        {
            "user_input": "Hermione",
            "expected_status": "success", 
            "description": "簡短角色名"
        },
        {
            "user_input": "Hello",
            "expected_status": "invalid",
            "description": "問候語"
        },
        {
            "user_input": "Someone brave",
            "expected_status": "need_clarification",
            "description": "模糊描述"
        }
    ]
    
    analyzer = CharacterAnalyzer()
    
    for i, test_case in enumerate(api_test_cases, 1):
        print(f"API 測試 {i}: {test_case['description']}")
        print(f"輸入: '{test_case['user_input']}'")
        print(f"期望狀態: {test_case['expected_status']}")
        print("-" * 40)
        
        try:
            # 模擬 /api/parse-input 端點
            result = analyzer.parse_user_input(test_case['user_input'])
            
            if result:
                actual_status = result.get('status')
                print(f"實際狀態: {actual_status}")
                print(f"回應訊息: {result.get('message')}")
                
                # 檢查是否符合期望
                if actual_status == test_case['expected_status']:
                    print("✅ 測試通過")
                else:
                    print(f"⚠️ 狀態不符期望 (期望: {test_case['expected_status']}, 實際: {actual_status})")
                
                # 如果成功，模擬完整推薦流程
                if actual_status == "success":
                    print("\n📝 模擬完整推薦 API 回應格式:")
                    mock_response = {
                        "success": True,
                        "character_name": result.get('character_name'),
                        "character_analysis": {
                            "traits": ["brave", "loyal", "determined"],
                            "style": ["bold", "confident"],
                            "analysis": "角色分析描述"
                        },
                        "recommendations": [
                            {
                                "rank": 1,
                                "fragrance": {
                                    "name": "範例香水",
                                    "brand": "範例品牌"
                                },
                                "rationale": "推薦理由",
                                "match_score": 5
                            }
                        ],
                        "message": f"Found 3 perfect fragrance matches for {result.get('character_name')}!"
                    }
                    print(f"  角色: {mock_response['character_name']}")
                    print(f"  成功: {mock_response['success']}")
                    print(f"  推薦數量: {len(mock_response['recommendations'])}")
                    print(f"  訊息: {mock_response['message']}")
            else:
                print("❌ 解析失敗")
                
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
        
        print("\n" + "="*50 + "\n")

def main():
    """主測試函數"""
    print("開始測試智能輸入解析功能...\n")
    
    # 基本輸入解析測試
    test_input_parsing()
    
    # 完整流程測試
    test_complete_smart_flow()
    
    # API 模擬測試
    test_api_simulation()
    
    print("🎉 所有測試完成！")

if __name__ == "__main__":
    main()