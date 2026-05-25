import json
import os


class EVDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.default_data = {
            "VF3": {"name": "VF3", "price": 235.0, "range": 210},
            "VF5": {"name": "VF5", "price": 458.0, "range": 326},
            "VF6": {"name": "VF6", "price": 675.0, "range": 399},
            "VF7": {"name": "VF7", "price": 850.0, "range": 431},
            "VF8": {"name": "VF8", "price": 1079.0, "range": 471},
            "VF9": {"name": "VF9", "price": 1499.0, "range": 626},
        }
        self.data = {}
        self.load()

    def _key(self, name):
        return str(name).upper().replace(" ", "").strip()

    def load(self):
        if self.db_path and os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data = {self._key(v.get("name", k)): self._normalize_car(v.get("name", k), v) for k, v in loaded.items()}
                return
            except Exception:
                pass
        self.data = self.default_data.copy()

    def _normalize_car(self, name, car):
        return {
            "name": str(name).strip().upper().replace(" ", ""),
            "price": float(car["price"]),
            "range": int(car["range"]),
        }

    def save(self):
        if self.db_path:
            try:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error saving database: {e}")

    def get_all(self):
        return sorted(self.data.values(), key=lambda car: (car["price"], car["name"]))

    def get_by_name(self, name):
        key = self._key(name)
        if key in self.data:
            return self.data[key]
        for car_key, car in self.data.items():
            if key in car_key or car_key in key:
                return car
        return None

    def get_model_names(self):
        return [car["name"] for car in self.get_all()]

    def upsert(self, name, price, range_km):
        name_clean = str(name).strip().upper().replace(" ", "")
        key = self._key(name_clean)
        self.data[key] = {
            "name": name_clean,
            "price": float(price),
            "range": int(range_km),
        }
        self.save()
        return self.data[key]

    def delete(self, name):
        key = self._key(name)
        if key in self.data:
            del self.data[key]
            self.save()
            return True
        return False

    def query(self, conditions=None, sort_by=None, reverse=False):
        results = self.get_all()

        if conditions:
            for cond in conditions:
                results = [car for car in results if cond(car)]

        if sort_by:
            results.sort(key=lambda car: car.get(sort_by, 0), reverse=reverse)

        return results
