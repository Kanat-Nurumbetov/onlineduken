const targetText = arguments[0].trim().toLowerCase();
const root = document.querySelector('#main-content') || document.body;
const isVisible = (el) => {
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
};
const buttons = Array.from(root.querySelectorAll('button, a, [role="button"]')).filter(isVisible);
for (const button of buttons) {
  const text = (button.innerText || button.textContent || '').trim().replace(/\s+/g, ' ').toLowerCase();
  if (!text || text !== targetText) continue;
  button.scrollIntoView({block: 'center'});
  button.click();
  return true;
}
return false;
