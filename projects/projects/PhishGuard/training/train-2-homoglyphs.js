// PhishGuard Training Script 2 â€” Homoglyph & Brand Spoofing
// Trains the extension to catch digit substitution attacks:
//   paypa1 instead of paypal
//   g00gle instead of google
//   micros0ft instead of microsoft
// HOW TO USE:
//   1. Click the PhishGuard icon â†’ right-click â†’ Inspect
//   2. Console tab â†’ paste and press Enter
// ============================================================

const HOMOGLYPH_PHISHING = [
  'https://paypa1.com/login',
  'https://g00gle-secure.com/verify',
  'https://micros0ft-support.com/account',
  'https://app1e-id.com/signin',
  'https://arnazon-deals.com/account',
  'https://faceb00k.com/login',
  'https://lnstagram-verify.com/account',
  'https://tw1tter-support.com/verify',
  'https://disc0rd-nitro.com/claim',
  'https://steamc0mmunity.com/login',
  'https://paypai-secure.com/verify',
  'https://googIe.com/signin',
  'https://micosoft.com/support',
  'https://arnaz0n-prime.com/verify',
  'https://app1e-support.com/id/verify',
];

const SAFE_URLS = [
  'https://paypal.com',
  'https://google.com',
  'https://microsoft.com',
  'https://apple.com',
  'https://amazon.com',
  'https://facebook.com',
  'https://instagram.com',
  'https://twitter.com',
  'https://discord.com',
  'https://store.steampowered.com',
];

function hasHomoglyph(hostname) {
  const brands = ['paypal','google','apple','amazon','microsoft','facebook','instagram','twitter','discord','steam'];
  const map = { a:'4', e:'3', i:'1', o:'0', l:'1', s:'5' };
  return brands.some(brand => {
    let mangled = brand.split('').map(c => map[c] || c).join('');
    return hostname.includes(mangled) && !hostname.includes(brand);
  });
}

function scoreUrl(url, weights) {
  let score = 0;
  let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return 99; }
  if (!url.startsWith('https://')) score += weights.https;
  if (['login','verify','secure','account','update','confirm','signin','claim'].some(w => url.toLowerCase().includes(w))) score += weights.keywords;
  if (hasHomoglyph(hostname)) score += weights.homoglyphs;
  if (['.xyz','.tk','.ml','.ga','.cf'].some(t => hostname.endsWith(t))) score += weights.suspiciousTLD;
  return score;
}

chrome.storage.local.get('weights', async function(data) {
  let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  console.log('Starting homoglyph training...');
  console.log('Starting weights:', JSON.stringify(weights));

  let correct = 0; let total = 0;

  HOMOGLYPH_PHISHING.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score >= 3) {
      correct++;
      console.log('âœ… Caught homoglyph attack:', url, '| score:', score.toFixed(1));
    } else {
      weights.homoglyphs = Math.min(5, weights.homoglyphs + 0.4);
      console.log('âŒ Missed homoglyph:', url, '| score:', score.toFixed(1), 'â€” increased homoglyph weight to', weights.homoglyphs.toFixed(1));
    }
  });

  SAFE_URLS.forEach(url => {
    let score = scoreUrl(url, weights); total++;
    if (score === 0) {
      correct++;
      console.log('âœ… Legitimate brand clear:', url);
    } else {
      weights.homoglyphs = Math.max(0.1, weights.homoglyphs - 0.2);
      console.log('âš ï¸ False positive on brand:', url, '| score:', score.toFixed(1));
    }
  });

  await chrome.storage.local.set({ weights });
  console.log('========================================');
  console.log('Homoglyph training complete. Accuracy:', correct + '/' + total, '(' + Math.round(correct/total*100) + '%)');
  console.log('Final weights:', JSON.stringify(weights));
  console.log('========================================');
});
