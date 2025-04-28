document.addEventListener("DOMContentLoaded", () => {
    const micButton = document.getElementById("micButton");
    const micIcon = document.getElementById("micIcon");
    const textBox = document.querySelector(".text-box");
    const mainInterface = document.getElementById("mainInterface");
    const dashboardInterface = document.getElementById("dashboardInterface");
    const settingsInterface = document.getElementById("settingsInterface");
    const avatar = document.querySelector(".avatar");

    let speakingInterval;
    let uploadedFilename = null;
    let uploadedImageFile = null;

    function startSpeaking() {
        clearInterval(speakingInterval);
        let toggle = false;
        speakingInterval = setInterval(() => {
            toggle = !toggle;
            avatar.style.backgroundImage = toggle
                ? 'url("/static/image-open.jpg")'
                : 'url("/static/image.jpg")';
        }, 300);
    }

    function stopSpeaking() {
        clearInterval(speakingInterval);
        speakingInterval = null;
        avatar.style.backgroundImage = 'url("/static/image.jpg")';
    }

    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.lang = "en-US";
    let isMuted = true;

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        addChatMessage("user", transcript);
        sendToBackend(transcript);
    };

    micButton.addEventListener("click", () => {
        isMuted = !isMuted;
        if (!isMuted) {
            micButton.classList.add("muted");
            micIcon.src = "static/unmutemic.jpg";
            recognition.start();
        } else {
            micButton.classList.remove("muted");
            micIcon.src = "static/mutemic.jpg";
            recognition.stop();
        }
    });

    document.getElementById("fileUpload").addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const fileType = file.type;

        if (fileType.startsWith("image/")) {
            uploadedImageFile = file;
        } else {
            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch("/upload", {
                    method: "POST",
                    body: formData,
                });

                const data = await response.json();
                if (data.filename) {
                    uploadedFilename = data.filename;
                }
            } catch (err) {
                console.error("Upload error:", err);
            }
        }
    });

    textBox.addEventListener("click", (event) => {
        if (!textBox.classList.contains("expanded") && !textBox.querySelector(".bot-popup")) {
            expandTextBoxWithMessage();
        }
        event.stopPropagation();
    });

    document.body.addEventListener("click", () => {
        collapseTextBox();
    });

    function collapseTextBox() {
        if (textBox.classList.contains("expanded")) {
            textBox.classList.remove("expanded");
            textBox.innerHTML = `<span>Tap to type a message...</span>`;
        }
    }

    function expandTextBoxWithMessage(prefillMessage = "") {
        if (!textBox.classList.contains("expanded")) {
            textBox.classList.add("expanded");
            textBox.innerHTML = `
                <button id="closeButton" class="close-button">&times;</button>
                <div class="chat-window"></div>
                <div class="chat-input">
                    <input type="text" id="chatInput" placeholder="Type your message here..." />
                    <button id="sendMessageButton">Send</button>
                </div>
            `;

            if (prefillMessage) {
                const chatWindow = textBox.querySelector(".chat-window");
                const messageDiv = document.createElement("div");
                messageDiv.classList.add("chat-message", "bot-message");
                messageDiv.textContent = prefillMessage;
                chatWindow.appendChild(messageDiv);
            }

            document.getElementById("closeButton").addEventListener("click", (e) => {
                e.stopPropagation();
                collapseTextBox();
            });

            document.getElementById("sendMessageButton").addEventListener("click", () => {
                const chatInput = document.getElementById("chatInput");
                const message = chatInput.value.trim();
                if (message) {
                    addChatMessage("user", message);
                    chatInput.value = "";
                    sendToBackend(message);
                }
            });
        }
    }

    function addChatMessage(sender, message) {
        const chatWindow = textBox.querySelector(".chat-window");
        if (chatWindow) {
            const messageDiv = document.createElement("div");
            messageDiv.classList.add("chat-message", sender === "user" ? "user-message" : "bot-message");
            messageDiv.textContent = message;
            chatWindow.appendChild(messageDiv);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    }

    function showBotPopup(message) {
        if (!textBox.classList.contains("expanded")) {
            textBox.innerHTML = "";
            const popup = document.createElement("div");
            popup.classList.add("bot-popup");
            popup.textContent = message;
            textBox.appendChild(popup);
            popup.addEventListener("click", (event) => {
                event.stopPropagation();
                expandTextBoxWithMessage(message);
            });
        }
    }

    function hideBotPopup() {
        const popup = textBox.querySelector(".bot-popup");
        if (popup) popup.remove();
        if (!textBox.classList.contains("expanded")) {
            textBox.innerHTML = `<span>Tap to type a message...</span>`;
        }
    }

    function sendToBackend(input) {
        console.log("Sending input to the server...");

        if (uploadedImageFile) {
            const formData = new FormData();
            formData.append("image", uploadedImageFile);
            formData.append("prompt", input);

            fetch("/upload-image", {
                method: "POST",
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => {
                    const botMessage = data.response || "I'm sorry, I couldn't understand the image.";
                    addChatMessage("bot", botMessage);
                    showBotPopup(botMessage);

                    if (data.audio) {
                        const audio = new Audio("data:audio/wav;base64," + data.audio);
                        startSpeaking();
                        audio.play().catch((e) => console.error("Audio error:", e));
                        audio.addEventListener("ended", () => {
                            stopSpeaking();
                            setTimeout(hideBotPopup, 5000);
                        });
                    } else {
                        setTimeout(hideBotPopup, 5000);
                    }

                    uploadedImageFile = null;
                })
                .catch((error) => {
                    console.error("Vision error:", error);
                    addChatMessage("bot", "Error analyzing the image.");
                });
            return;
        }

        const endpoint = uploadedFilename ? "/qa" : "/process-audio";
        const payload = uploadedFilename
            ? JSON.stringify({ question: input, filename: uploadedFilename })
            : JSON.stringify({ transcript: input });

        fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: payload,
        })
            .then((response) => response.json())
            .then((data) => {
                const botMessage = data.response || "I'm sorry, I didn't understand that.";
                addChatMessage("bot", botMessage);
                showBotPopup(botMessage);

                if (data.audio) {
                    const audio = new Audio("data:audio/wav;base64," + data.audio);
                    startSpeaking();
                    audio.play().catch((e) => console.error("Audio error:", e));
                    audio.addEventListener("ended", () => {
                        stopSpeaking();
                        setTimeout(hideBotPopup, 5000);
                    });
                } else {
                    setTimeout(hideBotPopup, 5000);
                }

                uploadedFilename = null;
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    }

    document.getElementById("menuButton").addEventListener("click", () => {
        mainInterface.style.display = "none";
        dashboardInterface.style.display = "block";
    });

    document.getElementById("settingsButton").addEventListener("click", () => {
        mainInterface.style.display = "none";
        settingsInterface.style.display = "block";
    });

    document.querySelectorAll(".back-arrow").forEach((arrow) => {
        arrow.addEventListener("click", () => {
            dashboardInterface.style.display = "none";
            settingsInterface.style.display = "none";
            mainInterface.style.display = "block";
        });
    });

    function requestLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    fetch('/process-location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                        })
                    })
                        .then((res) => res.json())
                        .then((data) => console.log("Location sent:", data))
                        .catch((err) => console.error("Location error:", err));
                },
                function (error) {
                    alert("Location access denied or unavailable.");
                }
            );
        } else {
            alert("Geolocation is not supported by your browser.");
        }
    }

    requestLocation();

    document.getElementById("whatsappIcon").addEventListener("click", () => {
        window.location.href = "whatsapp://send?phone=";
    });
    document.getElementById("youtubeIcon").addEventListener("click", () => {
        window.location.href = "https://www.youtube.com/";
    });
    document.getElementById("musicIcon").addEventListener("click", () => {
        window.location.href = "spotify://";
    });
    document.getElementById("photosIcon").addEventListener("click", () => {
        window.location.href = "googlephotos://";
    });
    document.getElementById("newsIcon").addEventListener("click", () => {
        window.location.href = "https://news.google.com/";
    });
    document.getElementById("gamesIcon").addEventListener("click", () => {
        window.location.href = "https://play.google.com/store";
    });
});