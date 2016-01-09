import argparse
import csv
import logging

import mwparserfromhell
import pywikibot

TEMPLATE_NAME = 'RE'

def use_param(template, name, mangle):
    if template.has(name, ignore_empty=True):
        result = mangle(template.get(name).value)
        if len(result) == 0:
            logging.warning('Failed to use {!r:}'.format(template.get(name)))
        return result
    return dict()

def mangle_wikipedia(raw):
    try:
        wde_page = pywikibot.Page(pywikibot.Site('de', 'wikipedia'), raw)
        if wde_page.isRedirectPage():
            wde_page = wde_page.getRedirectTarget()
    except pywikibot.NoPage:
        return {'wikipdia': '??? ' + raw}
    try:
        item = pywikibot.ItemPage.fromPage(wde_page).title()
        return {'subject': item.title(), 'wikipedia': wde_page.title()}
    except:
        return {'wikipedia': wde_page.title()}


def process_page(page):
    logging.debug('Processing page {}'.format(page))
    wikicode = mwparserfromhell.parse(page.get())
    templates = wikicode.filter_templates()
    re_templates = [t for t in templates if t.name.matches(TEMPLATE_NAME)]
    if len(re_templates) == 1:
        re = re_templates[0]
        result = {}
        result['title'] = page.title()
        try:
            result['wikidata'] = pywikibot.ItemPage.fromPage(page).title()
        except pywikibot.NoPage: pass
        result.update(use_param(re, 9, mangle_wikipedia))
        if 'subject' in result:
            writer.writerow(result)

    else:
        logging.warning('multiple templates found; skipping page')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Harvest links from Paulys Realenzyklopädie der classischen \
        Altertumswissenschaft articles to Wikidata objects.')
    parser.add_argument('--log', type=str, help='target file for log',
                        default='paulyre.log')
    parser.add_argument('--level', type=int, default=20,
                        help='numeric value for loglevel')
    parser.add_argument('output', type=str,
                        help='target file for extracted data')
    args = parser.parse_args()

    site = pywikibot.Site('de', 'wikisource')
    site.login()
    site_dewp = pywikibot.Site('de', 'wikipedia')
    site_dewp.login()
    data_repository = site.data_repository()
    data_repository.login()

    template = pywikibot.Page(site, 'Template:' + TEMPLATE_NAME)

    logging.basicConfig(filename=args.log,level=args.level)

    with open(args.output, 'w', 1) as csvfile:
        fieldnames = ['title', 'wikipedia', 'wikidata', 'subject']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for page in template.embeddedin(namespaces=0, content=True):
            try:
                process_page(page)
            except Exception as err:
                logging.error('Processing {} failed: {}'.format(page, err))
