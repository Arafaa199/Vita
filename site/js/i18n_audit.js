(function () {
  const ATTR = 'data-i18n';
  const ATTR_MAP = 'data-i18n-attr';
  const isVisible = (el) => el.offsetParent !== null || el === document.body;

  const all = Array.from(document.querySelectorAll('body *'))
    .filter(el => isVisible(el) && !['SCRIPT','STYLE'].includes(el.tagName));

  let total = 0, translated = 0, offenders = [];

  for (const el of all) {
    // text node check
    const text = (el.textContent || '').trim();
    const hasChildren = el.children && el.children.length > 0;
    const hasKey = el.hasAttribute(ATTR);
    const hasAttrMap = el.hasAttribute(ATTR_MAP);

    // count only elements that show user-facing text/placeholder/title/value
    const userFacing =
      (text && !hasChildren) ||
      el.placeholder || el.title || el.value;

    if (!userFacing) continue;
    total++;

    if (hasKey || hasAttrMap) translated++;
    else offenders.push(el);
  }

  const pct = total ? Math.round((translated / total) * 100) : 100;
  console.log(`[i18n] Coverage: ${translated}/${total} = ${pct}%`);
  if (offenders.length) {
    console.log('[i18n] Missing bindings (first 20):');
    offenders.slice(0, 20).forEach((el, i) => {
      console.log(i+1, el.tagName, el.className || '', (el.textContent||'').trim().slice(0,80));
    });
  }

  window.__i18nAudit = { total, translated, pct, offenders };
})();
