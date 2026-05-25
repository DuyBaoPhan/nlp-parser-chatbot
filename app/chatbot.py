from app.nlp_pipeline import EVNLPPipeline
from app.database import EVDatabase
import time

class EVChatbot:
    def __init__(self, db_path=None):
        self.pipeline = EVNLPPipeline()
        self.db = EVDatabase(db_path)

    def get_response(self, query: str) -> dict:
        """
        Nhận câu hỏi, phân tích NLP, truy vấn cơ sở dữ liệu và trả về câu trả lời.
        """
        start_time = time.time()
        
        # 1. Chạy NLP Pipeline
        nlp_result = self.pipeline.process(query)
        parser = nlp_result["parser"]
        
        # 2. Xử lý logic truy vấn cơ sở dữ liệu
        answer = "Hiện tôi chưa có thông tin đó."
        matched_cars = []
        query_log = []
        
        subject = parser["subject"]
        conditions = parser["conditions"]
        target = parser["target_attribute"]
        
        # Xây dựng các hàm lambda điều kiện lọc từ Parser
        db_conditions = []
        for cond in conditions:
            field = cond["field"]
            op = cond["operator"]
            val = cond["value"]
            raw = cond["raw"]
            
            query_log.append(f"Lọc theo điều kiện: {field} {op} {val} ({raw})")
            
            if field == "price":
                if op == "<":
                    db_conditions.append(lambda x, v=val: x["price"] < v)
                elif op == ">":
                    db_conditions.append(lambda x, v=val: x["price"] > v)
                    
        # Thực hiện truy vấn
        if isinstance(subject, str) and subject.upper() in ["VF3", "VF5", "VF6", "VF7", "VF8", "VF9"]:
            # 2a. Hỏi về một dòng xe cụ thể (ví dụ: "VF3 giá bao nhiêu?", "VF5 chạy được bao xa?")
            car = self.db.get_by_name(subject)
            if car:
                matched_cars.append(car)
                query_log.append(f"Truy vấn thông tin cụ thể xe: {car['name']}")
                
                # Áp dụng bộ lọc điều kiện nếu có (để phòng trường hợp hỏi mâu thuẫn như "VF3 giá trên 500 triệu")
                valid = True
                for cond_func in db_conditions:
                    if not cond_func(car):
                        valid = False
                        break
                        
                if valid:
                    if target and target["field"] == "price":
                        answer = f"Mẫu xe {car['name']} có giá là {int(car['price']) if car['price'].is_integer() else car['price']} triệu đồng, với tầm hoạt động {car['range']} km."
                    elif target and target["field"] == "range":
                        answer = f"Tầm hoạt động của mẫu xe {car['name']} là {car['range']} km, mức giá bán là {int(car['price']) if car['price'].is_integer() else car['price']} triệu đồng."
                    else:
                        answer = f"Thông tin xe {car['name']}: Giá bán {int(car['price']) if car['price'].is_integer() else car['price']} triệu đồng, tầm hoạt động khoảng {car['range']} km."
                else:
                    answer = "Hiện tôi chưa có thông tin đó."
            else:
                answer = "Hiện tôi chưa có thông tin đó."
                
        else:
            # 2b. Hỏi chung chung về phân khúc hoặc so sánh (ví dụ: "xe điện nào dưới 500 triệu chạy xa nhất?")
            # Lấy toàn bộ danh sách xe thỏa mãn điều kiện
            candidates = self.db.query(conditions=db_conditions)
            
            if candidates:
                query_log.append(f"Tìm thấy {len(candidates)} mẫu xe thỏa mãn bộ lọc")
                
                if target:
                    field = target["field"]
                    query_type = target["type"]
                    
                    if query_type == "max":
                        # Tìm xe có thuộc tính lớn nhất (e.g. chạy xa nhất)
                        candidates.sort(key=lambda x: x.get(field, 0), reverse=True)
                        best_car = candidates[0]
                        matched_cars.append(best_car)
                        query_log.append(f"Tìm xe có {field} lớn nhất: {best_car['name']}")
                        
                        cond_str = f" trong phân khúc {conditions[0]['raw']}" if conditions else ""
                        if field == "range":
                            answer = f"Trong phân khúc{cond_str}, mẫu xe {best_car['name']} chạy xa nhất với quãng đường di chuyển {best_car['range']} km (giá bán {int(best_car['price'])} triệu đồng)."
                        elif field == "price":
                            answer = f"Trong phân khúc{cond_str}, mẫu xe {best_car['name']} có giá cao nhất là {int(best_car['price'])} triệu đồng, tầm hoạt động {best_car['range']} km."
                            
                    elif query_type == "min":
                        # Tìm xe có thuộc tính nhỏ nhất (e.g. rẻ nhất)
                        candidates.sort(key=lambda x: x.get(field, 0), reverse=False)
                        best_car = candidates[0]
                        matched_cars.append(best_car)
                        query_log.append(f"Tìm xe có {field} nhỏ nhất: {best_car['name']}")
                        
                        cond_str = f" trong phân khúc {conditions[0]['raw']}" if conditions else ""
                        if field == "price":
                            answer = f"Mẫu xe {best_car['name']} có giá rẻ nhất{cond_str} là {int(best_car['price'])} triệu đồng, tầm hoạt động {best_car['range']} km."
                        elif field == "range":
                            answer = f"Mẫu xe {best_car['name']} có quãng đường ngắn nhất{cond_str} là {best_car['range']} km, giá bán {int(best_car['price'])} triệu đồng."
                    
                    elif query_type == "query":
                        # Trả về danh sách xe thỏa mãn kèm thông tin thuộc tính cần hỏi
                        matched_cars = candidates
                        car_infos = []
                        for car in candidates:
                            val = car.get(field)
                            unit = "triệu đồng" if field == "price" else "km"
                            car_infos.append(f"{car['name']} ({val} {unit})")
                        
                        cond_str = f" {conditions[0]['raw']}" if conditions else ""
                        attr_vietnamese = "giá bán" if field == "price" else "tầm hoạt động"
                        answer = f"Các xe điện{cond_str} có {attr_vietnamese} là: {', '.join(car_infos)}."
                        
                else:
                    # Trả về toàn bộ xe thỏa mãn điều kiện lọc
                    matched_cars = candidates
                    car_infos = [f"{c['name']} (Giá: {int(c['price'])} triệu, Quãng đường: {c['range']} km)" for c in candidates]
                    cond_str = f" {conditions[0]['raw']}" if conditions else ""
                    answer = f"Dưới đây là các xe điện thỏa mãn điều kiện{cond_str}: {'; '.join(car_infos)}."
            else:
                query_log.append("Không có mẫu xe nào thỏa mãn điều kiện lọc")
                answer = "Hiện tôi chưa có thông tin đó."

        # Nếu câu hỏi hoàn toàn ngoài lề (không nhận diện được bất kỳ thực thể xe/giá/quãng đường nào và parser không hiểu gì)
        # thì trả về câu mặc định
        if not nlp_result["entities"] and not parser["conditions"] and not parser["target_attribute"] and parser["subject"] == "xe điện":
            # Ngoại lệ: Nếu câu hỏi hỏi chung chung "có những xe gì", "tư vấn xe"
            if any(x in query.lower() for x in ["tư vấn", "danh sách xe", "có những xe nào", "xe gì"]):
                all_cars = self.db.get_all()
                matched_cars = all_cars
                car_infos = [f"{c['name']} (Giá: {int(c['price'])} triệu, Quãng đường: {c['range']} km)" for c in all_cars]
                answer = f"Hiện tôi đang có thông tin của các dòng xe: {'; '.join(car_infos)}."
            else:
                answer = "Hiện tôi chưa có thông tin đó."
                
        total_time_ms = (time.time() - start_time) * 1000
        
        return {
            "query": query,
            "answer": answer,
            "matched_cars": matched_cars,
            "query_log": query_log,
            "nlp_pipeline": nlp_result,
            "chatbot_latency_ms": round(total_time_ms, 3)
        }
