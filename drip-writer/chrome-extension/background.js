// Clicking the toolbar icon injects the panel into the current tab.
// Using activeTab + scripting means the extension only touches a page when
// you click the button — no broad "read all your sites" permission.
chrome.action.onClicked.addListener(async (tab) => {
  if (!tab || !tab.id) return;
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
  } catch (e) {
    // Some pages (chrome://, the Web Store, PDF viewer) block injection.
    console.warn("Drip Writer can't run on this page:", e);
  }
});
