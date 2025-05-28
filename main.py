#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from data_handler import DataHandler
from analyzer import CharacterAnalyzer
import json

def main():
    """主程序示例"""
    print("=== 香水角色匹配系統 ===\n")
    
    # 初始化數據處理器
    print("1. 初始化數據處理器...")
    try:
        data_handler = DataHandler()
        test_result = data_handler.test_connection()
        
        if not test_result["success"]:
            print(f"資料庫連線失敗: {test_result['error']}")
            return
        
        print(f"   ✓ 成功連線資料庫，共有 {test_result['total_count']} 筆香水資料\n")
    except Exception as e:
        print(f"   ✗ 初始化失敗: {e}")
        return
    
    # 初始化角色分析器
    print("2. 初始化角色分析器...")
    try:
        analyzer = CharacterAnalyzer()
        print("   ✓ 分析器初始化成功\n")
    except Exception as e:
        print(f"   ✗ 分析器初始化失敗: {e}")
        return
    
    # 獲取香水資料
    print("3. 獲取香水資料...")
    try:
        # 為了測試，先獲取前10筆資料
        fragrances = data_handler.get_all_fragrances(limit=10)
        if not fragrances:
            print("   ✗ 沒有獲取到香水資料")
            return
        print(f"   ✓ 成功獲取 {len(fragrances)} 筆香水資料\n")
    except Exception as e:
        print(f"   ✗ 獲取香水資料失敗: {e}")
        return
    
    # 角色分析示例
    print("4. 角色分析示例...")
    character_name = "Hermione Granger"
    source_type = "Harry Potter"
    
    try:
        print(f"   分析角色: {character_name} ({source_type})")
        character_analysis = analyzer.analyze_character(character_name, source_type)
        
        print("   角色分析結果:")
        print(f"   - 特質: {', '.join(character_analysis.get('traits', []))}")
        print(f"   - 風格: {', '.join(character_analysis.get('style', []))}")
        print(f"   - 分析: {character_analysis.get('analysis', '')}\n")
        
    except Exception as e:
        print(f"   ✗ 角色分析失敗: {e}")
        return
    
    # 香水匹配示例
    print("5. 香水匹配示例...")
    try:
        print("   正在匹配最適合的香水...")
        match_result = analyzer.match_fragrance(character_analysis, fragrances)
        
        if match_result and match_result.get('fragrance'):
            fragrance = match_result['fragrance']
            rationale = match_result['rationale']
            
            print("   匹配結果:")
            print(f"   - 香水: {fragrance.get('Name', 'Unknown')}")
            print(f"   - 品牌: {fragrance.get('Brand', 'Unknown')}")
            print(f"   - 香調: {', '.join(fragrance.get('Accords', []))}")
            print(f"   - 推薦理由: {rationale}\n")
            
            # 生成描述
            print("6. 生成香水描述...")
            try:
                description = analyzer.generate_description(fragrance)
                print("   香水描述:")
                print(f"   {description}\n")
            except Exception as e:
                print(f"   ✗ 描述生成失敗: {e}")
                
        else:
            print("   ✗ 沒有找到匹配的香水")
            
    except Exception as e:
        print(f"   ✗ 香水匹配失敗: {e}")
    
    # 清理資源
    print("7. 清理資源...")
    try:
        data_handler.close_connection()
        print("   ✓ 資源清理完成")
    except Exception as e:
        print(f"   ✗ 資源清理失敗: {e}")

def test_data_enhancement():
    """測試資料增強功能"""
    print("\n=== 測試資料增強功能 ===\n")
    
    # 模擬你的MongoDB數據結構
    sample_fragrance = {
        "_id": "6828c379444d6f9b6b70f1629",
        "Name": "Far Away Splendoria",
        "Brand": "Avon",
        "Accords": "Floral,Creamy,Oriental,Sweet,Woody",
        "Notes": {
            "Top Notes": "Black plum",
            "Heart Notes": "White oud,White gardenia",
            "Base Notes": "Vanilla"
        }
    }
    
    try:
        analyzer = CharacterAnalyzer()
        enhanced_fragrance = analyzer.enhance_fragrance_data(sample_fragrance)
        
        print("原始資料:")
        print(json.dumps(sample_fragrance, indent=2, ensure_ascii=False))
        
        print("\n增強後資料:")
        print(json.dumps(enhanced_fragrance, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"資料增強測試失敗: {e}")

def interactive_mode():
    """互動模式"""
    print("\n=== 互動模式 ===")
    print("輸入角色名稱來獲取香水推薦，輸入 'quit' 退出\n")
    
    try:
        data_handler = DataHandler()
        analyzer = CharacterAnalyzer()
        fragrances = data_handler.get_all_fragrances(limit=20)  # 獲取20筆用於測試
        
        if not fragrances:
            print("無法獲取香水資料")
            return
            
        while True:
            character_name = input("請輸入角色名稱 (或 'quit' 退出): ").strip()
            
            if character_name.lower() == 'quit':
                break
                
            if not character_name:
                continue
            
            source_type = input("請輸入來源 (可選): ").strip()
            
            print(f"\n正在分析 {character_name}...")
            
            # 分析角色
            character_analysis = analyzer.analyze_character(character_name, source_type)
            
            # 匹配香水
            match_result = analyzer.match_fragrance(character_analysis, fragrances)
            
            if match_result and match_result.get('fragrance'):
                fragrance = match_result['fragrance']
                print(f"\n推薦香水: {fragrance.get('Name')} by {fragrance.get('Brand')}")
                print(f"推薦理由: {match_result['rationale']}")
                
                # 生成描述
                description = analyzer.generate_description(fragrance)
                print(f"\n香水描述:\n{description}\n")
            else:
                print("抱歉，沒有找到合適的香水推薦\n")
        
        data_handler.close_connection()
        print("再見！")
        
    except Exception as e:
        print(f"互動模式出錯: {e}")

if __name__ == "__main__":
    # 運行主程序
    main()
    
    # 測試數據增強
    test_data_enhancement()
    
    # 可選：運行互動模式
    # interactive_mode()