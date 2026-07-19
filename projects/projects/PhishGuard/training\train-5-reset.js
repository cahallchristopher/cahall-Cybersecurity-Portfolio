// PhishGuard Training Script 5 â€” Reset Weights to Defaults
// Use this if the weights drift too far and cause too many
// false positives or miss too many threats.
// HOW TO USE:
//   1. Click the PhishGuard icon â†’ right-click â†’ Inspect
//   2. Console tab â†’ paste and press Enter
// ============================================================

const DEFAULT_WEIGHTS = {
  https: 2,
  keywords: 1,
  blacklist: 3,
  redirects: 2,
  subdomains: 1,
  homoglyphs: 2,
  suspiciousTLD: 1,
  longUrl: 1
};

chrome.storage.local.get('weights', async function(data) {
  console.log('Current weights:', JSON.stringify(data.weights));
  await chrome.storage.local.set({ weights: DEFAULT_WEIGHTS });
  console.log('âœ… Weights reset to defaults:', JSON.stringify(DEFAULT_WEIGHTS));
  console.log('Run train-1-url-patterns.js to retrain from scratch.');
});
