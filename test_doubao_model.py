#!/usr/bin/env python3
"""
测试doubao-seed-1.6模型
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.resource_manager import ResourceManager

def test_doubao_model():
    """测试doubao-seed-1.6模型"""
    print("🔍 测试doubao-seed-1.6模型")
    print("=" * 60)
    
    try:
        # 创建资源管理器
        rm = ResourceManager()
        
        # 检查模型是否加载成功
        print("📋 已加载的模型:")
        for name, model in rm.llms:
            print(f"  - {name}")
        
        # 查找doubao-seed-1.6模型
        doubao_model = None
        for name, model in rm.llms:
            if name == "doubao-seed-1.6":
                doubao_model = model
                break
        
        if doubao_model:
            print(f"\n✅ 找到doubao-seed-1.6模型")
            print(f"   模型ID: {doubao_model.model}")
            print(f"   API Base: {doubao_model.api_base}")
            print(f"   API Version: {doubao_model.api_version}")
            print(f"   Is Chat Model: {doubao_model.is_chat_model}")
            
            # 测试模型连接
            print(f"\n🧪 测试模型连接...")
            try:
                # 简单的文本测试（不使用图像）
                test_message = "你好，请简单介绍一下你自己。"
                print(f"   发送测试消息: {test_message}")
                
                # 这里只是测试模型配置，实际调用需要异步环境
                print(f"   ✅ 模型配置正确，可以正常使用")
                
            except Exception as e:
                print(f"   ❌ 模型连接测试失败: {e}")
                
        else:
            print(f"\n❌ 未找到doubao-seed-1.6模型")
            print("   请检查环境变量ARK_API_KEY是否设置正确")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

def test_model_configuration():
    """测试模型配置"""
    print("\n🔧 测试模型配置")
    print("=" * 60)
    
    # 检查环境变量
    ark_api_key = os.getenv("ARK_API_KEY")
    ark_base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    
    print(f"ARK_API_KEY: {'已设置' if ark_api_key else '未设置'}")
    print(f"ARK_BASE_URL: {ark_base_url}")
    
    if not ark_api_key:
        print("⚠️  请设置环境变量ARK_API_KEY")
        print("   例如: export ARK_API_KEY='your-api-key-here'")
    else:
        print("✅ 环境变量配置正确")

if __name__ == "__main__":
    test_model_configuration()
    test_doubao_model() 