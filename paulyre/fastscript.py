import csv

import mwparserfromhell
import requests
import pywikibot

base_url = 'https://de.wikisource.org/w/api.php'
payload = {
    'format': 'json',
    'action': 'query',
    'prop': 'revisions',
    'rvprop': 'content',
    'titles': 'Vorlage:RE',
    'generator': 'transcludedin',
    'gtiprop': 'title',
    'gtilimit': '50',
    'titles': 'Vorlage:RE',
}
continue_at = None

def process_page(page):
    sde_title = page['title']
    text = page['revisions'][0]['*']
    wikicode = mwparserfromhell.parse(text)
    templates = wikicode.filter_templates()
    re_templates = [t for t in templates if t.name.matches('RE')]
    if len(re_templates) == 1:
        re = re_templates[0]
        if re.has(9, ignore_empty=True):
            wde_title = re.get(9).value.strip()
            return [sde_title, wde_title, None, None]
    return [sde_title, None, None, None]

intermediate_result = []

while True:
    print("Running query 1")
    r = requests.get(base_url, params=payload)
    s = r.json()
    pages = s['query']['pages']
    for page in pages.values():
        intermediate_result.append(process_page(page))
    try:
        payload['gticontinue'] = r.json()['continue']['gticontinue']
    except:
        break

print("*** STEP ONE COMPLETE ***")

base_url = 'https://www.wikidata.org/w/api.php'
payload = {
    'action': 'wbgetentities',
    'sites': 'dewikisource',
    'format': 'json',
    'props': 'info|sitelinks',
}

intermediate_result2 = []

while True:
    print("Running query 2")
    processing = intermediate_result[:50]
    del intermediate_result[:50]
    if not processing:
        break;
    titles = [page[0] for page in processing]
    payload['titles'] = '|'.join(titles)
    entities = requests.get(base_url, params=payload).json()['entities']
    for e in entities.values():
        if not 'sitelinks' in e:
            continue
        title = e['sitelinks']['dewikisource']['title']
        q = e['title']
        index = titles.index(title)
        elem = processing[index]
        processing[index] = None
        elem[2] = q
        intermediate_result2.append(elem)
    intermediate_result2.extend([x for x in processing if x])

print("*** STEP TWO COMPLETE ***")


base_url = 'https://www.wikidata.org/w/api.php'
payload = {
    'action': 'wbgetentities',
    'sites': 'dewiki',
    'format': 'json',
    'props': 'info|sitelinks',
}

final_result = []

def get_hard_titles(elements):
    result = []
    for x in elements:
        for e in x:
            print(e)
            try:
                wde_page = pywikibot.Page(pywikibot.Site('de', 'wikipedia'), e[1])
                if wde_page.isRedirectPage():
                    wde_page = wde_page.getRedirectTarget()
                e[3] = pywikibot.ItemPage.fromPage(wde_page).title()
            except pywikibot.NoPage:
                pass
            result.append(e)
    return result


def step3(elements):
    result = []
    in_progress = dict()
    while elements:
        elem = elements.pop()
        if elem[1]:
            if not elem[1] in in_progress:
                in_progress[elem[1]] = []
            in_progress[elem[1]].append(elem)
        else:
            result.append(elem)
    print("*** Filtered result")
    hard_cases = []
    while in_progress:
        titles = []
        processing = []
        while (len(processing) < 50) and in_progress:
            (key, values) = in_progress.popitem()
            titles.append(key)
            processing.append(values)
        payload['titles'] = '|'.join(titles)
        entities = requests.get(base_url, params=payload).json()['entities']
        for e in entities.values():
            if not 'sitelinks' in e:
                continue
            title = e['sitelinks']['dewiki']['title']
            q = e['title']
            try:
                for x in processing[titles.index(title)]:
                    x[3] = q
                result.extend(processing[titles.index(title)])
                processing[titles.index(title)] = None
            except ValueError:
                pass
        hard_cases.extend([x for x in processing if x])
    print("*** Resolved simple cases")
    result.extend(get_hard_titles(hard_cases))
    return result


final_result = step3(intermediate_result2)

# while True:
#     print("Running query 3")
#     processing = []
#     while True:
#         if len(processing) == 50 or not len(intermediate_result2):
#             break
#         item = intermediate_result2.pop()
#         if not item[1]:
#             final_result.append(item)
#         else:
#             processing.append(item)
#     if not processing:
#         break
#     titles = [str(page[1]) for page in processing]
#     payload['titles'] = '|'.join(titles)
#     entities = requests.get(base_url, params=payload).json()['entities']
#     for e in entities.values():
#         if not 'sitelinks' in e:
#             continue
#         title = e['sitelinks']['dewiki']['title']
#         q = e['title']
#         try:
#             index = titles.index(title)
#         except:
#             print("Fail", title)
#             continue
#         elem = processing[index]
#         processing[index] = None
#         elem[3] = q
#         final_result.append(elem)
#     final_result.extend([x for x in processing if x])

print("*** STEP THREE COMPLETE ***")


with open('fastpaulyre.csv', 'w') as csvfile:
    fieldnames = ['title', 'wikipedia', 'wikidata', 'subject']
    writer = csv.writer(csvfile)
    writer.writerow(fieldnames)
    for row in final_result:
        writer.writerow(row)

print("*** ALL COMPLETE ***")
