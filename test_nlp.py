from app.chatbot import EVChatbot
import json

def run_tests():
    bot = EVChatbot()
    
    test_queries = [
        "Xe điện nào dưới 500 triệu chạy xa nhất?",
        "VF3 giá bao nhiêu?",
        "VF5 đi được bao xa?",
        "Xe nào chạy được xa nhất?",
        "Có xe nào giá dưới 200 triệu không?",
        "Thời tiết hôm nay thế nào?"
    ]
    
    print("=" * 60)
    print("BẮT ĐẦU KIỂM THỬ AUTOMATED TESTS CHO EV NLP PIPELINE")
    print("=" * 60)
    
    for idx, query in enumerate(test_queries, 1):
        print(f"\n[Test #{idx}] Câu hỏi: \"{query}\"")
        res = bot.get_response(query)
        
        nlp = res["nlp_pipeline"]
        print(f"  - Tách từ (Tokens): {nlp['tokens']}")
        
        pos_list = [f"{t['token']}({t['pos']})" for t in nlp['pos_tags']]
        print(f"  - Gán từ loại (POS): {', '.join(pos_list)}")
        
        ents = [f"{e['entity']}:{e['label']}" for e in nlp['entities']]
        print(f"  - Thực thể (NER): {', '.join(ents) if ents else 'Không có'}")
        
        p = nlp['parser']
        print(f"  - Phân tích cú pháp (Parser):")
        print(f"    + Chủ thể (Subject): {p['subject']}")
        print(f"    + Hành động (Action): {p['action']}")
        print(f"    + Điều kiện (Conditions): {p['conditions']}")
        print(f"    + Thuộc tính hỏi (Target Attribute): {p['target_attribute']}")
        
        print(f"  - Quyết định / Lọc DB: {res['query_log']}")
        print(f"  - Câu trả lời Bot: \"{res['answer']}\"")
        print(f"  - Độ trễ xử lý NLP (Latency): {nlp['latency']['total_ms']} ms")
        print("-" * 50)

if __name__ == "__main__":
    run_tests()
