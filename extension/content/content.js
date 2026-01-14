let safePopupShown = false;

chrome.runtime.onMessage.addListener((message) => {
    if (message.type !== "SAFE_SITE") return;

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
                  style="cursor:pointer; font-size:16px; font-weight:bold;">
                ×
            </span>
        </div>
        <div style="margin-top:6px;">
            Safety Confidence: ${percent}%
        </div>
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
        minWidth: "220px"
    });

    document.body.appendChild(popup);

    const removePopup = () => {
        popup.remove();
        safePopupShown = false;
    };

    popup.querySelector("#safe-close-btn").onclick = removePopup;

    setTimeout(removePopup, 5000);
});
