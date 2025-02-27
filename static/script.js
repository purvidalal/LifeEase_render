document.addEventListener("DOMContentLoaded", () => {
    const micButton = document.getElementById("micButton");
    const micIcon = document.getElementById("micIcon");
    const textBox = document.querySelector(".text-box");
    const mainInterface = document.getElementById("mainInterface");
    const dashboardInterface = document.getElementById("dashboardInterface");
    const settingsInterface = document.getElementById("settingsInterface");

    // Speech recognition setup
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false; // Single recognition session
    recognition.lang = "en-US";
    let isMuted = true;

    recognition.onstart = function () {
        console.log("Speech recognition started...");
    };

    recognition.onend = function () {
        console.log("Speech recognition stopped...");
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        console.log("Recognized speech:", transcript);
        addChatMessage("user", transcript); // Add user message to chat
        sendToBackend(transcript); // Send transcript to backend
    };

    recognition.onerror = function (event) {
        console.error("Speech recognition error:", event.error);
    };

    // Show the Dashboard interface
    document.getElementById("menuButton").addEventListener("click", () => {
        mainInterface.style.display = "none";
        dashboardInterface.style.display = "block";
    });

    // Show the Settings interface
    document.getElementById("settingsButton").addEventListener("click", () => {
        mainInterface.style.display = "none";
        settingsInterface.style.display = "block";
    });

    // Back arrow functionality for both Dashboard and Settings
    document.querySelectorAll(".back-arrow").forEach((backArrow) => {
        backArrow.addEventListener("click", () => {
            dashboardInterface.style.display = "none";
            settingsInterface.style.display = "none";
            mainInterface.style.display = "block";
        });
    });

    // Toggle mute/unmute functionality for mic with images
    micButton.addEventListener("click", () => {
        isMuted = !isMuted;
        if (!isMuted) {
            micButton.classList.add("muted");
            micIcon.src = "static/unmutemic.jpg"; // Replace with the path to your unmute image
            micIcon.alt = "Unmute";
            console.log("Mic unmuted, starting recording...");
            recognition.start();
        } else {
            micButton.classList.remove("muted");
            micIcon.src = "static/mutemic.jpg"; // Replace with the path to your mute image
            micIcon.alt = "Mute";
            console.log("Mic muted, stopping recording...");
            recognition.stop();
        }
    });

    // Toggle text box expansion
    textBox.addEventListener("click", (event) => {
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

            document.getElementById("closeButton").addEventListener("click", (e) => {
                e.stopPropagation(); // Prevent click from re-expanding
                collapseTextBox();
            });

            document.getElementById("sendMessageButton").addEventListener("click", () => {
                const chatInput = document.getElementById("chatInput");
                const message = chatInput.value.trim();
                if (message) {
                    addChatMessage("user", message); // Add user message to chat
                    chatInput.value = ""; // Clear input field
                    sendToBackend(message); // Send user input to backend
                }
            });
        }
        event.stopPropagation(); // Prevent collapse when clicking inside
    });

    // Collapse the expanded text box when clicking outside
    document.body.addEventListener("click", () => {
        collapseTextBox();
    });

    // Collapse text box function
    function collapseTextBox() {
        if (textBox.classList.contains("expanded")) {
            textBox.classList.remove("expanded");
            textBox.innerHTML = `<span>Tap to type a message...</span>`;
        }
    }

    // Add a chat message to the chat window
    function addChatMessage(sender, message) {
        const chatWindow = textBox.querySelector(".chat-window");
        if (chatWindow) {
            const messageDiv = document.createElement("div");
            messageDiv.classList.add("chat-message", sender === "user" ? "user-message" : "bot-message");
            messageDiv.textContent = message;
            chatWindow.appendChild(messageDiv);

            // Auto-scroll to the bottom
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    }

    // Send the user input to the backend for processing
    function sendToBackend(input) {
        console.log("Sending input to the server...");
        fetch("/process-audio", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ transcript: input }), // Send input as a transcript
        })
            .then((response) => response.json())
            .then((data) => {
                console.log("Response from server:", data.response);
                addChatMessage("bot", data.response || "I'm sorry, I didn't understand that."); // Add bot response to chat

                if (data.audio) {
                    console.log("Playing audio response...");
                    try {
                        const audio = new Audio("data:audio/wav;base64," + data.audio);
                        audio.play().catch((error) => {
                            console.error("Error playing audio:", error);
                            alert("Could not play audio. Please check your system's audio settings.");
                        });
                    } catch (e) {
                        console.error("Audio playback error:", e);
                    }
                } else {
                    console.error("No audio response received from the server.");
                }
            })
            .catch((error) => {
                console.error("Error sending input to server:", error);
            });
    }
});

// Function to request location and send it to Flask
function requestLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                console.log("User Location: ", latitude, longitude);

                // Send location to Flask backend
                fetch('/process-location', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        latitude: latitude,
                        longitude: longitude
                    })
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Location sent successfully:", data);
                })
                .catch(error => {
                    console.error("Error sending location:", error);
                });
            },
            function (error) {
                console.error("Error getting location:", error);
                alert("Location access denied or unavailable. Please enable location in browser settings.");
            }
        );
    } else {
        alert("Geolocation is not supported by your browser.");
    }
}

// ✅ Deep Linking for Apps
document.getElementById("whatsappIcon").addEventListener("click", () => {
    window.location.href = "whatsapp://send?phone="; // Add number if needed
});

document.getElementById("youtubeIcon").addEventListener("click", () => {
    window.location.href = "https://www.youtube.com/";
});

document.getElementById("musicIcon").addEventListener("click", () => {
    window.location.href = "spotify://"; // Spotify deep link
});

document.getElementById("photosIcon").addEventListener("click", () => {
    window.location.href = "googlephotos://"; // Google Photos deep link
});

document.getElementById("newsIcon").addEventListener("click", () => {
    window.location.href = "https://news.google.com/";
});

document.getElementById("gamesIcon").addEventListener("click", () => {
    window.location.href = "https://play.google.com/store";
});

// Call this function when the page loads
window.onload = () => {
    requestLocation();
};