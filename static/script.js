document.addEventListener("DOMContentLoaded", () => {
    const micButton = document.getElementById("micButton");
    const micIcon = document.getElementById("micIcon");
    const textBox = document.querySelector(".text-box");
    const mainInterface = document.getElementById("mainInterface");
    const dashboardInterface = document.getElementById("dashboardInterface");
    const settingsInterface = document.getElementById("settingsInterface");

    // 1. Grab the avatar element (assumes your avatar is <div class="avatar"> in HTML)
    const avatar = document.querySelector(".avatar");

    // 2. Create functions to start/stop the talking video
    function startSpeaking() {
        // Hide the static background image so the video is visible
        avatar.style.backgroundImage = "none";
        // If the talking video doesn't exist yet, create and append it
        if (!document.getElementById("talkingVideo")) {
            const video = document.createElement("video");
            video.id = "talkingVideo";
            video.src = "static/talking-avatar.mp4";  // Path to your talking video
            video.loop = true;
            video.muted = true;       // Mute the video's audio if desired
            video.autoplay = true;
            // Position and size the video to cover the avatar container
            video.style.position = "absolute";
            video.style.top = "0";
            video.style.left = "0";
            video.style.width = "100%";
            video.style.height = "100%";
            video.style.objectFit = "cover";
            video.style.zIndex = "1"; // Updated z-index to ensure the video is visible
            avatar.appendChild(video);
        } else {
            // If the video already exists, just show and play it
            const video = document.getElementById("talkingVideo");
            video.style.display = "block";
            video.play();
        }
    }

    function stopSpeaking() {
        // Pause/hide the video so the default avatar image is visible again
        const video = document.getElementById("talkingVideo");
        if (video) {
            video.pause();
            video.style.display = "none";
        }
        // Restore the avatar's static background image
        avatar.style.backgroundImage = 'url("/static/image.jpg")';
    }

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

    // Toggle text box expansion (updated to work with bot popup)
    textBox.addEventListener("click", (event) => {
        // Expand if not already expanded and if there's no bot popup waiting
        if (!textBox.classList.contains("expanded") && !textBox.querySelector(".bot-popup")) {
            expandTextBoxWithMessage();
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
                const botMessage = data.response || "I'm sorry, I didn't understand that.";
                addChatMessage("bot", botMessage);

                // Dynamically create and show the bot response popup in the small text box
                showBotPopup(botMessage);

                if (data.audio) {
                    console.log("Playing audio response...");
                    try {
                        const audio = new Audio("data:audio/wav;base64," + data.audio);

                        // Start showing the talking video
                        startSpeaking();

                        audio.play().catch((error) => {
                            console.error("Error playing audio:", error);
                            alert("Could not play audio. Please check your system's audio settings.");
                            stopSpeaking(); // Hide the video if playback fails
                        });

                        // Once audio finishes, hide the talking video
                        audio.addEventListener('ended', () => {
                            stopSpeaking();
                            // Wait an extra 5 seconds before hiding the popup
                            setTimeout(() => {
                                hideBotPopup();
                            }, 5000);
                        });
                    } catch (e) {
                        console.error("Audio playback error:", e);
                        stopSpeaking();
                    }
                } else {
                    console.error("No audio response received from the server.");
                    // If no audio, still hide the popup after 5 seconds
                    setTimeout(() => {
                        hideBotPopup();
                    }, 5000);
                }
            })
            .catch((error) => {
                console.error("Error sending input to server:", error);
            });
    }

    // Dynamically create and display the bot response popup in the small text box
    function showBotPopup(message) {
        // Only show the popup if the text box is not expanded
        if (!textBox.classList.contains("expanded")) {
            // Clear current content (e.g., the "Tap to type a message..." text)
            textBox.innerHTML = "";
            
            // Create the popup element
            const popup = document.createElement("div");
            popup.classList.add("bot-popup");
            popup.textContent = message;
            
            // Append the popup to the text box
            textBox.appendChild(popup);
            
            // When the popup is clicked, expand the text box with the bot message prefilled
            popup.addEventListener("click", (event) => {
                event.stopPropagation();
                expandTextBoxWithMessage(message);
            });
        }
    }

    // Hide the bot popup if it exists
    function hideBotPopup() {
        const popup = textBox.querySelector(".bot-popup");
        if (popup) {
            popup.remove();
        }
        // If the text box is not expanded, reset it to the default placeholder.
        if (!textBox.classList.contains("expanded")) {
            textBox.innerHTML = `<span>Tap to type a message...</span>`;
        }
    }

    // Expand the text box and prefill it with a message (if provided)
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
            
            // If there is a prefill message, add it to the chat window
            if (prefillMessage) {
                const chatWindow = textBox.querySelector(".chat-window");
                const messageDiv = document.createElement("div");
                messageDiv.classList.add("chat-message", "bot-message");
                messageDiv.textContent = prefillMessage;
                chatWindow.appendChild(messageDiv);
            }
            
            // Bind the close button event
            document.getElementById("closeButton").addEventListener("click", (e) => {
                e.stopPropagation();
                collapseTextBox();
            });
            
            // Bind the send button event
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