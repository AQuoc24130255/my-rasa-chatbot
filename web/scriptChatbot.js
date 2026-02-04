document.addEventListener("DOMContentLoaded", () => {
    const launcher = document.getElementById("chat-launcher");
    const chatContainer = document.getElementById("chatbot-container");
    const closeBtn = document.getElementById("close-chat");
    const sendBtn = document.getElementById("send-btn");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    // Thay URL này bằng link Codespace của bạn nếu chạy trên GitHub
    const RASA_API_URL = "https://ideal-trout-r7p69j7v5gwf594w-5005.app.github.dev/webhooks/rest/webhook";
    // 1. CHỨC NĂNG ẨN/HIỆN
    launcher.addEventListener("click", () => {
        chatContainer.classList.remove("hidden");
        launcher.style.display = "none"; // Ẩn nút launcher khi mở chat
    });

    closeBtn.addEventListener("click", () => {
        chatContainer.classList.add("hidden");
        setTimeout(() => { launcher.style.display = "flex"; }, 300); // Hiện lại nút sau khi chat ẩn xong
    });

    // 2. CHỨC NĂNG GỬI TIN & KẾT NỐI RASA
    function appendMessage(text, side) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${side}`;
        msgDiv.innerText = text;
        chatBox.appendChild(msgDiv);

        // Cuộn mượt xuống cuối
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
    }

    // 3. HIỂN THỊ NÚT BẤM (QUAN TRỌNG)
    function appendButtons(buttons) {
        const btnContainer = document.createElement("div");
        btnContainer.className = "button-container";

        buttons.forEach(button => {
            const btn = document.createElement("button");
            btn.className = "chat-btn";
            btn.innerText = button.title;
            
            // Khi nhấn nút, gửi payload ẩn về Rasa
            btn.addEventListener("click", () => {
                appendMessage(button.title, "user"); // Hiện tên nút lên màn hình như tin nhắn người dùng
                sendToRasa(button.payload);         // Gửi payload (ví dụ: /ask_all_products)
                btnContainer.remove();               // Xóa cụm nút sau khi đã chọn
            });
            
            btnContainer.appendChild(btn);
        });

        chatBox.appendChild(btnContainer);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: "smooth" });
    }

    // 4. LOGIC GỬI DỮ LIỆU ĐẾN RASA
    async function sendToRasa(message) {
        try {
            const response = await fetch(RASA_API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sender: "user_web", message: message }),
            });
            const data = await response.json();
            
            data.forEach(res => { 
                if (res.text) appendMessage(res.text, "bot"); 
                if (res.buttons) appendButtons(res.buttons); // Kiểm tra và hiển thị nút bấm
            });
        } catch (error) {
            appendMessage("Lỗi kết nối Rasa server!", "bot");
        }
    }

    // 5. XỬ LÝ KHI NGƯỜI DÙNG GÕ PHÍM
    function handleSend() {
        const message = userInput.value.trim();
        if (!message) return;

        appendMessage(message, "user");
        userInput.value = "";
        sendToRasa(message);
    }

    sendBtn.addEventListener("click", handleSend);
    userInput.addEventListener("keypress", (e) => { if (e.key === "Enter") handleSend(); });
});