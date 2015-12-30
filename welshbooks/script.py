# Request for approval and description:
# https://www.wikidata.org/wiki/Wikidata:Requests_for_permissions/Bot/FischBot_5

import argparse
import csv
import logging

import isbnlib
import mwparserfromhell
import pywikibot

TEMPLATE_NAME = 'Gwybodlen llyfr'

def use_param(template, name, mangle):
    if template.has(name, ignore_empty=True):
        result = mangle(template.get(name).value)
        if len(result) == 0:
            logging.warning('Failed to use "{}"'.format(template.get(name)))
        return result
    return dict()

def _mangle_wikilink(raw, key):
    links = list(raw.filter_wikilinks())
    if len(links) == 1:
        try:
            page = pywikibot.Page(site, links[0].title)
            if page.isRedirectPage():
                page = page.getRedirectTarget()
            item = pywikibot.ItemPage.fromPage(page)
            return {key: item.title()}
        except pywikibot.NoPage: pass
    return dict()

def mangle_author(raw):
    return _mangle_wikilink(raw, 'author')

def mangle_language(raw):
    if raw.strip().lower() == 'cymraeg':
        return {'language': 'Q9309'}
    if raw.strip().lower() == 'saesneg':
        return {'language': 'Q1860'}
    else:
        return _mangle_wikilink(raw, 'language')

def mangle_country(raw):
    if raw.strip().lower() == 'cymru':
        return {'country': 'Q25'}
    else:
        return _mangle_wikilink(raw, 'country')

def mangle_published(raw):
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

def mangle_pages(raw):
    value = raw.strip()
    if value.endswith(' tudalen'):
        value = value[:-8]
    if value.isdigit():
        return {'pages': int(value)}
    return dict()

def mangle_publisher(raw):
    return _mangle_wikilink(raw, 'publisher')

def mangle_editor(raw):
    return _mangle_wikilink(raw, 'editor')

def mangle_isbn(raw):
    result = dict()
    for value in raw.strip().split():
        if isbnlib.is_isbn13(value):
            result['isbn13'] = isbnlib.mask(value)
        elif isbnlib.is_isbn10(value):
            result['isbn10'] = isbnlib.mask(value)
    return result

def mangle_oclc(raw):
    value = raw.strip()
    if value.isdigit():
        return {'oclc': value}
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
        result.update(use_param(book, 'awdur', mangle_author))
        result.update(use_param(book, 'iaith', mangle_language))
        result.update(use_param(book, 'gwlad', mangle_country))
        result.update(use_param(book, 'dyddiad cyhoeddi', mangle_published))
        result.update(use_param(book, 'dyddiad chyhoeddi', mangle_published))
        result.update(use_param(book, 'dyddiad rhyddhau', mangle_published))
        result.update(use_param(book, 'tudalennau', mangle_pages))
        result.update(use_param(book, 'Tudalennau', mangle_pages))
        result.update(use_param(book, 'cyhoeddwr', mangle_publisher))
        result.update(use_param(book, 'golygydd', mangle_editor))
        result.update(use_param(book, 'isbn', mangle_isbn))
        result.update(use_param(book, 'oclc', mangle_oclc))
        writer.writerow(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Harvest information from Welsh Wikipedia about books.')
    parser.add_argument('--log', type=str, help='target file for log',
                        default='welshbooks.log')
    parser.add_argument('--level', type=int, default=20,
                        help='numeric value for loglevel')
    parser.add_argument('output', type=str,
                        help='target file for extracted data')
    args = parser.parse_args()

    site = pywikibot.Site('cy', 'wikipedia')
    site.login()
    data_repository = site.data_repository()
    data_repository.login()

    template = pywikibot.Page(site, 'Template:' + TEMPLATE_NAME)

    logging.basicConfig(filename=args.log,level=args.level)

    with open(args.output, 'w', 1) as csvfile:
        fieldnames = ['title', 'wikidata', 'author', 'language', 'country',
                      'published', 'pages', 'publisher', 'editor',
                      'isbn13', 'isbn10', 'oclc']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for page in template.embeddedin(namespaces=0, content=True):
            try:
                process_page(page)
            except Exception as err:
                logging.error('Processing {} failed: {}'.format(page, err))
