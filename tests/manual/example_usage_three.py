#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
三個香水推薦系統使用範例
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.data_handler import DataHandler
from app.ai.analyzer import CharacterAnalyzer
import json

def test_three_recommendations():
    """測試三個香水推薦功能"""
    print("=== 三個香水推薦測試 ===\n")
    
    try:
        # 初始化
        data_handler = DataHandler()
        analyzer = CharacterAnalyzer()
        
        # 測試資料庫連線
        test_result = data_handler.test_connection()
        if not test_result["success"]:
            print(f"資料庫連線失敗: {test_result['error']}")
            return
        
        # 獲取香水資料
        fragrances = data_handler.get_all_fragrances(limit=20)  # 測試用，取20筆
        if not fragrances:
            print("無法獲取香水資料")
            return
        
        print(f"已獲取 {len(fragrances)} 筆香水資料\n")
        
        # 測試不同角色
        test_characters = [
            {"name": "妙麗·格蘭傑", "source": "哈利波特"},
            {"name": "黛西·布坎南", "source": "大亨小傳"},
            {"name": "奧黛麗·赫本", "source": "影星"}
        ]
        
        for char in test_characters:
            print(f"🎭 分析角色: {char['name']} ({char['source']})")
            print("-" * 50)
            
            # 角色分析
            character_analysis = analyzer.analyze_character(char['name'], char['source'])
            
            print(f"個性特質: {', '.join(character_analysis.get('traits', []))}")
            print(f"風格特色: {', '.join(character_analysis.get('style', []))}")
            print(f"角色分析: {character_analysis.get('analysis', '')}\n")
            
            # 獲取三個香水推薦
            match_result = analyzer.match_fragrances(character_analysis, fragrances, num_recommendations=3)
            
            if match_result and match_result.get("recommendations"):
                recommendations = match_result["recommendations"]
                
                print(f"🌹 為 {char['name']} 推薦的三款香水:")
                print("=" * 60)
                
                for i, rec in enumerate(recommendations, 1):
                    fragrance = rec["fragrance"]
                    print(f"\n【第 {rec['rank']} 名推薦】")
                    print(f"香水名稱: {fragrance.get('Name', 'Unknown')}")
                    print(f"品牌: {fragrance.get('Brand', 'Unknown')}")
                    print(f"主要香調: {', '.join(fragrance.get('Accords', []))}")
                    print(f"推薦理由: {rec['rationale']}")
                    
                    if rec.get('match_score') is not None:
                        print(f"匹配分數: {rec['match_score']}")
                    
                    # 生成香水描述
                    description = analyzer.generate_description(fragrance)
                    print(f"香水描述: {description}")
                    
                    print("-" * 40)
            else:
                print(f"❌ 未能為 {char['name']} 找到合適的香水推薦")
            
            print("\n" + "=" * 80 + "\n")
        
        # 關閉連線
        data_handler.close_connection()
        print("✅ 測試完成")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")

def test_api_format():
    """測試 API 回傳格式"""
    print("\n=== API 格式測試 ===\n")
    
    try:
        data_handler = DataHandler()
        analyzer = CharacterAnalyzer()
        
        fragrances = data_handler.get_all_fragrances(limit=10)
        character_analysis = analyzer.analyze_character("安娜·卡列尼娜", "小說")
        match_result = analyzer.match_fragrances(character_analysis, fragrances, num_recommendations=3)
        
        # 模擬 API 回傳格式
        api_response = {
            "character": {
                "name": "安娜·卡列尼娜",
                "source": "小說",
                **character_analysis
            },
            "recommendations": [],
            "total_recommendations": 0
        }
        
        if match_result and match_result.get("recommendations"):
            for rec in match_result["recommendations"]:
                fragrance = rec["fragrance"]
                description = analyzer.generate_description(fragrance)
                
                recommendation = {
                    "rank": rec["rank"],
                    "fragrance": {
                        "id": fragrance.get("id"),
                        "name": fragrance.get("Name"),
                        "brand": fragrance.get("Brand"),
                        "accords": fragrance.get("Accords", []),
                        "top_notes": fragrance.get("top_notes", []),
                        "heart_notes": fragrance.get("heart_notes", []),
                        "base_notes": fragrance.get("base_notes", []),
                        "additional_traits": fragrance.get("additional_traits", []),
                        "personality_match": fragrance.get("personality_match", []),
                        "mood_description": fragrance.get("mood_description", ""),
                        "season_suitability": fragrance.get("season_suitability", []),
                        "time_of_day": fragrance.get("time_of_day", [])
                    },
                    "rationale": rec["rationale"],
                    "description": description,
                    "match_score": rec.get("match_score", 0)
                }
                api_response["recommendations"].append(recommendation)
            
            api_response["total_recommendations"] = len(api_response["recommendations"])
        
        print("API 回傳格式範例:")
        print(json.dumps(api_response, indent=2, ensure_ascii=False))
        
        data_handler.close_connection()
        
    except Exception as e:
        print(f"❌ API 格式測試失敗: {str(e)}")

if __name__ == "__main__":
    # 執行測試
    test_three_recommendations()
    test_api_format()
