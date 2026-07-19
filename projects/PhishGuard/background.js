async function updatePhishList() {
  try {
    let r1 = await fetch('https://openphish.com/feed.txt');
    let t1 = await r1.text();
    let urls1 = t1.split('\n').filter(u => u.trim() !== '');
    let r2 = await fetch('https://urlhaus.abuse.ch/downloads/text/');
    let t2 = await r2.text();
    let urls2 = t2.split('\n').filter(u => u.trim() !== '' && !u.startsWith('#'));
    let combined = [...new Set([...urls1, ...urls2])];
    await chrome.storage.local.set({ phishList: combined });
    console.log('PhishGuard: updated list with ' + combined.length + ' URLs');
  } catch (e) {
    console.log('PhishGuard: feed update failed', e);
  }
}

chrome.runtime.onInstalled.addListener(() => {
  updatePhishList();
  chrome.alarms.create('updateFeed', { periodInMinutes: 60 });
});

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === 'updateFeed') updatePhishList();
});
