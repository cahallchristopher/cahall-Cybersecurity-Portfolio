// PhishGuard Training Script 4 â€” TLD Risk Training
// Trains the extension on high-risk top level domains.
// Free TLDs like .xyz .tk .ml .ga .cf are heavily abused
// by phishing campaigns because they cost nothing to register.
// HOW TO USE:
//   1. Click the PhishGuard icon â†’ right-click â†’ Inspect
//   2. Console tab â†’ paste and press Enter
// ============================================================

const HIGH_RISK_TLD_PHISHING = [
  'https://secure-banking.xyz/login',
  'https://paypal-verify.tk/account',
  'https://apple-support.ml/id/verify',
  'https://amazon-prize.ga/claim',
  'https://microsoft-alert.cf/support',
  'https://netflix-billing.xyz/update',
  'https://bank-secure.tk/login',
  'https://gmail-verify.ml/account',
  'https://instagram-verify.ga/login',
  'https://discord-nitro.cf/claim',
  'https://steam-trade.xyz/confirm',
  'https://coinbase-alert.tk/verify',
  'https://binance-secure.ml/login',
  'https://crypto-wallet.ga/recover',
  'https://nft-claim.cf/connect',
];

const LEGITIMATE_TLDS = [
  'https://google.com',
  'https://github.io',
  'https://cloudflare.net',
  'https://bbc.co.uk',
  'https://government.gov',
  'https://university.edu',
  'https://nonprofit.org',
  'https://startup.io',
  'https://developer.dev',
  'https://mysite.me',
];

function scoreUrl(url, weights) {
  let score = 0;
  let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return 99; }
  if (!url.startsWith('https://')) score += weights.https;
  if (['login','verify','secure','account','update','confirm','claim','recover','connect'].some(w => url.toLowerCase().includes(w))) score += weights.keywords;
  if (['.xyz','.tk','.ml','.ga','.cf'].some(t => hostname.endsWith(t))) score += weights.suspiciousTLD;
  return score;
}

chrome.storage.local.get('weights', async function(data) {
  let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  console.log('Starting TLD risk training...');
  console.log('Starting weights:', JSON.stringify(weights));

  let correct = 0; let total = 0;

  HIGH_RISK_TLD_PHISHING.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score >= 3) {
      correct++;
      console.log('âœ… Caught high-risk TLD:', url, '| score:', score.toFixed(1));
    } else {
      weights.suspiciousTLD = Math.min(5, weights.suspiciousTLD + 0.4);
      console.log('âŒ Missed high-risk TLD:', url, '| score:', score.toFixed(1), 'â€” increased TLD weight to', weights.suspiciousTLD.toFixed(1));
    }
  });

  LEGITIMATE_TLDS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score === 0) {
      correct++;
      console.log('âœ… Legitimate TLD clear:', url);
    } else {
      weights.suspiciousTLD = Math.max(0.1, weights.suspiciousTLD - 0.2);
      console.log('âš ï¸ False positive on TLD:', url, '| score:', score.toFixed(1));
    }
  });

  await chrome.storage.local.set({ weights });
  console.log('========================================');
  console.log('TLD training complete. Accuracy:', correct + '/' + total, '(' + Math.round(correct/total*100) + '%)');
  console.log('Final weights:', JSON.stringify(weights));
  console.log('========================================');
});
