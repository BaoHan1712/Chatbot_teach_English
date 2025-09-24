#!/usr/bin/env python3
"""
Test script để kiểm tra API backend
"""

import requests
import json

def test_api():
    try:
        # Test API endpoint
        url = "http://localhost:5000/generate/lesson/Food"
        print(f"🚀 Testing API: {url}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Response successful!")
            print(f"📊 Response keys: {list(data.keys())}")
            
            # Kiểm tra cấu trúc
            print("\n🔍 Checking structure:")
            print(f"  - Topic: {data.get('topic', 'N/A')}")
            print(f"  - Vocabulary count: {len(data.get('vocabulary', []))}")
            print(f"  - Example sentences count: {len(data.get('example_sentences', []))}")
            print(f"  - Conversation count: {len(data.get('conversation', []))}")
            print(f"  - Exercises count: {len(data.get('exercises', []))}")
            
            # Hiển thị mẫu dữ liệu
            print("\n📝 Sample vocabulary:")
            for i, vocab in enumerate(data.get('vocabulary', [])[:2]):
                print(f"  {i+1}. {vocab.get('word', 'N/A')} - {vocab.get('vietnamese_meaning', 'N/A')}")
            
            print("\n💬 Sample conversation:")
            for conv in data.get('conversation', [])[:2]:
                speaker = conv.get('speaker', 'N/A')
                text = conv.get('text', 'N/A')
                print(f"  {speaker}: {text}")
            
            print("\n🎯 Sample exercises:")
            for i, ex in enumerate(data.get('exercises', [])[:2]):
                ex_type = ex.get('type', 'N/A')
                print(f"  {i+1}. {ex_type}")
            
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend không chạy hoặc không thể kết nối")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Backend API...")
    success = test_api()
    
    if success:
        print("\n🎉 Test thành công! Backend hoạt động tốt.")
    else:
        print("\n💥 Test thất bại! Cần kiểm tra backend.")
