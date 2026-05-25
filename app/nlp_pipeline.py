import re
import unicodedata
from typing import Optional


class EVNLPPipeline:
    """Lightweight Vietnamese NLP pipeline for EV consultation queries."""

    PRICE_WORDS = ("giá", "gia", "chi phí", "chi phi", "tiền", "tien")
    RANGE_WORDS = (
        "tầm hoạt động",
        "tam hoat dong",
        "quãng đường",
        "quang duong",
        "phạm vi",
        "pham vi",
        "chạy",
        "chay",
        "đi được",
        "di duoc",
        "km",
        "cây số",
        "cay so",
    )

    def __init__(self, known_models=None):
        self.known_models = self._normalize_models(known_models or [])
        self.vocabulary = [
            "tầm hoạt động",
            "quãng đường",
            "chạy xa nhất",
            "chạy xa",
            "giá rẻ nhất",
            "giá cao nhất",
            "giá bao nhiêu",
            "chi phí",
            "xe điện",
            "ô tô điện",
            "ô tô",
            "chiếc xe",
            "ít hơn",
            "nhiều hơn",
            "lớn hơn",
            "nhỏ hơn",
            "không quá",
            "tối đa",
            "tối thiểu",
            "dưới",
            "trên",
            "khoảng",
            "trong tầm",
            "từ",
            "đến",
            "triệu đồng",
            "triệu",
            "tỷ",
            "km",
            "cây số",
            "bao nhiêu",
            "chiếc nào",
            "loại nào",
            "đi được",
            "so sánh",
            "tư vấn",
            "nên mua",
            "phù hợp",
        ]

        self.pos_rules = {
            "N": [
                "xe điện",
                "ô tô điện",
                "ô tô",
                "xe",
                "tầm hoạt động",
                "quãng đường",
                "chi phí",
                "triệu",
                "triệu đồng",
                "tỷ",
                "km",
                "cây số",
            ],
            "Np": list(self.known_models),
            "V": ["chạy", "chạy xa", "di chuyển", "đi được", "so sánh", "mua", "tư vấn", "bán", "có", "tìm", "nên mua"],
            "A": [
                "xa",
                "rẻ",
                "đắt",
                "cao",
                "thấp",
                "chạy xa nhất",
                "xa nhất",
                "giá bao nhiêu",
                "rẻ nhất",
                "đắt nhất",
                "tốt nhất",
                "phù hợp",
            ],
            "E": ["dưới", "trên", "từ", "đến", "khoảng", "trong tầm", "hơn", "không quá", "tối đa", "tối thiểu"],
            "P": ["nào", "gì", "bao nhiêu", "đâu"],
        }

    def set_known_models(self, models):
        self.known_models = self._normalize_models(models)
        self.pos_rules["Np"] = list(self.known_models)

    def _normalize_models(self, models):
        return {str(model).upper().replace(" ", "") for model in models if str(model).strip()}

    def _strip_accents(self, text: str) -> str:
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return text.replace("đ", "d").replace("Đ", "D")

    def _normalize_text(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _plain_text(self, text: str) -> str:
        return self._strip_accents(self._normalize_text(text))

    def _canonical_model(self, value: str) -> str:
        return value.upper().replace(" ", "")

    def _find_models(self, text: str) -> list:
        plain = self._plain_text(text)
        compact_plain = re.sub(r"[^a-z0-9]", "", plain).upper()
        models = []

        for match in re.finditer(r"\bvf\s*(\d+)\b", plain, flags=re.IGNORECASE):
            model = f"VF{match.group(1)}"
            if model not in models:
                models.append(model)

        for model in sorted(self.known_models, key=len, reverse=True):
            compact_model = re.sub(r"[^A-Z0-9]", "", model.upper())
            if compact_model and compact_model in compact_plain and model not in models:
                models.append(model)

        return models

    def _parse_number(self, value: str, unit: Optional[str] = None) -> float:
        number = float(value.replace(",", "."))
        unit_plain = self._plain_text(unit or "")
        if unit_plain in {"ty", "ti"}:
            return number * 1000
        return number

    def tokenize(self, text: str):
        normalized = self._normalize_text(text)
        raw_tokens = re.findall(r"[a-zA-Z0-9_À-ỹ]+|[.,?!=+\-]", normalized)

        tokens = []
        i = 0
        while i < len(raw_tokens):
            matched = False
            for length in range(4, 0, -1):
                phrase = " ".join(raw_tokens[i : i + length])
                if phrase in self.vocabulary or self._is_special_phrase(phrase):
                    tokens.append(phrase)
                    i += length
                    matched = True
                    break
            if matched:
                continue

            token = raw_tokens[i]
            model_match = re.fullmatch(r"vf\s*(\d+)", token, flags=re.IGNORECASE)
            if model_match:
                tokens.append(f"VF{model_match.group(1)}")
            else:
                tokens.append(token)
            i += 1

        return tokens

    def _is_special_phrase(self, phrase: str) -> bool:
        phrase_plain = self._plain_text(phrase)
        return bool(re.match(r"^\d+(?:[,.]\d+)?\s+(trieu|ty|km|dong|tr)$", phrase_plain))

    def pos_tag(self, tokens: list) -> list:
        tagged_tokens = []
        for token in tokens:
            token_lower = token.lower()
            token_plain = self._plain_text(token)
            tag = "N"

            if re.fullmatch(r"\d+(?:[,.]\d+)?", token):
                tag = "M"
            elif re.fullmatch(r"\d+(?:[,.]\d+)?\s+(trieu|ty|km|dong|tr)", token_plain):
                tag = "M"
            elif token in [".", ",", "?", "!", ":"]:
                tag = "F"
            elif self._canonical_model(token) in self.known_models or re.fullmatch(r"VF\d+", self._canonical_model(token)):
                tag = "Np"
            else:
                for pos, words in self.pos_rules.items():
                    normalized_words = {self._plain_text(word) for word in words}
                    if token_lower in words or token_plain in normalized_words:
                        tag = pos
                        break

            tagged_tokens.append({"token": token, "pos": tag})
        return tagged_tokens

    def extract_entities(self, tokens: list) -> list:
        entities = []
        text = " ".join(tokens)
        text_plain = self._plain_text(text)

        for model in self._find_models(text):
            entities.append({"entity": model, "label": "CAR_MODEL", "description": "Tên dòng xe điện"})

        for cond in self._extract_conditions(text):
            label = "PRICE_LIMIT" if cond["field"] == "price" else "RANGE_LIMIT"
            entities.append({"entity": cond["raw"], "label": label, "description": cond["description"]})

        target = self._detect_target(text)
        if target:
            entities.append(
                {
                    "entity": target["raw"],
                    "label": "QUERY_ATTR",
                    "description": "Thuộc tính người dùng muốn tra cứu hoặc so sánh",
                }
            )

        if any(word in text_plain for word in ["tu van", "nen mua", "phu hop", "goi y"]):
            entities.append({"entity": "tư vấn", "label": "INTENT", "description": "Yêu cầu tư vấn lựa chọn xe"})

        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity["entity"], entity["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        return unique_entities

    def _extract_conditions(self, text: str) -> list:
        normalized = self._normalize_text(text)
        plain = self._plain_text(normalized)
        conditions = []

        between_patterns = [
            r"(?:tu|trong khoang)\s+(\d+(?:[,.]\d+)?)\s*(trieu|ty|tr)?\s+(?:den|-)\s+(\d+(?:[,.]\d+)?)\s*(trieu|ty|tr)?",
            r"(\d+(?:[,.]\d+)?)\s*(trieu|ty|tr)?\s*(?:den|-)\s*(\d+(?:[,.]\d+)?)\s*(trieu|ty|tr)",
        ]
        for pattern in between_patterns:
            for match in re.finditer(pattern, plain):
                low = self._parse_number(match.group(1), match.group(2) or match.group(4))
                high = self._parse_number(match.group(3), match.group(4) or match.group(2))
                if low > high:
                    low, high = high, low
                conditions.append(
                    {
                        "field": "price",
                        "operator": "between",
                        "value": [low, high],
                        "raw": match.group(0),
                        "description": f"Khoảng giá từ {low:g} đến {high:g} triệu đồng",
                    }
                )

        rules = [
            (r"(?:duoi|nho hon|it hon|khong qua|toi da|tam)\s+(\d+(?:[,.]\d+)?)\s*(trieu|ty|tr)", "price", "<="),
            (r"(?:tren|lon hon|nhieu hon|toi thieu)\s+(\d+(?:[,.]\d+)?)\s*(trieu|ty|tr)", "price", ">="),
            (r"(?:duoi|nho hon|it hon|khong qua|toi da)\s+(\d+(?:[,.]\d+)?)\s*(?:km|cay so)", "range", "<="),
            (r"(?:tren|lon hon|nhieu hon|toi thieu)\s+(\d+(?:[,.]\d+)?)\s*(?:km|cay so)", "range", ">="),
        ]
        for pattern, field, operator in rules:
            for match in re.finditer(pattern, plain):
                value = self._parse_number(match.group(1), match.group(2) if field == "price" and match.lastindex and match.lastindex >= 2 else None)
                conditions.append(
                    {
                        "field": field,
                        "operator": operator,
                        "value": value,
                        "raw": match.group(0),
                        "description": self._condition_description(field, operator, value),
                    }
                )

        return self._dedupe_conditions(conditions)

    def _dedupe_conditions(self, conditions: list) -> list:
        unique = []
        seen = set()
        for cond in conditions:
            value = tuple(cond["value"]) if isinstance(cond["value"], list) else cond["value"]
            key = (cond["field"], cond["operator"], value)
            if key not in seen:
                seen.add(key)
                unique.append(cond)
        return unique

    def _condition_description(self, field: str, operator: str, value: float) -> str:
        label = "giá" if field == "price" else "tầm hoạt động"
        unit = "triệu đồng" if field == "price" else "km"
        return f"Điều kiện {label} {operator} {value:g} {unit}"

    def _detect_target(self, text: str) -> Optional[dict]:
        plain = self._plain_text(text)

        if any(word in plain for word in ["so sanh", "khac nhau", "hon kem"]):
            return {"field": "comparison", "type": "compare", "raw": "so sánh"}
        if any(word in plain for word in ["xa nhat", "di duoc xa nhat", "tam hoat dong lon nhat", "range cao nhat"]):
            return {"field": "range", "type": "max", "raw": "chạy xa nhất"}
        if any(word in plain for word in ["gan nhat", "ngan nhat", "tam hoat dong thap nhat"]):
            return {"field": "range", "type": "min", "raw": "tầm hoạt động thấp nhất"}
        if any(word in plain for word in ["re nhat", "gia thap nhat", "tiet kiem nhat"]):
            return {"field": "price", "type": "min", "raw": "rẻ nhất"}
        if any(word in plain for word in ["dat nhat", "gia cao nhat", "cao nhat"]):
            return {"field": "price", "type": "max", "raw": "giá cao nhất"}
        if any(word in plain for word in self.RANGE_WORDS):
            return {"field": "range", "type": "query", "raw": "tầm hoạt động"}
        if any(word in plain for word in self.PRICE_WORDS) or "bao nhieu" in plain:
            return {"field": "price", "type": "query", "raw": "giá bao nhiêu"}
        if any(word in plain for word in ["tu van", "nen mua", "phu hop", "goi y"]):
            return {"field": "recommendation", "type": "recommend", "raw": "tư vấn"}
        return None

    def parse(self, tokens: list) -> dict:
        text = " ".join(tokens)
        text_plain = self._plain_text(text)

        models_found = self._find_models(text)

        subject = "xe điện"
        if len(models_found) == 1:
            subject = models_found[0]
        elif len(models_found) > 1:
            subject = models_found

        action = "tư vấn"
        for tagged in self.pos_tag(tokens):
            if tagged["pos"] == "V":
                action = tagged["token"]
                break
        if "so sanh" in text_plain:
            action = "so sánh"
        elif any(word in text_plain for word in ["tu van", "nen mua", "phu hop", "goi y"]):
            action = "tư vấn"

        return {
            "subject": subject,
            "action": action,
            "conditions": self._extract_conditions(text),
            "target_attribute": self._detect_target(text),
        }

    def process(self, query: str) -> dict:
        import time

        start_time = time.time()

        tokens = self.tokenize(query)
        t_tokenize = (time.time() - start_time) * 1000

        start_step = time.time()
        pos_tags = self.pos_tag(tokens)
        t_pos = (time.time() - start_step) * 1000

        start_step = time.time()
        entities = self.extract_entities(tokens)
        t_ner = (time.time() - start_step) * 1000

        start_step = time.time()
        parsed_structure = self.parse(tokens)
        t_parse = (time.time() - start_step) * 1000

        total_time = (time.time() - start_time) * 1000

        return {
            "query": query,
            "tokens": tokens,
            "pos_tags": pos_tags,
            "entities": entities,
            "parser": parsed_structure,
            "latency": {
                "tokenizer_ms": round(t_tokenize, 3),
                "pos_tagger_ms": round(t_pos, 3),
                "ner_ms": round(t_ner, 3),
                "parser_ms": round(t_parse, 3),
                "total_ms": round(total_time, 3),
            },
        }
