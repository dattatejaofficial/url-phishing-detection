let safePopupShown = false;
let trustedPopupShown = false;

const FEEDBACK_API = "http://127.0.0.1:8000/feedback";

/* =====================================================
   MESSAGE LISTENER
===================================================== */
chrome.runtime.onMessage.addListener((message) => {

    /* =================================================
       SAFE SITE POPUP (MODEL-BASED)
    ================================================= */
    if (message.type === "SAFE_SITE") {
        if (safePopupShown) return;
        safePopupShown = true;

        const percent =
            typeof message.confidence === "number"
                ? Math.round((1 - message.confidence) * 100)
                : "N/A";

        const popup = document.createElement("div");
        popup.id = "safe-site-popup";

        popup.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>✅ Site is Safe</strong>
                <span id="safe-close-btn"
                      style="cursor:pointer; font-size:16px; font-weight:bold;">×</span>
            </div>

            <div style="margin-top:6px;">
                Safety Confidence: ${percent}%
            </div>

            <button id="notLegitBtn"
                style="margin-top:10px;
                       padding:6px 10px;
                       font-size:12px;
                       cursor:pointer;">
                ❌ This is NOT legitimate
            </button>
        `;

        Object.assign(popup.style, {
            position: "fixed",
            bottom: "20px",
            right: "20px",
            backgroundColor: "#e6fffa",
            color: "#065f46",
            padding: "14px 16px",
            borderRadius: "8px",
            fontSize: "14px",
            fontFamily: "Arial, sans-serif",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            zIndex: "999999",
            border: "1px solid #34d399",
            minWidth: "240px"
        });

        document.body.appendChild(popup);

        /* ❌ User says site is NOT legitimate */
        popup.querySelector("#notLegitBtn").onclick = async () => {
            chrome.storage.local.get(
                ["developerMode", "lastCheckedURL", "confidence"],
                async (data) => {

                    // 🔁 Always force warning page
                    chrome.runtime.sendMessage({
                        type: "FORCE_WARNING_PAGE"
                    });

                    // 📡 Send feedback ONLY in dev mode
                    if (data.developerMode) {
                        await fetch(FEEDBACK_API, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                url: data.lastCheckedURL,
                                model_prediction: "legitimate",
                                user_label: "phishing",
                                confidence: data.confidence
                            })
                        });
                    }
                }
            );
        };

        const removePopup = () => {
            popup.remove();
            safePopupShown = false;
        };

        popup.querySelector("#safe-close-btn").onclick = removePopup;
        setTimeout(removePopup, 6000);
    }

    /* =================================================
       TRUSTED SITE POPUP (USER-BASED)
    ================================================= */
    if (message.type === "TRUSTED_SITE_POPUP") {
        if (trustedPopupShown) return;
        trustedPopupShown = true;

        const popup = document.createElement("div");
        popup.id = "trusted-site-popup";

        popup.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>🛡️ Trusted Site</strong>
                <span id="trusted-close-btn"
                      style="cursor:pointer; font-size:16px; font-weight:bold;">×</span>
            </div>

            <div style="margin-top:6px; font-size:13px;">
                You marked <b>${message.domain}</b> as legitimate
            </div>

            <button id="remove-trust-btn"
                style="margin-top:10px;
                       padding:6px 10px;
                       font-size:12px;
                       cursor:pointer;">
                🔁 Remove trust
            </button>
        `;

        Object.assign(popup.style, {
            position: "fixed",
            bottom: "20px",
            right: "20px",
            backgroundColor: "#eef2ff",
            color: "#3730a3",
            padding: "14px 16px",
            borderRadius: "8px",
            fontSize: "14px",
            fontFamily: "Arial, sans-serif",
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            zIndex: "999999",
            border: "1px solid #6366f1",
            minWidth: "240px"
        });

        document.body.appendChild(popup);

        /* ❌ Close popup only */
        popup.querySelector("#trusted-close-btn").onclick = () => {
            popup.remove();
            trustedPopupShown = false;
        };

        /* 🔁 Remove trust permanently */
        popup.querySelector("#remove-trust-btn").onclick = () => {
            chrome.runtime.sendMessage({
                type: "UNTRUST_DOMAIN",
                domain: message.domain
            });

            popup.remove();
            trustedPopupShown = false;
            alert(`Trust removed for ${message.domain}`);
        };

        /* ⏱️ Auto-hide */
        setTimeout(() => {
            popup.remove();
            trustedPopupShown = false;
        }, 6000);
    }
});

/* =====================================================
   Feedback helper
===================================================== */
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
