// ============================================================
// PhishGuard Training Script 3 â€” Redirect Chain Training
// Trains the extension to catch malicious redirect attacks.
// Attackers use redirects to hide the final destination:
//   safe-looking.com/page?url=http://evil.com/steal
// HOW TO USE:
//   1. Click the PhishGuard icon â†’ right-click â†’ Inspect
//   2. Console tab â†’ paste and press Enter
// ============================================================

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
  let score = 0;
  let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return 99; }
  if (!url.startsWith('https://')) score += weights.https;
  if (['login','verify','secure','account','update','confirm'].some(w => url.toLowerCase().includes(w))) score += weights.keywords;
  if (['redirect=','url=','goto=','next=','return='].some(p => url.toLowerCase().includes(p))) score += weights.redirects;
  if (['.xyz','.tk','.ml','.ga','.cf'].some(t => {
    try { return new URL(decodeURIComponent(url.split('=')[1] || '')).hostname.endsWith(t); } catch(e) { return false; }
  })) score += weights.suspiciousTLD;
  return score;
}

chrome.storage.local.get('weights', async function(data) {
  let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  console.log('Starting redirect training...');
  console.log('Starting weights:', JSON.stringify(weights));

  let correct = 0; let total = 0;

  REDIRECT_PHISHING.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score >= 3) {
      correct++;
      console.log('âœ… Caught redirect attack:', url, '| score:', score.toFixed(1));
    } else {
      weights.redirects = Math.min(5, weights.redirects + 0.4);
      console.log('âŒ Missed redirect:', url, '| score:', score.toFixed(1), 'â€” increased redirect weight to', weights.redirects.toFixed(1));
    }
  });

  SAFE_REDIRECTS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score < 3) {
      correct++;
      console.log('âœ… Safe redirect clear:', url);
    } else {
      weights.redirects = Math.max(0.1, weights.redirects - 0.3);
      console.log('âš ï¸ False positive on redirect:', url, '| score:', score.toFixed(1));
    }
  });

  await chrome.storage.local.set({ weights });
  console.log('========================================');
  console.log('Redirect training complete. Accuracy:', correct + '/' + total, '(' + Math.round(correct/total*100) + '%)');
  console.log('Final weights:', JSON.stringify(weights));
  console.log('========================================');
});
