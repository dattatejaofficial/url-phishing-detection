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

            // ⭐ CHANGED: do NOT hide button in non-developer mode
            // Trust should be allowed for all users
        }
    );

    /* =========================
       GO BACK (SPA-safe)
    ========================= */
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

    /* =========================
       PROCEED ANYWAY
    ========================= */
    if (proceedBtn) {
        proceedBtn.addEventListener("click", proceedAnyway);
    }

    /* =========================
       NOT PHISHING (TRUST SITE)
    ========================= */
    if (notPhishingBtn) {
        notPhishingBtn.addEventListener("click", async () => {
            chrome.storage.local.get(
                ["lastCheckedURL", "confidence", "developerMode"],
                async (data) => {
                    if (!data.lastCheckedURL) return;

                    // ⭐ ALWAYS trust locally
                    chrome.runtime.sendMessage({
                        type: "TRUST_DOMAIN_PERMANENT",
                        url: data.lastCheckedURL
                    });

                    // ⭐ Send feedback ONLY in developer mode
                    if (data.developerMode) {
                        await sendFeedback({
                            url: data.lastCheckedURL,
                            model_prediction: "phishing",
                            user_label: "legitimate",
                            confidence: data.confidence
                        });
                    }

                    // ⭐ One-time bypass so page opens immediately
                    chrome.storage.local.set(
                        { bypassURL: data.lastCheckedURL },
                        () => {
                            alert("Website marked as legitimate.");
                            window.location.href = data.lastCheckedURL;
                        }
                    );
                }
            );
        });
    }
});

/* =========================
   Proceed Anyway helper
========================= */
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

/* =========================
   Feedback helper
========================= */
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
