const root = document.querySelector('#main-content') || document.body;
const banned = [
  'главная', 'каталог', 'qr', 'корзина', 'еще', 'назад', 'закрыть',
  'подключиться', 'подробнее', 'мои заказы', 'бонусы', 'оплатить поставщику',
  'создать заказ', 'в корзину', 'найти поставщика', 'перейти в заказы'
];
const isVisible = (el) => {
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
};
const selectors = [
  '[class*="category"]',
  '[class*="subcategory"]',
  '[class*="product"]',
  '[class*="item"]',
  '[class*="card"]',
  '[routerlink]',
  'article',
  'section'
];
const seen = new Set();
const candidates = [];
for (const selector of selectors) {
  for (const el of root.querySelectorAll(selector)) {
    if (seen.has(el) || !isVisible(el)) continue;
    seen.add(el);
    const text = (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').toLowerCase();
    if (!text || banned.some((token) => text.includes(token))) continue;
    candidates.push(el);
  }
}
for (const candidate of candidates) {
  candidate.scrollIntoView({block: 'center'});
  candidate.click();
  return true;
}
return false;
