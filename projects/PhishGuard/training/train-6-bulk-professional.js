// PhishGuard Professional Bulk Training Script
// Fetches live feeds, 80/20 train/test split, outputs precision/recall/F1
// HOW TO USE: right-click PhishGuard popup → Inspect → Console → paste

const CONFIG = { DANGER_THRESHOLD: 3, TRAIN_SPLIT: 0.8, MAX_PHISHING_URLS: 500, MAX_SAFE_URLS: 500, LEARNING_RATE_UP: 0.3, LEARNING_RATE_DOWN: 0.2, EPOCHS: 3 };

const SAFE_SITES = [
  'https://google.com','https://youtube.com','https://facebook.com','https://twitter.com','https://instagram.com','https://linkedin.com',
  'https://microsoft.com','https://apple.com','https://amazon.com','https://netflix.com','https://reddit.com','https://wikipedia.org',
  'https://github.com','https://stackoverflow.com','https://twitch.tv','https://discord.com','https://spotify.com','https://paypal.com',
  'https://adobe.com','https://dropbox.com','https://slack.com','https://zoom.us','https://cloudflare.com','https://mozilla.org',
  'https://python.org','https://nodejs.org','https://docker.com','https://bbc.com','https://cnn.com','https://nytimes.com',
  'https://reuters.com','https://bloomberg.com','https://wsj.com','https://chase.com','https://bankofamerica.com','https://wellsfargo.com',
  'https://citibank.com','https://capitalone.com','https://visa.com','https://mastercard.com','https://americanexpress.com','https://ally.com',
  'https://techcrunch.com','https://wired.com','https://arstechnica.com','https://elastic.co','https://grafana.com','https://prometheus.io',
  'https://postgresql.org','https://mysql.com','https://mongodb.com',
];

function shannonEntropy(str) {
  let freq = {};
  for (let c of str) freq[c] = (freq[c] || 0) + 1;
  let len = str.length;
  return -Object.values(freq).reduce((sum, f) => { let p = f/len; return sum + p * Math.log2(p); }, 0);
}

function extractFeatures(url) {
  let f = { noHttps:false, hasKeywords:false, hasRedirect:false, excessiveSubdomains:false, suspiciousTLD:false, longUrl:false, hasHomoglyph:false, hasIpAddress:false, highEntropy:false, manyDots:false };
  let hostname = '';
  try { hostname = new URL(url).hostname; } catch(e) { return f; }
  let parts = hostname.split('.');
  f.noHttps = !url.startsWith('https://');
  f.hasKeywords = ['login','verify','secure','account','update','confirm','signin','recover','suspend','validate','billing','alert'].some(w => url.toLowerCase().includes(w));
  f.hasRedirect = ['redirect=','url=','goto=','next=','return=','link=','out=','click='].some(p => url.toLowerCase().includes(p));
  f.excessiveSubdomains = parts.length > 4;
  f.suspiciousTLD = ['.xyz','.tk','.ml','.ga','.cf','.gq','.top','.click','.link','.work'].some(t => hostname.endsWith(t));
  f.longUrl = url.length > 100;
  const brands = ['paypal','google','apple','amazon','microsoft','facebook','netflix','instagram','twitter','discord'];
  const gm = { a:'4',e:'3',i:'1',o:'0',l:'1',s:'5' };
  f.hasHomoglyph = brands.some(b => { let m = b.split('').map(c => gm[c]||c).join(''); return hostname.includes(m) && !hostname.includes(b); });
  f.hasIpAddress = /^\d{1,3}(\.\d{1,3}){3}$/.test(hostname);
  f.highEntropy = shannonEntropy(parts[0]) > 3.5;
  f.manyDots = (url.match(/\./g)||[]).length > 5;
  return f;
}

function scoreUrl(url, weights) {
  let f = extractFeatures(url); let score = 0;
  if (f.noHttps) score += weights.https;
  if (f.hasKeywords) score += weights.keywords;
  if (f.hasRedirect) score += weights.redirects;
  if (f.excessiveSubdomains) score += weights.subdomains;
  if (f.suspiciousTLD) score += weights.suspiciousTLD;
  if (f.longUrl) score += weights.longUrl;
  if (f.hasHomoglyph) score += weights.homoglyphs;
  if (f.hasIpAddress) score += (weights.ipAddress||2);
  if (f.highEntropy) score += (weights.entropy||1);
  if (f.manyDots) score += (weights.manyDots||1);
  return score;
}

function calculateMetrics(results) {
  let tp = results.filter(r => r.isPhishing && r.detected).length;
  let fp = results.filter(r => !r.isPhishing && r.detected).length;
  let fn = results.filter(r => r.isPhishing && !r.detected).length;
  let tn = results.filter(r => !r.isPhishing && !r.detected).length;
  let precision = tp/(tp+fp)||0; let recall = tp/(tp+fn)||0;
  let f1 = 2*(precision*recall)/(precision+recall)||0;
  let accuracy = (tp+tn)/results.length||0;
  return { tp, fp, fn, tn, precision, recall, f1, accuracy };
}

async function bulkTrain() {
  console.log('==============================================');
  console.log('PhishGuard Professional Bulk Training');
  console.log('==============================================');
  let phishingUrls = [];
  try { let r1 = await fetch('https://openphish.com/feed.txt'); let t1 = await r1.text(); let o = t1.split('\n').filter(u => u.trim() !== ''); console.log('OpenPhish:', o.length, 'URLs'); phishingUrls.push(...o); } catch(e) { console.log('OpenPhish failed:', e.message); }
  try { let r2 = await fetch('https://urlhaus.abuse.ch/downloads/text/'); let t2 = await r2.text(); let u = t2.split('\n').filter(u => u.trim() !== '' && !u.startsWith('#')); console.log('URLhaus:', u.length, 'URLs'); phishingUrls.push(...u); } catch(e) { console.log('URLhaus failed:', e.message); }
  phishingUrls = [...new Set(phishingUrls)].slice(0, CONFIG.MAX_PHISHING_URLS);
  let safeUrls = SAFE_SITES.slice(0, CONFIG.MAX_SAFE_URLS);
  console.log('Total phishing:', phishingUrls.length, '| Total safe:', safeUrls.length);
  function splitData(arr) { let s = [...arr].sort(() => Math.random()-0.5); let sp = Math.floor(s.length*CONFIG.TRAIN_SPLIT); return { train: s.slice(0,sp), test: s.slice(sp) }; }
  let phishSplit = splitData(phishingUrls); let safeSplit = splitData(safeUrls);
  console.log('Train:', phishSplit.train.length, 'phishing +', safeSplit.train.length, 'safe | Test:', phishSplit.test.length, 'phishing +', safeSplit.test.length, 'safe');
  let data = await chrome.storage.local.get('weights');
  let weights = data.weights || { https:2,keywords:1,blacklist:3,redirects:2,subdomains:1,homoglyphs:2,suspiciousTLD:1,longUrl:1,ipAddress:2,entropy:1,manyDots:1 };
  let bestWeights = {...weights}; let bestF1 = 0;
  for (let epoch = 0; epoch < CONFIG.EPOCHS; epoch++) {
    let correct = 0; let total = 0;
    phishSplit.train.forEach(url => { let score = scoreUrl(url,weights); total++; if (score >= CONFIG.DANGER_THRESHOLD) { correct++; } else { Object.keys(weights).forEach(k => { if (k !== 'blacklist') weights[k] = Math.min(5,weights[k]+CONFIG.LEARNING_RATE_UP); }); } });
    safeSplit.train.forEach(url => { let score = scoreUrl(url,weights); total++; if (score === 0) { correct++; } else { Object.keys(weights).forEach(k => { if (k !== 'blacklist') weights[k] = Math.max(0.1,weights[k]-CONFIG.LEARNING_RATE_DOWN); }); } });
    let testResults = [...phishSplit.test.map(url => ({ isPhishing:true, detected: scoreUrl(url,weights) >= CONFIG.DANGER_THRESHOLD })),...safeSplit.test.map(url => ({ isPhishing:false, detected: scoreUrl(url,weights) >= CONFIG.DANGER_THRESHOLD }))];
    let m = calculateMetrics(testResults);
    console.log('Epoch', epoch+1, '— Train:', Math.round(correct/total*100)+'%', '| F1:', m.f1.toFixed(3), '| Precision:', m.precision.toFixed(3), '| Recall:', m.recall.toFixed(3));
    if (m.f1 > bestF1) { bestF1 = m.f1; bestWeights = {...weights}; }
  }
  let finalResults = [...phishSplit.test.map(url => ({ isPhishing:true, detected: scoreUrl(url,bestWeights) >= CONFIG.DANGER_THRESHOLD })),...safeSplit.test.map(url => ({ isPhishing:false, detected: scoreUrl(url,bestWeights) >= CONFIG.DANGER_THRESHOLD }))];
  let fm = calculateMetrics(finalResults);
  await chrome.storage.local.set({ weights: bestWeights });
  console.log('==============================================');
  console.log('TRAINING COMPLETE');
  console.log('Confusion Matrix: TP:', fm.tp, '| FP:', fm.fp, '| TN:', fm.tn, '| FN:', fm.fn);
  console.log('Accuracy:', (fm.accuracy*100).toFixed(1)+'% | Precision:', (fm.precision*100).toFixed(1)+'% | Recall:', (fm.recall*100).toFixed(1)+'% | F1:', fm.f1.toFixed(3));
  console.log('Best weights saved:', JSON.stringify(bestWeights));
  console.log('==============================================');
}

bulkTrain();
