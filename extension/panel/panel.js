document.addEventListener("DOMContentLoaded", init);

function init() {
  const versionText = document.getElementById("versionText");
  const protectedCountEl = document.getElementById("protectedCount");

  const toggleDetection = document.getElementById("toggleDetection");
  const toggleText = document.getElementById("toggleText");
  const statusIndicator = document.getElementById("statusIndicator");

  const devToggle = document.getElementById("developerMode");
  const trustedList = document.getElementById("trustedList");
  const clearAllBtn = document.getElementById("clearAllBtn");

  const trustedInput = document.getElementById("trustedInput");
  const addBtn = document.getElementById("addBtn");
  const removeBtn = document.getElementById("removeBtn");

  const toast = document.getElementById("toast");

  let selectedDomain = null;
  let trustedDomainsCache = {};

  const manifest = chrome.runtime.getManifest();
  versionText.textContent = `Version ${manifest.version}`;

  chrome.storage.local.get(
    {
      detectionEnabled: true,
      developerMode: false,
      trustedDomains: {},
      sitesProtectedCount: 0
    },
    ({ detectionEnabled, developerMode, trustedDomains, sitesProtectedCount }) => {
      toggleDetection.checked = detectionEnabled;
      devToggle.checked = developerMode;
      trustedDomainsCache = { ...trustedDomains };
      protectedCountEl.textContent = sitesProtectedCount;

      updateDetectionUI(detectionEnabled);
      renderTrustedDomains(trustedDomainsCache);
    }
  );

  toggleDetection.addEventListener("change", () => {
    const enabled = toggleDetection.checked;
    chrome.storage.local.set({ detectionEnabled: enabled });
    updateDetectionUI(enabled);
  });

  devToggle.addEventListener("change", () => {
    chrome.storage.local.set({ developerMode: devToggle.checked });
    if (devToggle.checked) {
      showToast("Developer Mode enabled. Feedback actions may send URLs.");
    }
  });

  clearAllBtn.addEventListener("click", () => {
    if (!confirm("Clear all trusted websites?")) return;
    trustedDomainsCache = {};
    chrome.storage.local.set({ trustedDomains: {} }, () => {
      renderTrustedDomains(trustedDomainsCache);
    });
  });

  trustedInput.addEventListener("input", () => {
    addBtn.disabled = !isValidDomain(trustedInput.value.trim());
  });

  addBtn.addEventListener("click", () => {
    const domain = extractDomain(trustedInput.value.trim());
    trustedDomainsCache[domain] = true;

    chrome.storage.local.set(
      { trustedDomains: trustedDomainsCache },
      () => {
        trustedInput.value = "";
        addBtn.disabled = true;
        renderTrustedDomains(trustedDomainsCache);
      }
    );
  });

  removeBtn.addEventListener("click", () => {
    if (!selectedDomain) return;

    chrome.runtime.sendMessage({
      type: "UNTRUST_DOMAIN",
      domain: selectedDomain
    });

    delete trustedDomainsCache[selectedDomain];
    selectedDomain = null;
    removeBtn.disabled = true;
    renderTrustedDomains(trustedDomainsCache);
  });

  function updateDetectionUI(enabled) {
    toggleText.textContent = enabled
      ? "Protection Enabled"
      : "Protection Disabled";
    statusIndicator.className = enabled ? "indicator on" : "indicator off";
  }

  function renderTrustedDomains(domains) {
    trustedList.innerHTML = "";
    const entries = Object.keys(domains);

    if (!entries.length) {
      trustedList.innerHTML = "<div>No trusted websites</div>";
      return;
    }

    entries.forEach((domain) => {
      const row = document.createElement("div");
      row.className = "trusted-item";
      row.textContent = domain;

      if (domain === selectedDomain) row.classList.add("selected");

      row.addEventListener("click", () => {
        selectedDomain = domain;
        removeBtn.disabled = false;
        renderTrustedDomains(domains);
      });

      trustedList.appendChild(row);
    });
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 3000);
  }
}

function isValidDomain(value) {
  return /^(https?:\/\/)?([a-z0-9-]+\.)+[a-z]{2,}$/i.test(value);
}

function extractDomain(value) {
  try {
    return new URL(value.startsWith("http") ? value : "https://" + value)
      .hostname.replace(/^www\./, "");
  } catch {
    return value;
  }
}
