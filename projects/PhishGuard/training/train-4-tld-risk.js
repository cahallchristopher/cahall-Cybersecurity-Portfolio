// PhishGuard Training Script 4 — TLD Risk Training
// Trains detection of high-risk free TLDs: .xyz .tk .ml .ga .cf
// HOW TO USE: right-click PhishGuard popup → Inspect → Console → paste

const HIGH_RISK_TLD_PHISHING = [
  'https://secure-banking.xyz/login', 'https://paypal-verify.tk/account',
  'https://apple-support.ml/id/verify', 'https://amazon-prize.ga/claim',
  'https://microsoft-alert.cf/support', 'https://netflix-billing.xyz/update',
  'https://bank-secure.tk/login', 'https://gmail-verify.ml/account',
  'https://instagram-verify.ga/login', 'https://discord-nitro.cf/claim',
  'https://steam-trade.xyz/confirm', 'https://coinbase-alert.tk/verify',
  'https://binance-secure.ml/login', 'https://crypto-wallet.ga/recover',
  'https://nft-claim.cf/connect',
];

const LEGITIMATE_TLDS = [
  'https://google.com', 'https://github.io', 'https://cloudflare.net',
  'https://bbc.co.uk', 'https://government.gov', 'https://university.edu',
  'https://nonprofit.org', 'https://startup.io', 'https://developer.dev',
  'https://mysite.me',
];

function scoreUrl(url, weights) {
  let score = 0; let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return 99; }
  if (!url.startsWith('https://')) score += weights.https;
  if (['login','verify','secure','account','update','confirm','claim','recover','connect'].some(w => url.toLowerCase().includes(w))) score += weights.keywords;
  if (['.xyz','.tk','.ml','.ga','.cf'].some(t => hostname.endsWith(t))) score += weights.suspiciousTLD;
  return score;
}

chrome.storage.local.get('weights', async function(data) {
  let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  console.log('Starting TLD risk training...');
  let correct = 0; let total = 0;
  HIGH_RISK_TLD_PHISHING.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score >= 3) { correct++; console.log('✅ Caught:', url); }
    else { weights.suspiciousTLD = Math.min(5, weights.suspiciousTLD + 0.4); console.log('❌ Missed:', url, '| score:', score.toFixed(1)); }
  });
  LEGITIMATE_TLDS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score === 0) { correct++; } else { weights.suspiciousTLD = Math.max(0.1, weights.suspiciousTLD - 0.2); console.log('⚠️ False positive:', url); }
  });
  await chrome.storage.local.set({ weights });
  console.log('Accuracy:', correct + '/' + total, '(' + Math.round(correct/total*100) + '%)');
  console.log('Final weights:', JSON.stringify(weights));
});
