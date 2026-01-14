let phishingWarningShown = false;
let safePopupShown = false;

chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "SHOW_PHISHING_WARNING") {

        if (phishingWarningShown) return;
        phishingWarningShown = true;

        const banner = document.createElement("div");
        banner.innerText =
            "⚠️ Warning: This website may be a phishing site. Proceed with caution.";

        Object.assign(banner.style, {
            position: "fixed",
            top: "0",
            left: "0",
            width: "100%",
            padding: "12px",
            backgroundColor: "#b00020",
            color: "#ffffff",
            fontSize: "14px",
            fontWeight: "bold",
            textAlign: "center",
            zIndex: "999999",
            boxShadow: "0 2px 6px rgba(0,0,0,0.3)"
        });

        const closeBtn = document.createElement("span");
        closeBtn.innerText = " ❌";
        closeBtn.style.cursor = "pointer";
        closeBtn.style.marginLeft = "15px";

        closeBtn.onclick = () => banner.remove();

        banner.appendChild(closeBtn);
        document.documentElement.prepend(banner);
    }

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
                      style="cursor:pointer; font-size:16px; font-weight:bold;">
                    ×
                </span>
            </div>
            <div style="margin-top:6px;">
                Confidence: ${percent}%
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

        popup.querySelector("#safe-close-btn").onclick = () => {
            popup.remove();
        };

        setTimeout(() => {
            popup.remove();
        }, 5000);
    }
});