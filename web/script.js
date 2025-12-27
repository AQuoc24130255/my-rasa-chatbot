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

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        appendMessage(message, "user");
        userInput.value = "";

        try {
            const response = await fetch("https://ideal-trout-r7p69j7v5gwf594w-5005.app.github.dev/webhooks/rest/webhook", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ sender: "user_web", message: message }),
            });
            const data = await response.json();
            data.forEach(res => { if (res.text) appendMessage(res.text, "bot"); });
        } catch (error) {
            appendMessage("Lỗi kết nối Rasa server!", "bot");
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });
});