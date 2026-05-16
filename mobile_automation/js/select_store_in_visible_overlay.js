const selectors = [
  '.bottom-overlay.bottom-overlay_visible .user-addresses__item',
  '.bottom-overlay.bottom-overlay_visible .user-addresses__item-inner'
];
for (const selector of selectors) {
  const candidates = Array.from(document.querySelectorAll(selector));
  for (const candidate of candidates) {
    const rect = candidate.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      continue;
    }
    candidate.scrollIntoView({block: 'center'});
    candidate.click();
    return (candidate.innerText || candidate.textContent || '').trim();
  }
}
return '';
