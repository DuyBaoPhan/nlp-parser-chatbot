from app.chatbot import EVChatbot


def run_tests():
    bot = EVChatbot()

    test_queries = [
        "Xe điện nào dưới 500 triệu chạy xa nhất?",
        "VF3 giá bao nhiêu?",
        "VF5 đi được bao xa?",
        "Xe nào chạy được xa nhất?",
        "Có xe nào giá từ 400 đến 900 triệu không?",
        "Tư vấn xe dưới 700 triệu phù hợp nhất",
        "So sánh VF5 và VF6",
        "Xe nào đi được trên 400 km?",
        "Thời tiết hôm nay thế nào?",
    ]

    print("=" * 60)
    print("BẮT ĐẦU KIỂM THỬ EV NLP PIPELINE")
    print("=" * 60)

    for idx, query in enumerate(test_queries, 1):
        print(f'\n[Test #{idx}] Câu hỏi: "{query}"')
        res = bot.get_response(query)

        nlp = res["nlp_pipeline"]
        print(f"  - Tokens: {nlp['tokens']}")

        pos_list = [f"{item['token']}({item['pos']})" for item in nlp["pos_tags"]]
        print(f"  - POS: {', '.join(pos_list)}")

        entities = [f"{item['entity']}:{item['label']}" for item in nlp["entities"]]
        print(f"  - NER: {', '.join(entities) if entities else 'Không có'}")

        parser = nlp["parser"]
        print("  - Parser:")
        print(f"    + Subject: {parser['subject']}")
        print(f"    + Action: {parser['action']}")
        print(f"    + Conditions: {parser['conditions']}")
        print(f"    + Target: {parser['target_attribute']}")

        print(f"  - Query log: {res['query_log']}")
        print(f'  - Bot: "{res["answer"]}"')
        print(f"  - NLP latency: {nlp['latency']['total_ms']} ms")
        print("-" * 50)


if __name__ == "__main__":
    run_tests()
