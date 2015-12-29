import csv
import logging

import pywikibot
import mwparserfromhell
import isbnlib

TEMPLATE_NAME = 'Gwybodlen llyfr'

site = pywikibot.Site('cy', 'wikipedia')
site.login()
data_repository = site.data_repository()
data_repository.login()

template = pywikibot.Page(site, 'Template:' + TEMPLATE_NAME)

logging.basicConfig(filename='welshbooks/2015-12-29.log',level=logging.DEBUG)

def use_param(template, name, mangle):
    if template.has(name, ignore_empty=True):
        result = mangle(template.get(name).value)
        if len(result) == 0:
            logging.warning('Failed to use "{}"'.format(template.get(name)))
        return result
    return dict()

def mangle_date(raw):
    text = raw.strip_code().strip()
    if len(text) == 4 and text.isdigit():
        return {'published': int(text)}
    try:
        (day, month, year) = text.split()
        if day.isdigit():
            day = int(day)
        else: return dict()
        if month == 'Ionawr':
            month = 1
        elif month == 'Chwefror':
            month = 2
        elif month == 'Mawrth':
            month = 3
        elif month == 'Ebrill':
            month = 4
        elif month == 'Mai':
            month = 5
        elif month == 'Mehefin':
            month = 6
        elif month == 'Gorffennaf':
            month = 7
        elif month == 'Awst':
            month = 8
        elif month == 'Medi':
            month = 9
        elif month == 'Hydref':
            month = 10
        elif month == 'Tachwedd':
            month = 11
        elif month == 'Rhagfyr':
            month = 12
        else: return dict()
        if year.isdigit():
            year = int(year)
        else: return dict()
        return {'published': '{:04}-{:02}-{:02}'.format(year, month, day)}
    except ValueError:
        return dict()

def mangle_isbn(raw):
    result = dict()
    for value in raw.strip().replace('-', '').split():
        if isbnlib.is_isbn13(value):
            result['isbn13'] = isbnlib.mask(value)
        elif isbnlib.is_isbn10(value):
            result['isbn10'] = isbnlib.mask(value)
    return result

def mangle_oclc(raw):
    value = raw.strip()
    if value.isdigit():
        return {'oclc': value}
    return {}

def mangle_pages(raw):
    value = raw.strip()
    if value.isdigit():
        return {'pages': int(value)}
    elif value.endswith(' tudalen') and value[x:-8].isdigit():
        return {'pages': int(value)}
    return dict()

def mangle_wikilink(raw):
    links = list(raw.filter_wikilinks())
    if len(links) == 1:
        try:
            page = pywikibot.Page(site, links[0].title)
            if page.isRedirectPage():
                page = page.getRedirectTarget()
            item = pywikibot.ItemPage.fromPage(page)
            return item.title()
        except pywikibot.NoPage: pass

def mangle_country(raw):
    value = mangle_wikilink(raw)
    if value:
        return {'country': value}
    if raw.strip().lower() == 'cymru':
        item = pywikibot.ItemPage.fromPage(pywikibot.Page(site, 'Cymru'))
        return {'country': item.title()}
    return dict()

def mangle_language(raw):
    value = mangle_wikilink(raw)
    if value:
        return {'language': value}
    if raw.strip().lower() == 'cymraeg':
        item = pywikibot.ItemPage.fromPage(pywikibot.Page(site, 'Cymraeg'))
        return {'language': item.title()}
    if raw.strip().lower() == 'saesneg':
        item = pywikibot.ItemPage.fromPage(pywikibot.Page(site, 'Saesneg'))
        return {'language': item.title()}
    return dict()

def mangle_author(raw):
    value = mangle_wikilink(raw)
    if value:
        return {'author': value}
    return dict()

def mangle_lccn(raw):
    return {'lccn': raw.strip()}

def mangle_genre(raw):
    value = mangle_wikilink(raw)
    if value:
        return {'genre': value}
    return dict()

def mangle_publisher(raw):
    value = mangle_wikilink(raw)
    if value:
        return {'publisher': value}
    return dict()

def mangle_editor(raw):
    value = mangle_wikilink(raw)
    if value:
        return {'editor': value}
    return dict()

def process_page(page):
    logging.debug('Processing page {}'.format(page))
    wikicode = mwparserfromhell.parse(page.get())
    templates = wikicode.filter_templates()
    book_templates = [t for t in templates if t.name.matches(TEMPLATE_NAME)]
    if len(book_templates) == 1:
        book = book_templates[0]
        result = {}
        result['title'] = page.title()
        try:
            result['wikidata'] = pywikibot.ItemPage.fromPage(page).title()
        except pywikibot.NoPage: pass
        result.update(use_param(book, 'dyddiad cyhoeddi', mangle_date))
        result.update(use_param(book, 'dyddiad chyhoeddi', mangle_date))
        result.update(use_param(book, 'dyddiad rhyddhau', mangle_date))
        result.update(use_param(book, 'isbn', mangle_isbn))
        result.update(use_param(book, 'oclc', mangle_oclc))
        result.update(use_param(book, 'tudalennau', mangle_pages))
        result.update(use_param(book, 'Tudalennau', mangle_pages))
        result.update(use_param(book, 'gwlad', mangle_country))
        result.update(use_param(book, 'cyngres', mangle_lccn))
        result.update(use_param(book, 'iaith', mangle_language))
        result.update(use_param(book, 'awdur', mangle_author))
        # tests
        result.update(use_param(book, 'genre', mangle_genre))
        result.update(use_param(book, 'cyhoeddwr', mangle_publisher))
        result.update(use_param(book, 'golygydd', mangle_editor))
        writer.writerow(result)

with open('welshbooks/2015-12-29.csv', 'w', 1) as csvfile:
    fieldnames = ['title', 'wikidata', 'author', 'country', 'language',
                  'published', 'pages', 'isbn13', 'isbn10', 'oclc', 'lccn',
                  'genre', 'publisher', 'editor']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for page in template.embeddedin(namespaces=0, content=True):
        try:
            process_page(page)
        except Exception as err:
            logging.error('Processing {} failed: {}'.format(page, err))
