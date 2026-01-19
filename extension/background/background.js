/* =====================================================
   STATE
===================================================== */
const lastSafeURLPerTab = {};

/* =====================================================
   HELPERS
===================================================== */
function getBaseDomain(hostname) {
    const parts = hostname.split(".");
    if (parts.length <= 2) return hostname;
    return parts.slice(-2).join(".");
}

function isSearchEnginePage(url) {
    try {
        const host = new URL(url).hostname;
        return [
            "google.com",
            "www.google.com",
            "bing.com",
            "www.bing.com",
            "duckduckgo.com",
            "www.duckduckgo.com",
            "search.yahoo.com"
        ].includes(host);
    } catch {
        return false;
    }
}

/* =====================================================
   SAFE MESSAGE SENDER (MV3)
===================================================== */
function sendToTab(tabId, message) {
    chrome.tabs.sendMessage(tabId, message, () => {
        if (chrome.runtime.lastError) {
            // Content script may not exist yet — safe to ignore
        }
    });
}

/* =====================================================
   MESSAGE HANDLERS
===================================================== */
chrome.runtime.onMessage.addListener((message) => {

    /* -------- TRUST DOMAIN PERMANENTLY -------- */
    if (message.type === "TRUST_DOMAIN_PERMANENT" && message.url) {
        try {
            const hostname = new URL(message.url).hostname;
            const baseDomain = getBaseDomain(hostname);

            chrome.storage.local.get({ trustedDomains: {} }, (data) => {
                data.trustedDomains[baseDomain] = true;
                chrome.storage.local.set({ trustedDomains: data.trustedDomains });
            });
        } catch {}
        return;
    }

    /* -------- REMOVE TRUST -------- */
    if (message.type === "UNTRUST_DOMAIN" && message.domain) {
    chrome.storage.local.get(
        { trustedDomains: {}, bypassURL: null },
        (data) => {
            delete data.trustedDomains[message.domain];

            chrome.storage.local.set({
                trustedDomains: data.trustedDomains,
                bypassURL: null
            });
        }
    );
    return;
}


    /* -------- FORCE WARNING PAGE -------- */
    if (message.type === "FORCE_WARNING_PAGE") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (!tabs.length) return;
            chrome.tabs.update(tabs[0].id, {
                url: chrome.runtime.getURL("warnings/warning.html")
            });
        });
    }
});

/* =====================================================
   NAVIGATION LISTENER
===================================================== */
chrome.webNavigation.onBeforeNavigate.addListener(
    async (details) => {
        if (details.frameId !== 0) return;

        const { detectionEnabled } = await chrome.storage.local.get({
            detectionEnabled: true
        });
        if (!detectionEnabled) return;

        const url = details.url;
        if (!/^https?:\/\//i.test(url)) return;
        if (isSearchEnginePage(url)) return;

        /* =================================================
           USER-TRUSTED DOMAIN → DELAYED TRUSTED POPUP
        ================================================= */
        try {
            const { trustedDomains = {} } =
                await chrome.storage.local.get(["trustedDomains"]);

            const hostname = new URL(url).hostname;
            const baseDomain = getBaseDomain(hostname);

            if (trustedDomains[baseDomain]) {
                const tabId = details.tabId;

                const listener = (updatedTabId, info) => {
                    if (updatedTabId === tabId && info.status === "complete") {
                        sendToTab(tabId, {
                            type: "TRUSTED_SITE_POPUP",
                            domain: baseDomain
                        });
                        chrome.tabs.onUpdated.removeListener(listener);
                    }
                };

                chrome.tabs.onUpdated.addListener(listener);
                return; // ⛔ skip ML & warnings
            }
        } catch {}

        /* =================================================
           ONE-TIME BYPASS
        ================================================= */
        const { bypassURL } = await chrome.storage.local.get(["bypassURL"]);
        if (bypassURL === url) {
            await chrome.storage.local.remove("bypassURL");
            return;
        }

        /* =================================================
           ML PREDICTION
        ================================================= */
        try {
            const response = await fetch("http://127.0.0.1:8000/predict/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            if (!response.ok) throw new Error("API error");

            const result = await response.json();

            /* 🚨 PHISHING */
            if (result.prediction === true) {
                const fallbackURL =
                    lastSafeURLPerTab[details.tabId] || "chrome://newtab/";

                await chrome.storage.local.set({
                    lastCheckedURL: url,
                    fallbackURL,
                    lastDecision: "phishing",
                    confidence: result.probability
                });

                chrome.tabs.update(details.tabId, {
                    url: chrome.runtime.getURL("warnings/warning.html")
                });
                return;
            }

            /* ✅ SAFE (MODEL-BASED) */
            lastSafeURLPerTab[details.tabId] = url;

            await chrome.storage.local.set({
                lastCheckedURL: url,
                lastDecision: "safe",
                confidence: result.probability
            });

            const tabId = details.tabId;
            const listener = (updatedTabId, info) => {
                if (updatedTabId === tabId && info.status === "complete") {
                    sendToTab(tabId, {
                        type: "SAFE_SITE",
                        confidence: result.probability
                    });
                    chrome.tabs.onUpdated.removeListener(listener);
                }
            };
            chrome.tabs.onUpdated.addListener(listener);

        } catch (err) {
            console.error("Phishing API error:", err);
        }
    },
    { url: [{ schemes: ["http", "https"] }] }
);
