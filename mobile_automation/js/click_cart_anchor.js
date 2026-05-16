const link = document.querySelector('a[href="/web/customer-frontend/cart"]');
if (!link) return false;
link.scrollIntoView({block: 'center'});
link.click();
return true;
