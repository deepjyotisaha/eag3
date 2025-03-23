chrome.action.onClicked.addListener((tab) => {
  // Open the side panel
  chrome.sidePanel.open({ windowId: tab.windowId });
}); 