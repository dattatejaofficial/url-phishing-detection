document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("toggleDetection");
    const toggleText = document.getElementById("toggleText");
    const statusIndicator = document.getElementById("statusIndicator");
    const versionText = document.getElementById("versionText");

    const devToggle = document.getElementById("developerMode");

    /* Version */
    const manifest = chrome.runtime.getManifest();
    versionText.innerText = `Version ${manifest.version}`;

    /* Load states */
    chrome.storage.local.get(
        { detectionEnabled: true, developerMode: false },
        (data) => {
            toggle.checked = data.detectionEnabled;
            devToggle.checked = data.developerMode;
            updateUI(data.detectionEnabled);
        }
    );

    /* Detection toggle */
    toggle.addEventListener("change", () => {
        const enabled = toggle.checked;
        chrome.storage.local.set({ detectionEnabled: enabled });
        updateUI(enabled);
    });

    /* Developer mode toggle */
    devToggle.addEventListener("change", () => {
        chrome.storage.local.set({
            developerMode: devToggle.checked
        });
    });

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
