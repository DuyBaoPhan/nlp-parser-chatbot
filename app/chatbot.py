import time

from app.database import EVDatabase
from app.nlp_pipeline import EVNLPPipeline


class EVChatbot:
    def __init__(self, db_path=None):
        self.db = EVDatabase(db_path)
        self.pipeline = EVNLPPipeline(self.db.get_model_names())

    def get_response(self, query: str) -> dict:
        start_time = time.time()
        self.pipeline.set_known_models(self.db.get_model_names())

        nlp_result = self.pipeline.process(query)
        parser = nlp_result["parser"]
        subject = parser["subject"]
        conditions = parser["conditions"]
        target = parser["target_attribute"]

        query_log = []
        matched_cars = []

        db_conditions = self._build_db_conditions(conditions, query_log)
        candidates = self.db.query(conditions=db_conditions)

        if isinstance(subject, list):
            answer, matched_cars = self._answer_comparison(subject, target, query_log)
        elif isinstance(subject, str) and self.db.get_by_name(subject):
            answer, matched_cars = self._answer_specific_car(subject, target, db_conditions, query_log)
        elif target and target["type"] == "recommend":
            answer, matched_cars = self._answer_recommendation(candidates, conditions, query_log)
        else:
            answer, matched_cars = self._answer_general(candidates, conditions, target, query, query_log)

        total_time_ms = (time.time() - start_time) * 1000

        return {
            "query": query,
            "answer": answer,
            "matched_cars": matched_cars,
            "query_log": query_log,
            "nlp_pipeline": nlp_result,
            "chatbot_latency_ms": round(total_time_ms, 3),
        }

    def _build_db_conditions(self, conditions, query_log):
        db_conditions = []
        for cond in conditions:
            field = cond["field"]
            operator = cond["operator"]
            value = cond["value"]
            query_log.append(f"Lọc điều kiện: {field} {operator} {value} ({cond['raw']})")

            if operator == "<":
                db_conditions.append(lambda car, f=field, v=value: car[f] < v)
            elif operator == "<=":
                db_conditions.append(lambda car, f=field, v=value: car[f] <= v)
            elif operator == ">":
                db_conditions.append(lambda car, f=field, v=value: car[f] > v)
            elif operator == ">=":
                db_conditions.append(lambda car, f=field, v=value: car[f] >= v)
            elif operator == "between":
                low, high = value
                db_conditions.append(lambda car, f=field, lo=low, hi=high: lo <= car[f] <= hi)
        return db_conditions

    def _answer_specific_car(self, model, target, db_conditions, query_log):
        car = self.db.get_by_name(model)
        query_log.append(f"Truy vấn xe cụ thể: {car['name']}")

        if db_conditions and not all(condition(car) for condition in db_conditions):
            return f"{car['name']} có trong dữ liệu, nhưng không thỏa điều kiện bạn đưa ra.", []

        if target and target["field"] == "price":
            answer = f"{car['name']} có giá {self._format_price(car['price'])}, tầm hoạt động khoảng {car['range']} km."
        elif target and target["field"] == "range":
            answer = f"{car['name']} đi được khoảng {car['range']} km sau mỗi lần sạc, giá {self._format_price(car['price'])}."
        else:
            answer = f"{car['name']}: giá {self._format_price(car['price'])}, tầm hoạt động {car['range']} km."

        return answer, [car]

    def _answer_comparison(self, models, target, query_log):
        cars = [self.db.get_by_name(model) for model in models]
        cars = [car for car in cars if car]
        query_log.append(f"So sánh {len(cars)} mẫu xe: {', '.join(car['name'] for car in cars)}")

        if len(cars) < 2:
            return "Tôi cần ít nhất hai mẫu xe có trong dữ liệu để so sánh.", cars

        parts = [f"{car['name']} giá {self._format_price(car['price'])}, đi được {car['range']} km" for car in cars]
        cheapest = min(cars, key=lambda car: car["price"])
        longest = max(cars, key=lambda car: car["range"])

        if target and target["field"] == "price":
            conclusion = f"Nếu ưu tiên giá, {cheapest['name']} đang dễ tiếp cận hơn."
        elif target and target["field"] == "range":
            conclusion = f"Nếu ưu tiên tầm hoạt động, {longest['name']} nổi bật hơn."
        else:
            conclusion = f"{cheapest['name']} lợi thế về giá; {longest['name']} lợi thế về tầm hoạt động."

        return f"So sánh nhanh: {'; '.join(parts)}. {conclusion}", cars

    def _answer_recommendation(self, candidates, conditions, query_log):
        if not candidates:
            query_log.append("Không có mẫu xe phù hợp để tư vấn")
            return "Tôi chưa tìm thấy mẫu xe nào khớp ngân sách hoặc điều kiện bạn đưa ra.", []

        candidates = sorted(candidates, key=lambda car: (car["range"] / max(car["price"], 1), car["range"]), reverse=True)
        best = candidates[0]
        alternatives = candidates[1:3]
        query_log.append(f"Đề xuất xe có tỷ lệ tầm hoạt động/giá tốt nhất: {best['name']}")

        answer = (
            f"Tôi gợi ý {best['name']} vì xe có giá {self._format_price(best['price'])}, "
            f"tầm hoạt động {best['range']} km và cân bằng tốt giữa chi phí với quãng đường."
        )
        if alternatives:
            answer += " Bạn cũng có thể cân nhắc " + ", ".join(
                f"{car['name']} ({self._format_price(car['price'])}, {car['range']} km)" for car in alternatives
            ) + "."
        return answer, candidates[:3]

    def _answer_general(self, candidates, conditions, target, query, query_log):
        if not candidates:
            query_log.append("Không có mẫu xe nào thỏa bộ lọc")
            return "Tôi chưa tìm thấy mẫu xe nào thỏa điều kiện đó. Bạn có thể nới ngân sách hoặc giảm yêu cầu tầm hoạt động.", []

        query_plain = self.pipeline._plain_text(query)
        if not target and not conditions and not any(word in query_plain for word in ["danh sach", "co nhung xe", "xe gi", "tu van"]):
            return (
                "Tôi có thể tư vấn theo giá, tầm hoạt động hoặc so sánh xe. "
                "Ví dụ: 'VF5 giá bao nhiêu?', 'xe dưới 700 triệu chạy xa nhất?', hoặc 'so sánh VF5 và VF6'."
            ), []

        query_log.append(f"Tìm thấy {len(candidates)} mẫu xe phù hợp")

        if target:
            field = target["field"]
            query_type = target["type"]
            if query_type in {"max", "min"} and field in {"price", "range"}:
                reverse = query_type == "max"
                best = sorted(candidates, key=lambda car: car[field], reverse=reverse)[0]
                query_log.append(f"Chọn {best['name']} theo {query_type}({field})")
                if field == "range":
                    label = "chạy xa nhất" if query_type == "max" else "có tầm hoạt động ngắn nhất"
                    return (
                        f"{best['name']} {label} trong nhóm phù hợp: {best['range']} km, "
                        f"giá {self._format_price(best['price'])}."
                    ), [best]
                label = "giá cao nhất" if query_type == "max" else "rẻ nhất"
                return (
                    f"{best['name']} là mẫu {label} trong nhóm phù hợp: {self._format_price(best['price'])}, "
                    f"tầm hoạt động {best['range']} km."
                ), [best]

            if query_type == "query" and field in {"price", "range"}:
                return self._answer_attribute_list(candidates, field), candidates

        return self._answer_list(candidates), candidates

    def _answer_attribute_list(self, cars, field):
        if field == "price":
            values = [f"{car['name']} {self._format_price(car['price'])}" for car in cars]
            return "Giá các mẫu xe phù hợp: " + "; ".join(values) + "."
        values = [f"{car['name']} {car['range']} km" for car in cars]
        return "Tầm hoạt động các mẫu xe phù hợp: " + "; ".join(values) + "."

    def _answer_list(self, cars):
        return "Các mẫu xe phù hợp: " + "; ".join(
            f"{car['name']} (giá {self._format_price(car['price'])}, {car['range']} km)" for car in cars
        ) + "."

    def _format_price(self, price):
        if float(price).is_integer():
            return f"{int(price)} triệu đồng"
        return f"{price:g} triệu đồng"
