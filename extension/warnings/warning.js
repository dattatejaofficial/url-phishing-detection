document.addEventListener("DOMContentLoaded", () => {
    const urlDiv = document.getElementById("phishingUrl");
    const confidenceDiv = document.getElementById("confidenceScore");
    const goBackBtn = document.getElementById("goBack");
    const proceedBtn = document.getElementById("proceedAnyway");

    chrome.storage.local.get(
        ["lastCheckedURL", "confidence"],
        (data) => {
            urlDiv.innerText = data.lastCheckedURL || "Unknown URL";

            if (typeof data.confidence === "number") {
                confidenceDiv.innerText =
                    `Risk Confidence: ${Math.round(data.confidence * 100)}%`;
            } else {
                confidenceDiv.innerText = "Risk Confidence: Unknown";
            }
        }
    );

    /* ✅ GO BACK (SPA SAFE) */
    goBackBtn.addEventListener("click", () => {
        chrome.storage.local.get(["fallbackURL"], (data) => {
            const target = data.fallbackURL || "chrome://newtab/";

            chrome.tabs.query(
                { active: true, currentWindow: true },
                (tabs) => {
                    chrome.tabs.update(tabs[0].id, { url: target });
                }
            );
        });
    });

    /* 🔓 PROCEED ANYWAY (ONE-TIME BYPASS) */
    proceedBtn.addEventListener("click", () => {
        chrome.storage.local.get(["lastCheckedURL"], (data) => {
            if (!data.lastCheckedURL) return;

            chrome.storage.local.set(
                { bypassURL: data.lastCheckedURL },
                () => {
                    window.location.href = data.lastCheckedURL;
                }
            );
        });
    });
});
