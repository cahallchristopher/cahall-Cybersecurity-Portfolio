// PhishGuard Training Script 1 — URL Pattern Training
// HOW TO USE:
//   1. Click the PhishGuard icon to open the popup
//   2. Right-click inside the popup → Inspect
//   3. Click the Console tab
//   4. Paste this entire script and press Enter

const PHISHING_URLS = [
  'http://paypa1-secure.com/login',
  'https://secure-login.verify-account.xyz/update',
  'http://apple-id-locked.ml/confirm',
  'https://amazon-security-alert.tk/account',
  'http://192.168.1.1/login/verify',
  'https://login.secure.verify.paypal.evil.com/update',
  'http://microsoft-alert.ga/confirm-account',
  'https://google.com/page?redirect=http://steal.com',
  'http://faceb00k-login.cf/secure/account',
  'https://bankofamerica-secure.xyz/verify/login',
  'http://netfl1x-billing.tk/account/update',
  'https://secure.paypal-login.verify.xyz/confirm',
  'http://amazon-prize-winner.ml/claim/account',
  'https://apple-support-alert.ga/verify-now',
  'http://chase-bank-alert.cf/secure/login',
];

const SAFE_URLS = [
  'https://google.com', 'https://github.com', 'https://stackoverflow.com',
  'https://microsoft.com', 'https://apple.com', 'https://amazon.com',
  'https://youtube.com', 'https://linkedin.com', 'https://reddit.com',
  'https://wikipedia.org', 'https://bbc.com', 'https://nytimes.com',
  'https://cloudflare.com', 'https://mozilla.org', 'https://python.org',
];

function scoreUrl(url, weights) {
  let score = 0; let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return 99; }
  let parts = hostname.split('.');
  if (!url.startsWith('https://')) score += weights.https;
  if (['login','verify','secure','account','update','confirm'].some(w => url.toLowerCase().includes(w))) score += weights.keywords;
  if (['redirect=','url=','goto=','next=','return='].some(p => url.toLowerCase().includes(p))) score += weights.redirects;
  if (parts.length > 4) score += weights.subdomains;
  if (['.xyz','.tk','.ml','.ga','.cf'].some(t => hostname.endsWith(t))) score += weights.suspiciousTLD;
  if (url.length > 100) score += weights.longUrl;
  return score;
}

chrome.storage.local.get('weights', async function(data) {
  let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  console.log('Starting weights:', JSON.stringify(weights));
  let correct = 0; let total = 0;
  PHISHING_URLS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score >= 3) { correct++; console.log('✅ Caught:', url, '| score:', score.toFixed(1)); }
    else { Object.keys(weights).forEach(k => { if (k !== 'blacklist') weights[k] = Math.min(5, weights[k] + 0.3); }); console.log('❌ Missed:', url, '| score:', score.toFixed(1)); }
  });
  SAFE_URLS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score === 0) { correct++; console.log('✅ Safe clear:', url); }
    else { Object.keys(weights).forEach(k => { if (k !== 'blacklist') weights[k] = Math.max(0.1, weights[k] - 0.2); }); console.log('⚠️ False positive:', url, '| score:', score.toFixed(1)); }
  });
  await chrome.storage.local.set({ weights });
  console.log('========================================');
  console.log('Accuracy:', correct + '/' + total, '(' + Math.round(correct/total*100) + '%)');
  console.log('Final weights:', JSON.stringify(weights));
});
