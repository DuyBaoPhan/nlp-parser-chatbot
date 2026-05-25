import re

class EVNLPPipeline:
    def __init__(self):
        # 1. Từ điển chuyên biệt cho xe điện (EV Dictionary) dùng cho Tokenizer
        # Sắp xếp từ dài nhất đến ngắn nhất để thuật toán Maximum Matching chạy chính xác
        self.vocabulary = [
            # Tên xe
            "vf 3", "vf 5", "vf 6", "vf 7", "vf 8", "vf 9",
            "vf3", "vf5", "vf6", "vf7", "vf8", "vf9",
            # Thực thể thuộc tính / Cụm từ chuyên ngành
            "tầm hoạt động", "quãng đường", "chạy xa nhất", "chạy xa",
            "giá rẻ nhất", "giá cao nhất", "giá bao nhiêu", "chi phí",
            "xe điện", "ô tô điện", "ô tô", "chiếc xe",
            # Giới từ / Điều kiện
            "ít hơn", "nhiều hơn", "lớn hơn", "nhỏ hơn", "dưới", "trên",
            "khoảng", "trong tầm", "từ", "đến",
            # Đơn vị
            "triệu đồng", "triệu", "tỷ", "km", "cây số",
            # Đại từ / Nghi vấn
            "nào", "gì", "bao nhiêu", "chiếc nào", "loại nào",
            # Động từ hành động
            "chạy", "di chuyển", "đi được", "so sánh", "mua", "tư vấn"
        ]
        
        # POS Tag Map mặc định
        self.pos_rules = {
            "N": ["xe điện", "ô tô điện", "ô tô", "xe", "tầm hoạt động", "quãng đường", "chi phí", "triệu", "triệu đồng", "tỷ", "km", "cây số"],
            "Np": ["vf3", "vf5", "vf6", "vf7", "vf8", "vf9", "vf 3", "vf 5", "vf 6", "vf 7", "vf 8", "vf 9"],
            "V": ["chạy", "di chuyển", "đi được", "so sánh", "mua", "tư vấn", "bán", "có", "tìm"],
            "A": ["xa", "rẻ", "đắt", "cao", "thấp", "xa nhất", "rẻ nhất", "đắt nhất", "tốt nhất"],
            "E": ["dưới", "trên", "từ", "đến", "khoảng", "trong tầm", "hơn"],
            "P": ["nào", "gì", "bao nhiêu", "đâu"],
        }
        
    def _normalize_text(self, text: str) -> str:
        # Chuẩn hóa văn bản: viết thường, loại bỏ khoảng trắng dư thừa
        text = text.lower().strip()
        # Thay thế các ký tự đặc biệt nhưng giữ lại dấu chấm hỏi, phẩy
        text = re.sub(r'\s+', ' ', text)
        return text

    def tokenize(self, text: str):
        """
        Sử dụng giải thuật Maximum Matching (Khớp tối đa) để tách từ tiếng Việt.
        """
        normalized = self._normalize_text(text)
        # Tách dấu câu để xử lý riêng
        # Tách các từ/số và dấu câu
        raw_tokens = re.findall(r'[a-zA-Z0-9_À-ỹ]+|[.,?!=+-]', normalized)
        
        tokens = []
        i = 0
        n = len(raw_tokens)
        
        while i < n:
            matched = False
            # Thử ghép từ dài nhất (tối đa 4 token liên tiếp)
            for length in range(4, 0, -1):
                if i + length <= n:
                    phrase = " ".join(raw_tokens[i:i+length])
                    # Nếu phrase nằm trong vocabulary hoặc là 1 số tự nhiên ghép với đơn vị
                    if phrase in self.vocabulary or self._is_special_phrase(phrase):
                        tokens.append(phrase)
                        i += length
                        matched = True
                        break
            if not matched:
                # Nếu không khớp từ ghép nào, giữ nguyên token đơn
                tokens.append(raw_tokens[i])
                i += 1
                
        # Chuẩn hóa chuẩn viết hoa cho dòng xe (ví dụ: vf3 -> VF3)
        for idx, tok in enumerate(tokens):
            if tok.replace(" ", "").lower() in ["vf3", "vf5", "vf6", "vf7", "vf8", "vf9"]:
                tokens[idx] = tok.replace(" ", "").upper()
                
        return tokens

    def _is_special_phrase(self, phrase: str) -> bool:
        # Nhận diện số kèm đơn vị ví dụ: "500 triệu", "210 km"
        if re.match(r'^\d+\s+(triệu|km|tỷ|đồng)$', phrase):
            return True
        return False

    def pos_tag(self, tokens: list) -> list:
        """
        Gán từ loại cho từng token.
        """
        tagged_tokens = []
        for token in tokens:
            token_lower = token.lower()
            tag = "N" # Mặc định là danh từ
            
            # Kiểm tra xem có phải số không
            if token.isdigit() or re.match(r'^\d+(\.\d+)?$', token):
                tag = "M" # Số từ
            elif re.match(r'^\d+\s+(triệu|km|tỷ|đồng)$', token_lower):
                tag = "M" # Cụm số lượng
            elif token in [".", ",", "?", "!", ":"]:
                tag = "F" # Dấu câu
            else:
                found = False
                for t, words in self.pos_rules.items():
                    if token_lower in words:
                        tag = t
                        found = True
                        break
                if not found:
                    # Fallback dựa trên các heuristics đơn giản
                    if token_lower.startswith("vf"):
                        tag = "Np"
                    elif token_lower in ["chạy", "đi", "so"]:
                        tag = "V"
                    elif token_lower in ["nhất", "hơn"]:
                        tag = "A"
                        
            tagged_tokens.append({"token": token, "pos": tag})
        return tagged_tokens

    def extract_entities(self, tokens: list) -> list:
        """
        Nhận diện thực thể (NER):
        - CAR_MODEL (Tên xe): VF3, VF5, VF6,...
        - PRICE_LIMIT (Điều kiện giá): dưới 500 triệu, trên 300 triệu,...
        - QUERY_ATTR (Thuộc tính truy vấn): chạy xa nhất, giá rẻ nhất,...
        """
        entities = []
        text = " ".join(tokens)
        
        # 1. Nhận diện dòng xe (CAR_MODEL)
        for model in ["VF3", "VF5", "VF6", "VF7", "VF8", "VF9"]:
            if model in text:
                entities.append({
                    "entity": model,
                    "label": "CAR_MODEL",
                    "description": "Tên dòng xe VinFast"
                })
                
        # 2. Nhận diện bộ lọc giá (PRICE_LIMIT)
        # Tìm các cụm như "dưới 500 triệu", "dưới 500tr", "trên 300 triệu"
        price_patterns = [
            r'(dưới|trên|tầm|khoảng|từ)\s+(\d+)\s*(triệu|tỷ|đồng|tr)?',
            r'(\d+)\s*(triệu|tỷ|đồng|tr)'
        ]
        
        for token in tokens:
            token_lower = token.lower()
            # Kiểm tra xem có chứa số và đơn vị tiền tệ không
            if "triệu" in token_lower or "tỷ" in token_lower:
                match = re.search(r'(\d+)\s*(triệu|tỷ)', token_lower)
                if match:
                    val = match.group(1)
                    unit = match.group(2)
                    # Tìm xem có từ chỉ hướng ở trước không (dưới, trên)
                    # Ta quét qua token trước đó nếu có
                    idx = tokens.index(token)
                    prefix = ""
                    if idx > 0 and tokens[idx-1].lower() in ["dưới", "trên", "khoảng", "tầm"]:
                        prefix = tokens[idx-1] + " "
                    
                    entities.append({
                        "entity": prefix + token,
                        "label": "PRICE_LIMIT" if "triệu" in token_lower or "tỷ" in token_lower else "NUMBER",
                        "description": f"Giới hạn giá trị tài chính: {val} {unit}"
                    })
                    
        # 3. Nhận diện thuộc tính truy vấn (QUERY_ATTR)
        for token in tokens:
            token_lower = token.lower()
            if "xa nhất" in token_lower or "xa" in token_lower or "tầm hoạt động" in token_lower:
                entities.append({
                    "entity": token,
                    "label": "QUERY_ATTR",
                    "description": "Yêu cầu lọc tầm hoạt động (Quãng đường)"
                })
            elif "rẻ nhất" in token_lower or "giá" in token_lower or "chi phí" in token_lower:
                entities.append({
                    "entity": token,
                    "label": "QUERY_ATTR",
                    "description": "Yêu cầu lọc giá cả"
                })
                
        # Loại bỏ các thực thể bị trùng lặp trùng lặp
        unique_entities = []
        seen = set()
        for ent in entities:
            key = (ent["entity"], ent["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)
                
        return unique_entities

    def parse(self, tokens: list) -> dict:
        """
        Phân tích cú pháp ngữ nghĩa (Parser).
        Xác định:
        - Chủ thể (Subject)
        - Hành động (Action)
        - Điều kiện (Condition)
        - Thuộc tính cần hỏi (Target Attribute)
        """
        subject = "xe điện"  # Mặc định chủ thể
        action = None
        conditions = []
        target_attribute = None
        
        # Quét các tokens để phân tích
        tokens_lower = [t.lower() for t in tokens]
        
        # 1. Xác định Chủ thể (Subject)
        # Xem có nhắc tên xe cụ thể nào không
        models_found = []
        for t in tokens:
            if t in ["VF3", "VF5", "VF6", "VF7", "VF8", "VF9"]:
                models_found.append(t)
        if models_found:
            subject = models_found[0] if len(models_found) == 1 else models_found
            
        # 2. Xác định Hành động (Action)
        for idx, tag in enumerate(self.pos_tag(tokens)):
            if tag["pos"] == "V":
                action = tag["token"]
                break
        if not action:
            # Fallback nếu không thấy động từ rõ ràng
            if "chạy" in tokens_lower:
                action = "chạy"
            else:
                action = "tư vấn"
                
        # 3. Xác định Điều kiện (Condition)
        # Tìm điều kiện về giá
        for idx, token in enumerate(tokens_lower):
            # Dưới X triệu
            if token in ["dưới", "nhỏ hơn", "ít hơn"]:
                if idx + 1 < len(tokens):
                    next_tok = tokens[idx+1].lower()
                    # Kiểm tra xem có chứa số/triệu không
                    match = re.search(r'(\d+)', next_tok)
                    if match:
                        val = int(match.group(1))
                        conditions.append({
                            "field": "price",
                            "operator": "<",
                            "value": val,
                            "raw": f"{token} {tokens[idx+1]}"
                        })
            # Trên X triệu
            elif token in ["trên", "lớn hơn", "nhiều hơn"]:
                if idx + 1 < len(tokens):
                    next_tok = tokens[idx+1].lower()
                    match = re.search(r'(\d+)', next_tok)
                    if match:
                        val = int(match.group(1))
                        conditions.append({
                            "field": "price",
                            "operator": ">",
                            "value": val,
                            "raw": f"{token} {tokens[idx+1]}"
                        })
                        
        # 4. Xác định Thuộc tính cần hỏi (Target Attribute)
        if any(x in tokens_lower for x in ["chạy xa nhất", "xa nhất", "tầm hoạt động xa nhất", "xa"]):
            target_attribute = {
                "field": "range",
                "type": "max",
                "raw": "chạy xa nhất"
            }
        elif any(x in tokens_lower for x in ["rẻ nhất", "giá rẻ nhất", "tiết kiệm nhất"]):
            target_attribute = {
                "field": "price",
                "type": "min",
                "raw": "rẻ nhất"
            }
        elif any(x in tokens_lower for x in ["đắt nhất", "giá cao nhất"]):
            target_attribute = {
                "field": "price",
                "type": "max",
                "raw": "đắt nhất"
            }
        elif any(x in tokens_lower for x in ["bao nhiêu", "giá", "chi phí"]):
            # Hỏi về giá của một mẫu xe cụ thể
            target_attribute = {
                "field": "price",
                "type": "query",
                "raw": "giá bao nhiêu"
            }
        elif any(x in tokens_lower for x in ["tầm hoạt động", "bao nhiêu km", "quãng đường"]):
            target_attribute = {
                "field": "range",
                "type": "query",
                "raw": "tầm hoạt động"
            }
            
        return {
            "subject": subject,
            "action": action,
            "conditions": conditions,
            "target_attribute": target_attribute
        }

    def process(self, query: str) -> dict:
        """
        Chạy toàn bộ pipeline NLP trên câu hỏi đầu vào.
        """
        import time
        start_time = time.time()
        
        # 1. Tokenizer
        tokens = self.tokenize(query)
        t_tokenize = (time.time() - start_time) * 1000
        
        # 2. POS Tagger
        start_step = time.time()
        pos_tags = self.pos_tag(tokens)
        t_pos = (time.time() - start_step) * 1000
        
        # 3. Entity Recognizer
        start_step = time.time()
        entities = self.extract_entities(tokens)
        t_ner = (time.time() - start_step) * 1000
        
        # 4. Parser
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
                "total_ms": round(total_time, 3)
            }
        }
