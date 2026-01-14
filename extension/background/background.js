console.log("BACKGROUND VERSION 9.4 — SEARCH ENGINE FIX");

/* =====================================================
   Helper: Identify search engine pages ONLY
===================================================== */
function isSearchEnginePage(url) {
    try {
        const parsed = new URL(url);
        const host = parsed.hostname;

        const searchEngines = [
            "google.com",
            "www.google.com",
            "bing.com",
            "www.bing.com",
            "duckduckgo.com",
            "www.duckduckgo.com",
            "search.yahoo.com"
        ];

        // Skip detection ONLY if user is still on search engine domain
        return searchEngines.includes(host);
    } catch {
        return false;
    }
}

/* =====================================================
   Navigation Listener
===================================================== */
chrome.webNavigation.onBeforeNavigate.addListener(
    async (details) => {
        // Only top-frame navigation
        if (details.frameId !== 0) return;

        // Detection toggle
        const { detectionEnabled } = await chrome.storage.local.get({
            detectionEnabled: true
        });
        if (!detectionEnabled) return;

        const url = details.url;
        console.log("NAV:", url);

        // Allow only http / https
        if (!/^https?:\/\//i.test(url)) return;

        // ❌ Skip search engine pages themselves
        if (isSearchEnginePage(url)) {
            console.log("Skipping search engine page:", url);
            return;
        }

        // 🔓 One-time bypass
        const { bypassURL } = await chrome.storage.local.get(["bypassURL"]);
        if (bypassURL && url === bypassURL) {
            console.log("Bypassing check for:", url);
            await chrome.storage.local.remove("bypassURL");
            return;
        }

        try {
            const response = await fetch("http://127.0.0.1:8000/predict/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                throw new Error(`API error ${response.status}`);
            }

            const result = await response.json();
            console.log("API RESULT:", result);

            /* 🚨 PHISHING */
            if (result.prediction === true) {
                await chrome.storage.local.set({
                    lastCheckedURL: url,
                    lastDecision: "phishing",
                    confidence: result.probability,
                    timestamp: Date.now()
                });

                chrome.tabs.update(details.tabId, {
                    url: chrome.runtime.getURL("warnings/warning.html")
                });
                return;
            }

            /* ✅ SAFE */
            await chrome.storage.local.set({
                lastCheckedURL: url,
                lastDecision: "safe",
                confidence: result.probability,
                timestamp: Date.now()
            });

            // 🟢 Send SAFE popup AFTER page load
            const tabId = details.tabId;

            const listener = (updatedTabId, info) => {
                if (updatedTabId === tabId && info.status === "complete") {
                    chrome.tabs.sendMessage(tabId, {
                        type: "SAFE_SITE",
                        confidence: result.probability
                    });
                    chrome.tabs.onUpdated.removeListener(listener);
                }
            };

            chrome.tabs.onUpdated.addListener(listener);

        } catch (error) {
            console.error("Phishing API error:", error);
        }
    },
    {
        url: [{ schemes: ["http", "https"] }]
    }
);
