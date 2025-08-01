#!/usr/bin/env python3
"""
简化的doubao-seed-1.6模型配置测试
"""

import os

def test_doubao_configuration():
    """测试doubao-seed-1.6模型配置"""
    print("🔍 测试doubao-seed-1.6模型配置")
    print("=" * 60)
    
    # 检查环境变量
    ark_api_key = os.getenv("ARK_API_KEY")
    ark_base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    
    print(f"ARK_API_KEY: {'已设置' if ark_api_key else '未设置'}")
    print(f"ARK_BASE_URL: {ark_base_url}")
    
    if not ark_api_key:
        print("⚠️  请设置环境变量ARK_API_KEY")
        print("   例如: export ARK_API_KEY='your-api-key-here'")
        return False
    else:
        print("✅ 环境变量配置正确")
    
    # 检查resource_manager.py中的配置
    print(f"\n📋 检查resource_manager.py配置...")
    
    try:
        with open("app/resource_manager.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否包含doubao-seed-1.6配置
        if "doubao-seed-1.6" in content:
            print("✅ 找到doubao-seed-1.6模型配置")
            
            # 提取配置信息
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "doubao-seed-1.6" in line:
                    print(f"   配置位置: 第{i+1}行")
                    # 显示相关配置行
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if j == i:
                            print(f"   >>> {j+1}: {lines[j]}")
                        else:
                            print(f"      {j+1}: {lines[j]}")
                    break
        else:
            print("❌ 未找到doubao-seed-1.6模型配置")
            return False
            
        # 检查模型ID配置
        if "doubao-seed-1-6-250615" in content:
            print("✅ 模型ID配置正确")
        else:
            print("❌ 模型ID配置错误")
            return False
            
        # 检查API配置
        if "api_version=\"2024-01-01\"" in content:
            print("✅ API版本配置正确")
        else:
            print("❌ API版本配置错误")
            return False
            
        if "is_chat_model=True" in content:
            print("✅ 聊天模型配置正确")
        else:
            print("❌ 聊天模型配置错误")
            return False
            
    except FileNotFoundError:
        print("❌ 未找到app/resource_manager.py文件")
        return False
    except Exception as e:
        print(f"❌ 读取配置文件时出错: {e}")
        return False
    
    print(f"\n✅ doubao-seed-1.6模型配置检查完成")
    print(f"   模型名称: doubao-seed-1.6")
    print(f"   模型ID: doubao-seed-1-6-250615")
    print(f"   API Base: {ark_base_url}")
    print(f"   API Version: 2024-01-01")
    print(f"   Is Chat Model: True")
    
    return True

def show_usage_example():
    """显示使用示例"""
    print(f"\n📖 使用示例")
    print("=" * 60)
    
    print("1. 设置环境变量:")
    print("   export ARK_API_KEY='your-api-key-here'")
    print("   export ARK_BASE_URL='https://ark.cn-beijing.volces.com/api/v3'")
    
    print("\n2. 在API请求中使用:")
    print("   POST /api/v1/workflow/execute")
    print("   {")
    print('     "llm_name": "doubao-seed-1.6",')
    print('     "database_name": "your_database",')
    print('     "workflow_type": "text2cypher_with_1_retry_and_output_check",')
    print('     "input_text": "糖尿病有哪些症状？"')
    print("   }")
    
    print("\n3. 模型特点:")
    print("   - 支持文本对话（不使用图像）")
    print("   - 基于ARK平台")
    print("   - 使用OpenAI兼容的API格式")
    print("   - 支持中文对话")

if __name__ == "__main__":
    success = test_doubao_configuration()
    if success:
        show_usage_example()
    else:
        print("\n❌ 配置检查失败，请检查上述问题") 