const FEEDBACK_API = "http://127.0.0.1:8000/feedback";

document.addEventListener("DOMContentLoaded", () => {
    const urlDiv = document.getElementById("phishingUrl");
    const confidenceDiv = document.getElementById("confidenceScore");
    const goBackBtn = document.getElementById("goBack");
    const proceedBtn = document.getElementById("proceedAnyway");
    const notPhishingBtn = document.getElementById("notPhishing");

    chrome.storage.local.get(
        ["lastCheckedURL", "confidence", "fallbackURL", "developerMode"],
        (data) => {
            if (urlDiv) urlDiv.innerText = data.lastCheckedURL || "Unknown URL";
            if (confidenceDiv) {
                confidenceDiv.innerText =
                    typeof data.confidence === "number"
                        ? `Risk Confidence: ${Math.round(data.confidence * 100)}%`
                        : "Risk Confidence: Unknown";
            }
            if (!data.developerMode && notPhishingBtn) {
                notPhishingBtn.style.display = "none";
            }
        }
    );

    if (goBackBtn) {
        goBackBtn.addEventListener("click", () => {
            chrome.storage.local.get(["fallbackURL"], (data) => {
                const target = data.fallbackURL || "chrome://newtab/";
                chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                    chrome.tabs.update(tabs[0].id, { url: target });
                });
            });
        });
    }

    if (proceedBtn) {
        proceedBtn.addEventListener("click", proceedAnyway);
    }

    if (notPhishingBtn) {
        notPhishingBtn.addEventListener("click", async () => {
            chrome.storage.local.get(
                ["lastCheckedURL", "confidence"],
                async (data) => {
                    if (!data.lastCheckedURL) return;

                    await sendFeedback({
                        url: data.lastCheckedURL,
                        model_prediction: "phishing",
                        user_label: "legitimate",
                        confidence: data.confidence
                    });

                    chrome.runtime.sendMessage({
                        type: "TRUST_DOMAIN_PERMANENT",
                        url: data.lastCheckedURL
                    });
                    
                    chrome.storage.local.set(
                        { bypassURL: data.lastCheckedURL },
                        () => {
                            alert("Thanks! Feedback recorded.");
                            window.location.href = data.lastCheckedURL;
                        }
                    );
                }
            );
        });
    }
});

function proceedAnyway() {
    chrome.storage.local.get(["lastCheckedURL"], (data) => {
        if (!data.lastCheckedURL) return;
        chrome.storage.local.set(
            { bypassURL: data.lastCheckedURL },
            () => {
                window.location.href = data.lastCheckedURL;
            }
        );
    });
}

async function sendFeedback(payload) {
    try {
        await fetch(FEEDBACK_API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
    } catch (err) {
        console.error("Feedback error:", err);
    }
}
