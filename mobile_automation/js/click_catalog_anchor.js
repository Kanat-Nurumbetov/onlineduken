const link = document.querySelector(
  'a[href="/web/customer-frontend/distributors"], a[href="/web/customer-frontend/distributor"]'
);
if (!link) return false;
link.scrollIntoView({block: 'center'});
link.click();
return true;
