import json
import os

class EVDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path
        # Dữ liệu mặc định
        self.default_data = {
            "VF3": {"name": "VF3", "price": 235, "range": 210},
            "VF5": {"name": "VF5", "price": 458, "range": 326},
            "VF6": {"name": "VF6", "price": 675, "range": 399}
        }
        self.data = {}
        self.load()

    def load(self):
        if self.db_path and os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = self.default_data.copy()
        else:
            self.data = self.default_data.copy()

    def save(self):
        if self.db_path:
            try:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error saving database: {e}")

    def get_all(self):
        return list(self.data.values())

    def get_by_name(self, name):
        name_upper = name.upper().strip()
        # Tìm chính xác hoặc chứa tên
        for k, v in self.data.items():
            if k.upper() == name_upper or name_upper in k.upper() or k.upper() in name_upper:
                return v
        return None

    def upsert(self, name, price, range_km):
        name_clean = name.strip()
        self.data[name_clean] = {
            "name": name_clean,
            "price": float(price),
            "range": int(range_km)
        }
        self.save()
        return self.data[name_clean]

    def delete(self, name):
        name_clean = name.strip()
        if name_clean in self.data:
            del self.data[name_clean]
            self.save()
            return True
        return False

    def query(self, conditions=None, sort_by=None, reverse=False):
        """
        Truy vấn xe điện với các điều kiện lọc và sắp xếp.
        conditions: list các hàm lambda trả về True/False
        sort_by: tên thuộc tính cần sắp xếp ('price', 'range')
        """
        results = list(self.data.values())

        # Lọc theo điều kiện
        if conditions:
            for cond in conditions:
                results = [r for r in results if cond(r)]

        # Sắp xếp
        if sort_by:
            results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        return results
