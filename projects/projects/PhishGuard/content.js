const WHITELIST = ['google.com','youtube.com','facebook.com','twitter.com','microsoft.com','apple.com','amazon.com','github.com','wikipedia.org','linkedin.com','reddit.com','netflix.com','stackoverflow.com','cloudflare.com','mozilla.org'];

chrome.storage.local.get(['phishList', 'weights'], function(data) {
  var list = data.phishList || [];
  var weights = data.weights || { https: 2, keywords: 1, blacklist: 3, redirects: 2, subdomains: 1, homoglyphs: 2, suspiciousTLD: 1, longUrl: 1 };
  var url = window.location.href;
  var hostname = window.location.hostname;
  var score = 0;
  var reasons = [];

  if (WHITELIST.some(function(w) { return hostname === w || hostname.endsWith('.'+w); })) { return; }

  if (!url.startsWith('https://')) { score += weights.https; reasons.push('No HTTPS'); }
  if (['login','verify','secure','account','update','confirm'].some(function(w) { return url.toLowerCase().includes(w); })) { score += weights.keywords; reasons.push('Suspicious keywords'); }
  if (list.some(function(u) { try { return new URL(u).hostname === hostname; } catch(e) { return false; } })) { score += weights.blacklist; reasons.push('Known phishing site'); }
  if (['redirect=','url=','goto=','next=','return='].some(function(p) { return url.toLowerCase().includes(p); })) { score += weights.redirects; reasons.push('Suspicious redirect'); }
  if (window.location.hostname.split('.').length > 4) { score += weights.subdomains; reasons.push('Excessive subdomains'); }
  if (['.xyz','.tk','.ml','.ga','.cf'].some(function(t) { return hostname.endsWith(t); })) { score += weights.suspiciousTLD; reasons.push('Suspicious TLD'); }
  if (url.length > 100) { score += weights.longUrl; reasons.push('Long URL'); }

  var forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    var action = form.action || '';
    if (action && action.startsWith('http')) {
      try {
        var actionHost = new URL(action).hostname;
        if (actionHost && actionHost !== hostname) { score += 2; reasons.push('Form sends data to ' + actionHost); }
      } catch(e) {}
    }
  });

  if (!url.startsWith('https://')) {
    var passwords = document.querySelectorAll('input[type=password]');
    if (passwords.length > 0) { score += 2; reasons.push('Password field on HTTP'); }
  }

  var body = document.body ? document.body.innerText.toLowerCase() : '';
  var urgency = ['your account will be suspended','verify immediately','click here now','account has been compromised'];
  if (urgency.some(function(u) { return body.includes(u); })) { score += 1; reasons.push('Urgency language'); }

  if (score >= 3) {
    var banner = document.createElement('div');
    banner.style.cssText = 'position:fixed;top:0;left:0;width:100%;background:#dc2626;color:white;padding:12px;font-size:14px;font-weight:bold;z-index:999999;text-align:center;cursor:pointer;';
    banner.textContent = 'PhishGuard Warning: ' + reasons.join(', ') + ' — Click to dismiss';
    banner.addEventListener('click', function() { banner.remove(); });
    document.body.appendChild(banner);
  }
});
