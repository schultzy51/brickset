"""Scrape current prices for one LEGO set from US stores.

Each store loads its page in a real browser (Playwright) and pulls the data
out with a small JavaScript extractor; the Python side filters and ranks what
comes back. Stores change their pages and bot checks often, so every store
runs on its own and a failure is reported instead of stopping the others.

Amazon is not scraped: its Conditions of Use prohibit automated access.
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import quote_plus

BLOCK_PATTERNS = re.compile(
  r"robot or human|press & hold|are you a robot|just a moment|access denied|"
  r"page is currently unavailable|unusual traffic|verify you are human|access restricted",
  re.I,
)

EBAY_EXCLUDE = re.compile(
  r"sticker|display case|acrylic|\bled\b|light kit|lighting|"
  r"instructions?\b|manual|box only|empty box|\bparts?\b|\bpieces? only\b|\bbags?\b|"
  r"compatible|\bmoc\b|custom|knock ?off|generic|no box|lot of",
  re.I,
)
EBAY_MINIFIG = re.compile(r"minifig|\bfigures?\b", re.I)
EBAY_SEALED = re.compile(r"sealed|\bnisb\b|\bmisb\b|in box|building set", re.I)   # a full set that mentions its minifigs
EBAY_MIN_SHARE_OF_LIST = 0.6  # listings below 60% of list price are almost always parts/accessories
EBAY_KEEP = 3


@dataclass
class Offer:
  store: str
  price: Optional[float] = None
  shipping: Optional[float] = None   # None = not shown
  in_stock: Optional[bool] = None    # None = unknown
  seller: Optional[str] = None
  title: Optional[str] = None
  url: Optional[str] = None

  @property
  def total(self):
    if self.price is None:
      return None
    return self.price + (self.shipping or 0)


@dataclass
class StoreResult:
  store: str
  url: str
  offers: List[Offer] = field(default_factory=list)
  status: str = 'ok'                 # ok | not_found | blocked | error | link_only
  message: Optional[str] = None
  list_price: Optional[float] = None


def number_pattern(number):
  return re.compile(r'(?<![\d-]){}(?!\d)'.format(re.escape(number)))


def parse_money(text):
  if text is None:
    return None
  if isinstance(text, (int, float)):
    return float(text)
  m = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', str(text))
  return float(m.group(1).replace(',', '')) if m else None


def schema_in_stock(availability):
  if not availability:
    return None
  a = availability.rsplit('/', 1)[-1].lower()
  if a in ('instock', 'limitedavailability', 'onlineonly', 'instoreonly'):
    return True
  if a in ('outofstock', 'soldout', 'discontinued', 'backorder', 'preorder', 'presale'):
    return False
  return None


async def _blocked(page):
  try:
    text = await page.evaluate("() => (document.title + ' ' + document.body.innerText.slice(0, 2000))")
  except Exception:
    return False
  return bool(BLOCK_PATTERNS.search(text))


async def _goto(page, url, settle_ms=2500):
  response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
  await page.wait_for_timeout(settle_ms)
  return response


# ---------------------------------------------------------------- LEGO.com

LEGO_JS = r"""
() => {
  const lds = [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map(s => { try { return JSON.parse(s.textContent) } catch (e) { return null } })
    .filter(Boolean).flat();
  const p = lds.find(x => x['@type'] === 'Product');
  const html = document.documentElement.innerHTML;
  const list = (html.match(/"listPrice":\{[^}]*"formattedValue":([\d.]+)/) || [])[1];
  return p ? {name: p.name, offers: p.offers, listPrice: list ? parseFloat(list) : null, url: location.href} : null;
}
"""


async def lego(page, number, **_):
  url = 'https://www.lego.com/en-us/product/{}'.format(number)
  result = StoreResult('LEGO.com', url)
  response = await _goto(page, url)
  if response and response.status == 404:
    result.status = 'not_found'
    return result
  if await _blocked(page):
    result.status = 'blocked'
    return result

  data = await page.evaluate(LEGO_JS)
  if not data or not data.get('offers'):
    result.status = 'not_found'
    return result

  offer = data['offers'][0] if isinstance(data['offers'], list) else data['offers']
  result.url = data.get('url', url).split('?')[0]
  regular = [x.get('value') for x in offer.get('additionalProperty') or [] if (x.get('name') or '').lower() == 'regular price']
  result.list_price = data.get('listPrice') or (parse_money(regular[0]) if regular else None)
  result.offers.append(Offer(
    store='LEGO.com', price=parse_money(offer.get('price')), shipping=None,
    in_stock=schema_in_stock(offer.get('availability')), seller='LEGO',
    title=data.get('name'), url=result.url,
  ))
  return result


# ---------------------------------------------------------------- Walmart

WALMART_JS = r"""
() => {
  const nd = document.getElementById('__NEXT_DATA__');
  if (!nd) return null;
  const d = JSON.parse(nd.textContent);
  const stacks = (((d.props || {}).pageProps || {}).initialData || {}).searchResult;
  const out = [];
  for (const s of ((stacks || {}).itemStacks || []))
    for (const it of (s.items || []))
      if (it && it.name) out.push({
        id: it.usItemId, name: it.name, price: it.price,
        current: it.priceInfo && it.priceInfo.currentPrice && it.priceInfo.currentPrice.price,
        seller: it.sellerName, availability: (it.availabilityStatusV2 || {}).value || it.availabilityStatus,
        url: it.canonicalUrl,
      });
  return out;
}
"""


def walmart_offers(items, number):
  pattern, seen, offers = number_pattern(number), set(), []
  for it in items or []:
    if not pattern.search(it.get('name') or '') or it.get('id') in seen:
      continue
    seen.add(it.get('id'))
    price = parse_money(it.get('current') or it.get('price'))
    avail = (it.get('availability') or '').upper()
    offers.append(Offer(
      store='Walmart', price=price, shipping=None,
      in_stock=True if avail == 'IN_STOCK' else (False if avail else None),
      seller=it.get('seller'), title=it.get('name'),
      url='https://www.walmart.com' + (it.get('url') or '').split('?')[0] if it.get('url') else None,
    ))
  return offers


async def walmart(page, number, **_):
  url = 'https://www.walmart.com/search?q={}'.format(quote_plus('lego ' + number))
  result = StoreResult('Walmart', url)
  await _goto(page, url)
  if await _blocked(page):
    result.status = 'blocked'
    return result
  result.offers = walmart_offers(await page.evaluate(WALMART_JS), number)
  if not result.offers:
    result.status = 'not_found'
  return result


# ---------------------------------------------------------------- Best Buy

BESTBUY_SEARCH_JS = r"""
() => [...document.querySelectorAll('li.product-list-item')].map(li => ({
  title: (li.querySelector('.sku-block-content-title') || {}).innerText || '',
  href: (li.querySelector('a[href*="/product/"]') || {}).href || null,
}))
"""

PRODUCT_LD_JS = r"""
() => {
  const lds = [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map(s => { try { return JSON.parse(s.textContent) } catch (e) { return null } })
    .filter(Boolean).flat();
  const p = lds.find(x => x['@type'] === 'Product');
  return p ? {name: p.name, offers: p.offers} : null;
}
"""


def bestbuy_match(items, number):
  pattern = number_pattern(number)
  for it in items or []:
    if it.get('href') and pattern.search(it.get('title') or ''):
      return it
  return None


def ld_offers(store, data, url):
  if not data or not data.get('offers'):
    return []
  offers = data['offers'] if isinstance(data['offers'], list) else [data['offers']]
  out = []
  for o in offers:
    if 'used' in (o.get('itemCondition') or '').lower() or 'refurb' in (o.get('itemCondition') or '').lower():
      continue
    out.append(Offer(
      store=store, price=parse_money(o.get('price') or o.get('lowPrice')), shipping=None,
      in_stock=schema_in_stock(o.get('availability')),
      seller=(o.get('seller') or {}).get('name'), title=data.get('name'), url=url,
    ))
  return out


async def bestbuy(page, number, **_):
  url = 'https://www.bestbuy.com/site/searchpage.jsp?st={}&intl=nosplash'.format(quote_plus('lego ' + number))
  result = StoreResult('Best Buy', url)
  await _goto(page, url, settle_ms=3500)
  if await _blocked(page):
    result.status = 'blocked'
    return result

  match = bestbuy_match(await page.evaluate(BESTBUY_SEARCH_JS), number)
  if not match:
    result.status = 'not_found'
    return result

  product_url = match['href'].split('?')[0]
  await _goto(page, product_url)
  result.offers = ld_offers('Best Buy', await page.evaluate(PRODUCT_LD_JS), product_url)
  if not result.offers:
    result.status = 'not_found'
  return result


# ---------------------------------------------------------------- Target (best effort)

TARGET_JS = r"""
(number) => {
  const re = new RegExp('(^|[^\\d-])' + number + '(?!\\d)');
  const seen = new Set(), out = [];
  for (const a of document.querySelectorAll('a[href*="/p/"]')) {
    const href = a.href.split('?')[0];
    if (seen.has(href)) continue;
    // climb to the product card: the largest ancestor that still holds only this one product link
    const links = el => new Set([...el.querySelectorAll('a[href*="/p/"]')].map(x => x.href.split('?')[0])).size;
    let card = a;
    for (let i = 0; i < 10 && card.parentElement && links(card.parentElement) <= 1; i++) card = card.parentElement;
    const text = card.innerText || '';
    if (!re.test(text) || !/\$\d/.test(text)) continue;
    seen.add(href);
    out.push({href, title: (a.innerText || a.getAttribute('aria-label') || '').trim(), text: text.slice(0, 400)});
  }
  return out;
}
"""


async def target(page, number, **_):
  url = 'https://www.target.com/s?searchTerm={}'.format(quote_plus('lego ' + number))
  result = StoreResult('Target', url)
  await _goto(page, url, settle_ms=5000)
  if await _blocked(page):
    result.status = 'blocked'
    return result

  for card in await page.evaluate(TARGET_JS, number):
    text = card['text']
    result.offers.append(Offer(
      store='Target', price=parse_money(text), shipping=None,
      in_stock=False if re.search(r'out of stock|sold out', text, re.I) else None,
      seller='Target', title=card['title'] or None, url=card['href'],
    ))
  if not result.offers:
    result.status = 'not_found'
  return result


# ---------------------------------------------------------------- eBay

EBAY_JS = r"""
() => [...document.querySelectorAll('li.s-card, li.s-item')].map(li => ({
  title: ((li.querySelector('.s-card__title, .s-item__title') || {}).innerText || '').replace(/\s*Opens in a new window or tab\s*/i, '').replace(/^New Listing/i, '').trim(),
  price: (li.querySelector('.s-card__price, .s-item__price') || {}).innerText || '',
  rows: [...li.querySelectorAll('.s-card__attribute-row, .s-item__shipping, .s-item__logisticsCost')].map(r => r.innerText.trim()),
  href: ((li.querySelector('a[href*="/itm/"]') || {}).href || '').split('?')[0],
}))
"""


def ebay_shipping(rows):
  for row in rows or []:
    if re.search(r'free (delivery|shipping)', row, re.I):
      return 0.0
    if re.search(r'delivery|shipping', row, re.I):
      cost = parse_money(row)
      if cost is not None:
        return cost
  return None


def ebay_offers(items, number, list_price=None, keep=EBAY_KEEP):
  pattern, offers = number_pattern(number), []
  floor = list_price * EBAY_MIN_SHARE_OF_LIST if list_price else None
  for it in items or []:
    title, href = it.get('title') or '', it.get('href') or ''
    if not re.search(r'/itm/\d{9,}', href) or not pattern.search(title) or EBAY_EXCLUDE.search(title):
      continue
    if EBAY_MINIFIG.search(title) and not EBAY_SEALED.search(title):
      continue
    if ' to ' in (it.get('price') or ''):   # price ranges are multi-variation listings
      continue
    price = parse_money(it.get('price'))
    if price is None or (floor and price < floor):
      continue
    offers.append(Offer(store='eBay', price=price, shipping=ebay_shipping(it.get('rows')),
                        in_stock=True, seller='eBay seller', title=title, url=href))
  offers.sort(key=lambda o: o.total)
  return offers[:keep]


async def ebay(page, number, list_price=None, **_):
  url = 'https://www.ebay.com/sch/i.html?_nkw={}&LH_ItemCondition=1000&LH_BIN=1&LH_PrefLoc=1&_sop=15'.format(quote_plus('lego ' + number))
  result = StoreResult('eBay (new, Buy It Now)', url)
  await _goto(page, url)
  if await _blocked(page):
    result.status = 'blocked'
    return result
  result.offers = ebay_offers(await page.evaluate(EBAY_JS), number, list_price)
  if not result.offers:
    result.status = 'not_found'
  return result


# ---------------------------------------------------------------- runner

SCRAPERS = {
  'lego': lego,
  'walmart': walmart,
  'bestbuy': bestbuy,
  'target': target,
  'ebay': ebay,
}

DISPLAY_NAMES = {
  'lego': 'LEGO.com',
  'walmart': 'Walmart',
  'bestbuy': 'Best Buy',
  'target': 'Target',
  'ebay': 'eBay (new, Buy It Now)',
}

LINK_ONLY = {
  'Amazon': 'https://www.amazon.com/s?k={}',
}


async def _run_one(context, name, number, list_price, timeout):
  page = await context.new_page()
  fn = SCRAPERS[name]
  try:
    return await asyncio.wait_for(fn(page, number, list_price=list_price), timeout)
  except asyncio.TimeoutError:
    return StoreResult(DISPLAY_NAMES[name], '', status='error', message='timed out after {}s'.format(timeout))
  except Exception as e:
    return StoreResult(DISPLAY_NAMES[name], '', status='error', message='{}: {}'.format(type(e).__name__, str(e).splitlines()[0][:150]))
  finally:
    await page.close()


async def check_prices(number, stores, list_price=None, profile_dir='.cache/browser', headless=True, timeout=60):
  from playwright.async_api import async_playwright

  async with async_playwright() as p:
    launch = dict(user_data_dir=profile_dir, headless=headless, locale='en-US',
                  viewport={'width': 1366, 'height': 900}, args=['--disable-blink-features=AutomationControlled'])
    try:
      context = await p.chromium.launch_persistent_context(channel='chrome', **launch)
    except Exception:
      context = await p.chromium.launch_persistent_context(**launch)   # bundled Chromium

    try:
      # LEGO.com first: it supplies the list price that eBay filtering relies on
      results = []
      if 'lego' in stores:
        results.append(await _run_one(context, 'lego', number, list_price, timeout))
        list_price = list_price or results[0].list_price
      rest = [s for s in stores if s != 'lego']
      results += await asyncio.gather(*(_run_one(context, s, number, list_price, timeout) for s in rest))
    finally:
      await context.close()

  for store, template in LINK_ONLY.items():
    results.append(StoreResult(store, template.format(quote_plus('lego ' + number)), status='link_only'))
  return results, list_price
