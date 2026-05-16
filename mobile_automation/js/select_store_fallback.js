const skipPattern = /закрыть|close|cancel|отмена/i;
const roots = Array.from(
  document.querySelectorAll('[class*="bottom-overlay"], [class*="store"], [class*="shop"], [class*="branch"]')
);
for (const root of roots) {
  const candidates = root.querySelectorAll('button, a, [role="button"], [onclick], .item, .card');
  for (const candidate of candidates) {
    const text = (candidate.innerText || candidate.textContent || '').trim();
    if (!text || skipPattern.test(text)) {
      continue;
    }
    const rect = candidate.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      continue;
    }
    candidate.scrollIntoView({block: 'center'});
    candidate.click();
    return text;
  }
}
return '';
