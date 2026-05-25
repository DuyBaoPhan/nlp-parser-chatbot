document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements - Chat
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatWindow = document.getElementById("chat-window");
    const btnClearChat = document.getElementById("btn-clear-chat");
    const queryChips = document.getElementById("query-chips");
    const pingLatency = document.getElementById("ping-latency");

    // DOM Elements - Diagnostics (NLP Tab)
    const valTokenizer = document.getElementById("val-tokenizer");
    const valTagger = document.getElementById("val-tagger");
    const valNer = document.getElementById("val-ner");
    const valParser = document.getElementById("val-parser");
    const valTotal = document.getElementById("val-total");

    const pbTokenizer = document.getElementById("pb-tokenizer");
    const pbTagger = document.getElementById("pb-tagger");
    const pbNer = document.getElementById("pb-ner");
    const pbParser = document.getElementById("pb-parser");

    const visualizerTokenizer = document.getElementById("visualizer-tokenizer");
    const visualizerTagger = document.getElementById("visualizer-tagger");
    const visualizerNer = document.getElementById("visualizer-ner");

    const parserSubject = document.getElementById("parser-subject");
    const parserAction = document.getElementById("parser-action");
    const parserConditions = document.getElementById("parser-conditions");
    const parserAttribute = document.getElementById("parser-attribute");

    const decisionFlow = document.getElementById("decision-flow");

    // DOM Elements - Tabs
    const tabBtnNlp = document.getElementById("tab-btn-nlp");
    const tabBtnDb = document.getElementById("tab-btn-db");
    const nlpTab = document.getElementById("nlp-tab");
    const dbTab = document.getElementById("db-tab");

    // DOM Elements - DB Manager
    const dbForm = document.getElementById("db-form");
    const carName = document.getElementById("car-name");
    const carPrice = document.getElementById("car-price");
    const carRange = document.getElementById("car-range");
    const formMessage = document.getElementById("form-message");
    const dbTableBody = document.getElementById("db-table-body");

    // Measure active network roundtrip ping
    function updatePing() {
        const start = Date.now();
        fetch("/api/database")
            .then(res => res.json())
            .then(() => {
                const diff = Date.now() - start;
                pingLatency.textContent = diff;
            })
            .catch(() => {
                pingLatency.textContent = "N/A";
            });
    }
    updatePing();
    setInterval(updatePing, 10000); // Ping every 10 seconds

    // TAB Navigation logic
    tabBtnNlp.addEventListener("click", () => switchTab("nlp"));
    tabBtnDb.addEventListener("click", () => switchTab("db"));

    function switchTab(tab) {
        if (tab === "nlp") {
            tabBtnNlp.classList.add("active");
            tabBtnDb.classList.remove("active");
            nlpTab.classList.add("active");
            dbTab.classList.remove("active");
        } else {
            tabBtnNlp.classList.remove("active");
            tabBtnDb.classList.add("active");
            nlpTab.classList.remove("active");
            dbTab.classList.add("active");
            fetchDatabase(); // Refresh DB list when opening DB Tab
        }
    }

    // Chat Window functions
    function appendMessage(text, isUser = false) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.innerHTML = isUser ? '<i class="fa-regular fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.innerHTML = text;

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Suggested Queries click handling
    queryChips.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (chip) {
            const query = chip.dataset.query;
            chatInput.value = query;
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Clear Chat
    btnClearChat.addEventListener("click", () => {
        chatWindow.innerHTML = `
            <div class="message bot-message">
                <div class="avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="message-bubble">
                    Chào bạn! Tôi đã dọn dẹp hội thoại. Bây giờ bạn muốn tìm hiểu thông tin về xe điện nào?
                </div>
            </div>
        `;
    });

    // Main Chat Form Submit Flow
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        // Reset input immediately
        chatInput.value = "";

        // Append User message to UI
        appendMessage(message, true);

        // Add typing indicator
        const typingDiv = document.createElement("div");
        typingDiv.className = "message bot-message typing-indicator-msg";
        typingDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-bubble">
                <i class="fa-solid fa-ellipsis fa-bounce"></i> Đang phân tích cú pháp NLP...
            </div>
        `;
        chatWindow.appendChild(typingDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message })
            });

            // Remove typing indicator
            const typingMsg = chatWindow.querySelector(".typing-indicator-msg");
            if (typingMsg) typingMsg.remove();

            if (!response.ok) {
                const errorData = await response.json();
                appendMessage(`Lỗi hệ thống: ${errorData.detail || "Không rõ nguyên nhân"}`);
                return;
            }

            const data = await response.json();
            
            // Append Bot answer to UI
            appendMessage(data.answer);

            // Update NLP Diagnostic View
            updateDiagnostics(data.nlp_pipeline, data.query_log);

            // If we are currently in database tab, update it just in case
            if (dbTab.classList.contains("active")) {
                fetchDatabase();
            }

        } catch (err) {
            const typingMsg = chatWindow.querySelector(".typing-indicator-msg");
            if (typingMsg) typingMsg.remove();
            appendMessage(`Lỗi kết nối server: ${err.message}. Đảm bảo uvicorn server đang chạy!`);
        }
    });

    // Update Diagnostics Dashboard Elements
    function updateDiagnostics(nlp, log) {
        const lat = nlp.latency;

        // 1. Latency Times & Bars
        valTokenizer.textContent = `${lat.tokenizer_ms} ms`;
        valTagger.textContent = `${lat.pos_tagger_ms} ms`;
        valNer.textContent = `${lat.ner_ms} ms`;
        valParser.textContent = `${lat.parser_ms} ms`;
        valTotal.textContent = `${lat.total_ms} ms`;

        // Scale bar widths based on latency proportion (max is capped for aesthetic scaling)
        const scale = 20; // 1ms = 20%
        pbTokenizer.style.width = `${Math.min(100, lat.tokenizer_ms * scale)}%`;
        pbTagger.style.width = `${Math.min(100, lat.pos_tagger_ms * scale)}%`;
        pbNer.style.width = `${Math.min(100, lat.ner_ms * scale)}%`;
        pbParser.style.width = `${Math.min(100, lat.parser_ms * scale)}%`;

        // 2. Tokenizer Visualizer
        visualizerTokenizer.innerHTML = "";
        nlp.tokens.forEach(tok => {
            const span = document.createElement("span");
            span.className = "tok-box";
            span.textContent = tok;
            visualizerTokenizer.appendChild(span);
        });

        // 3. POS Tagger Visualizer
        visualizerTagger.innerHTML = "";
        nlp.pos_tags.forEach(item => {
            const div = document.createElement("div");
            div.className = `pos-box pos-${item.pos}`;
            
            const tokSpan = document.createElement("span");
            tokSpan.textContent = item.token;
            
            const tagSpan = document.createElement("span");
            tagSpan.className = "pos-tag";
            tagSpan.textContent = item.pos;
            
            div.appendChild(tokSpan);
            div.appendChild(tagSpan);
            visualizerTagger.appendChild(div);
        });

        // 4. Parser Visualizer
        const p = nlp.parser;
        // Subject rendering
        if (Array.isArray(p.subject)) {
            parserSubject.innerHTML = p.subject.map(s => `<span class="ner-label">${s}</span>`).join(" ");
        } else if (p.subject) {
            parserSubject.innerHTML = `<span class="ner-label">${p.subject}</span>`;
        } else {
            parserSubject.textContent = "-";
        }

        // Action rendering
        parserAction.innerHTML = p.action ? `<span class="pos-key pos-V">${p.action}</span>` : "-";

        // Conditions rendering
        if (p.conditions && p.conditions.length > 0) {
            parserConditions.innerHTML = p.conditions.map(c => 
                `<span class="pos-key pos-M">${c.field} ${c.operator} ${c.value}</span>`
            ).join(" ");
        } else {
            parserConditions.textContent = "Không có";
        }

        // Target Attribute rendering
        if (p.target_attribute) {
            const attr = p.target_attribute;
            const styleClass = attr.field === 'price' ? 'pos-A' : 'pos-Np';
            parserAttribute.innerHTML = `<span class="pos-key ${styleClass}">${attr.type}(${attr.field})</span>`;
        } else {
            parserAttribute.textContent = "-";
        }

        // 5. NER Visualizer
        visualizerNer.innerHTML = "";
        if (nlp.entities && nlp.entities.length > 0) {
            nlp.entities.forEach(ent => {
                const box = document.createElement("div");
                box.className = "ner-box";
                box.dataset.label = ent.label;

                const textSpan = document.createElement("span");
                textSpan.className = "ner-text";
                textSpan.textContent = ent.entity;

                const labelSpan = document.createElement("span");
                labelSpan.className = "ner-label";
                labelSpan.textContent = ent.label;

                const descSpan = document.createElement("span");
                descSpan.className = "ner-desc";
                descSpan.textContent = ent.description;

                box.appendChild(textSpan);
                box.appendChild(labelSpan);
                box.appendChild(descSpan);
                visualizerNer.appendChild(box);
            });
        } else {
            visualizerNer.innerHTML = `<span class="placeholder-text">Không tìm thấy thực thể nào trong câu.</span>`;
        }

        // 6. DB Query Process Log Visualizer
        decisionFlow.innerHTML = "";
        if (log && log.length > 0) {
            log.forEach(step => {
                const div = document.createElement("div");
                div.className = "flow-step";
                div.innerHTML = `<i class="fa-solid fa-circle-chevron-right"></i> <span>${step}</span>`;
                decisionFlow.appendChild(div);
            });
        } else {
            decisionFlow.innerHTML = `<div class="flow-step"><i class="fa-solid fa-check"></i> <span>Không cần lọc điều kiện DB, truy vấn thông tin trực tiếp hoặc trả về câu trả lời mặc định.</span></div>`;
        }
    }

    // DATABASE MANAGER FUNCTIONS
    async function fetchDatabase() {
        try {
            const res = await fetch("/api/database");
            const data = await res.json();
            renderDatabaseTable(data);
        } catch (err) {
            console.error("Lỗi lấy danh sách cơ sở dữ liệu:", err);
        }
    }

    function renderDatabaseTable(cars) {
        dbTableBody.innerHTML = "";
        if (cars.length === 0) {
            dbTableBody.innerHTML = `<tr><td colspan="4" class="text-dim text-center">CSDL trống!</td></tr>`;
            return;
        }

        cars.forEach(car => {
            const tr = document.createElement("tr");
            
            const tdName = document.createElement("td");
            tdName.innerHTML = `<strong>${car.name}</strong>`;
            
            const tdPrice = document.createElement("td");
            tdPrice.textContent = `${car.price} triệu VNĐ`;
            
            const tdRange = document.createElement("td");
            tdRange.textContent = `${car.range} km`;
            
            const tdAction = document.createElement("td");
            const btnDel = document.createElement("button");
            btnDel.className = "btn-delete";
            btnDel.innerHTML = `<i class="fa-solid fa-trash"></i>`;
            btnDel.title = `Xóa ${car.name}`;
            btnDel.addEventListener("click", () => deleteCar(car.name));
            tdAction.appendChild(btnDel);

            tr.appendChild(tdName);
            tr.appendChild(tdPrice);
            tr.appendChild(tdRange);
            tr.appendChild(tdAction);
            dbTableBody.appendChild(tr);
        });
    }

    // Add / Update Car in CSDL
    dbForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = carName.value.trim();
        const price = parseFloat(carPrice.value);
        const range = parseInt(carRange.value);

        if (!name || isNaN(price) || isNaN(range)) return;

        formMessage.className = "form-message";
        formMessage.textContent = "Đang lưu...";

        try {
            const res = await fetch("/api/database", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, price, range })
            });

            const data = await res.json();
            if (res.ok) {
                formMessage.className = "form-message success";
                formMessage.textContent = `Đã lưu thành công xe ${data.data.name}!`;
                dbForm.reset();
                fetchDatabase(); // Refresh database list
                
                // Cập nhật chip gợi ý thêm xe vừa tạo
                addNewQueryChip(data.data.name);

                setTimeout(() => { formMessage.textContent = ""; }, 4000);
            } else {
                formMessage.className = "form-message error";
                formMessage.textContent = `Lỗi: ${data.detail}`;
            }
        } catch (err) {
            formMessage.className = "form-message error";
            formMessage.textContent = `Lỗi kết nối: ${err.message}`;
        }
    });

    // Delete a Car from CSDL
    async function deleteCar(name) {
        if (!confirm(`Bạn có chắc chắn muốn xóa dòng xe ${name} ra khỏi cơ sở dữ liệu?`)) return;

        try {
            const res = await fetch(`/api/database/${name}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (res.ok) {
                fetchDatabase();
            } else {
                alert(`Lỗi khi xóa: ${data.detail}`);
            }
        } catch (err) {
            alert(`Lỗi kết nối: ${err.message}`);
        }
    }

    // Dynamic chip creation helpers
    function addNewQueryChip(name) {
        // Tránh trùng lặp chip
        const queryText = `"${name} giá bao nhiêu?"`;
        const exists = Array.from(queryChips.querySelectorAll(".chip")).some(c => c.dataset.query.includes(name));
        if (!exists) {
            const newChip = document.createElement("button");
            newChip.className = "chip";
            newChip.dataset.query = `${name} giá bao nhiêu?`;
            newChip.textContent = queryText;
            queryChips.appendChild(newChip);
        }
    }

    // Initial Database list pull
    fetchDatabase();
});
