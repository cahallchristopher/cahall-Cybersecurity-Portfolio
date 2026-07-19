// PhishGuard Training Script 5 — Reset Weights to Defaults
// HOW TO USE: right-click PhishGuard popup → Inspect → Console → paste

const DEFAULT_WEIGHTS = {
  https: 2, keywords: 1, blacklist: 3, redirects: 2,
  subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1
};

chrome.storage.local.get('weights', async function(data) {
  console.log('Current weights:', JSON.stringify(data.weights));
  await chrome.storage.local.set({ weights: DEFAULT_WEIGHTS });
  console.log('Weights reset to defaults:', JSON.stringify(DEFAULT_WEIGHTS));
  console.log('Run train-1-url-patterns.js to retrain from scratch.');
});
