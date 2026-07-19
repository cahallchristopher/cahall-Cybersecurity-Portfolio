let currentUrl = '';

const WHITELIST = ['google.com','youtube.com','facebook.com','twitter.com','microsoft.com','apple.com','amazon.com','github.com','wikipedia.org','linkedin.com','reddit.com','netflix.com','stackoverflow.com','cloudflare.com','mozilla.org'];

chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
  currentUrl = tabs[0].url;
  let status = document.getElementById('status');
  let hostname = new URL(currentUrl).hostname;
  let parts = hostname.split('.');

  if (WHITELIST.some(function(w) { return hostname === w || hostname.endsWith('.'+w); })) {
    status.textContent = 'Site looks safe';
    status.style.color = 'green';
    chrome.storage.local.get('phishList', function(data) {
      let list = data.phishList || [];
      document.getElementById('count').textContent = 'Tracking ' + list.length + ' threats';
    });
    return;
  }

  chrome.storage.local.get(['phishList', 'weights'], function(data) {
    let list = data.phishList || [];
    let weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
    document.getElementById('count').textContent = 'Tracking ' + list.length + ' threats';
    let score = 0;
    let reasons = [];
    if (!currentUrl.startsWith('https://')) { score += weights.https; reasons.push('No HTTPS'); }
    let suspicious = ['login','verify','secure','account','update','confirm'];
    if (suspicious.some(function(w) { return currentUrl.toLowerCase().includes(w); })) { score += weights.keywords; reasons.push('Suspicious keywords'); }
    if (list.some(function(u) { try { return new URL(u).hostname === hostname; } catch(e) { return false; } })) { score += weights.blacklist; reasons.push('Known phishing site'); }
    if (['redirect=','url=','goto=','next=','return='].some(function(p) { return currentUrl.toLowerCase().includes(p); })) { score += weights.redirects; reasons.push('Suspicious redirect'); }
    if (parts.length > 4) { score += weights.subdomains; reasons.push('Excessive subdomains'); }
    if (['.xyz','.tk','.ml','.ga','.cf'].some(function(t) { return hostname.endsWith(t); })) { score += weights.suspiciousTLD; reasons.push('Suspicious TLD'); }
    if (currentUrl.length > 100) { score += weights.longUrl; reasons.push('Long URL'); }
    if (score >= 3) { status.textContent = 'DANGER: ' + reasons.join(', '); status.style.color = 'red'; }
    else if (score >= 1) { status.textContent = 'Warning: ' + reasons.join(', '); status.style.color = 'orange'; }
    else { status.textContent = 'Site looks safe'; status.style.color = 'green'; }
  });
});

document.getElementById('updateBtn').addEventListener('click', async function() {
  document.getElementById('count').textContent = 'Updating...';
  try {
    let r1 = await fetch('https://openphish.com/feed.txt');
    let t1 = await r1.text();
    let urls1 = t1.split('\n').filter(function(u) { return u.trim() !== ''; });
    let r2 = await fetch('https://urlhaus.abuse.ch/downloads/text/');
    let t2 = await r2.text();
    let urls2 = t2.split('\n').filter(function(u) { return u.trim() !== '' && !u.startsWith('#'); });
    let combined = [...new Set([...urls1, ...urls2])];
    chrome.storage.local.set({ phishList: combined });
    document.getElementById('count').textContent = 'Tracking ' + combined.length + ' threats';
  } catch(e) {
    document.getElementById('count').textContent = 'Update failed: ' + e.message;
  }
});

document.getElementById('safeBtn').addEventListener('click', function() {
  chrome.storage.local.get('weights', function(data) {
    let w = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
    Object.keys(w).forEach(function(k) { if (k !== 'blacklist') w[k] = Math.max(0.1, w[k] - 0.1); });
    chrome.storage.local.set({ weights: w });
    document.getElementById('feedback').textContent = 'Noted: reduced sensitivity';
  });
});

document.getElementById('dangerBtn').addEventListener('click', function() {
  chrome.storage.local.get('weights', function(data) {
    let w = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
    Object.keys(w).forEach(function(k) { if (k !== 'blacklist') w[k] = Math.min(5, w[k] + 0.2); });
    chrome.storage.local.set({ weights: w });
    document.getElementById('feedback').textContent = 'Noted: increased sensitivity';
  });
});
