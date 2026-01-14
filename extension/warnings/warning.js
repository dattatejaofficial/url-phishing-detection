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
                const percent = Math.round(data.confidence * 100);
                confidenceDiv.innerText = `Risk Confidence: ${percent}%`;
            } else {
                confidenceDiv.innerText = "Risk Confidence: Unknown";
            }
        }
    );

    goBackBtn.addEventListener("click", () => {
        window.history.back();
    });

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