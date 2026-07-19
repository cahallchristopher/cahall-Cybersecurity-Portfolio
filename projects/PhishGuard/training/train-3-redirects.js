// PhishGuard Training Script 3 — Redirect Chain Training
// Trains detection of malicious redirect attacks
// HOW TO USE: right-click PhishGuard popup → Inspect → Console → paste

const REDIRECT_PHISHING = [
  'https://google.com/page?redirect=http://evil.com',
  'https://example.com/out?url=https://phish.xyz/login',
  'https://legitimate.com/click?goto=http://steal.ml/account',
  'https://news-site.com/article?next=https://fake-bank.tk/verify',
  'https://shop.com/checkout?return=http://credential-harvest.ga',
  'https://email-link.com/track?redirect=https://paypal-phish.xyz',
  'https://safe-site.com/link?url=http://amazon-fake.ml/login',
  'https://blog.com/post?goto=https://microsoft-support.cf/account',
  'https://forum.com/thread?next=http://apple-locked.tk/verify',
  'https://docs.com/view?return=https://chase-alert.xyz/secure',
];

const SAFE_REDIRECTS = [
  'https://google.com/search?q=phishing',
  'https://github.com/repo?tab=readme',
  'https://amazon.com/products?category=electronics',
  'https://youtube.com/watch?v=abc123',
  'https://twitter.com/user?status=active',
];

function scoreUrl(url, weights) {
  let score = 0; let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return 99; }
  if (!url.startsWith('https://')) score += weights.https;
  if (['login','verify','secure','account','update','confirm'].some(w => url.toLowerCase().includes(w))) score += weights.keywords;
  if (['redirect=','url=','goto=','next=','return='].some(p => url.toLowerCase().includes(p))) score += weights.redirects;
  if (['.xyz','.tk','.ml','.ga','.cf'].some(t => hostname.endsWith(t))) score += weights.suspiciousTLD;
  return score;
}

chrome.storage.local.get('weights', async function(data) {
  let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  console.log('Starting redirect training...');
  let correct = 0; let total = 0;
  REDIRECT_PHISHING.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score >= 3) { correct++; console.log('✅ Caught:', url); }
    else { weights.redirects = Math.min(5, weights.redirects + 0.4); console.log('❌ Missed:', url, '| score:', score.toFixed(1)); }
  });
  SAFE_REDIRECTS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score < 3) { correct++; } else { weights.redirects = Math.max(0.1, weights.redirects - 0.3); console.log('⚠️ False positive:', url); }
  });
  await chrome.storage.local.set({ weights });
  console.log('Accuracy:', correct + '/' + total, '(' + Math.round(correct/total*100) + '%)');
  console.log('Final weights:', JSON.stringify(weights));
});
