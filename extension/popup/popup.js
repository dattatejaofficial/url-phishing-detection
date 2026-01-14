document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("toggleDetection");
    const toggleText = document.getElementById("toggleText");
    const statusIndicator = document.getElementById("statusIndicator");
    const versionText = document.getElementById("versionText");

    /* =========================
       Load version dynamically
    ========================= */
    const manifest = chrome.runtime.getManifest();
    versionText.innerText = `Version ${manifest.version}`;

    /* =========================
       Load detection state
    ========================= */
    chrome.storage.local.get(
        { detectionEnabled: true },
        (data) => {
            toggle.checked = data.detectionEnabled;
            updateUI(data.detectionEnabled);
        }
    );

    /* =========================
       Toggle detection
    ========================= */
    toggle.addEventListener("change", () => {
        const enabled = toggle.checked;

        chrome.storage.local.set({
            detectionEnabled: enabled
        });

        updateUI(enabled);
    });

    /* =========================
       UI helper
    ========================= */
    function updateUI(enabled) {
        if (enabled) {
            toggleText.innerText = "Detection Enabled";
            statusIndicator.className = "indicator on";
        } else {
            toggleText.innerText = "Detection Disabled";
            statusIndicator.className = "indicator off";
        }
    }
});
