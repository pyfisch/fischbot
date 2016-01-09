import csv

import mwparserfromhell
import requests


# Fails:
# Fail Astronomie
# Fail Arda (Mariza)
# Fail Burgas
# Fail Dengizich
# Fail Măcin
# Fail Berenike II.
# Fail Attalos I.
# Fail Gnaeus Arulenus Caelius Sabinus
# Fail Gubazes II.
# Fail Aelia Eudoxia
# Fail Lucius Arruntius (Konsul 6)
# Fail Arminius
# Fail Aristion von Paros
# Fail Aronstabgewächse
# Fail Pontarlier
# Fail Civitavecchia
# Fail Ariobarzanes (Phrygien)
# Fail Peschiera del Garda
# Fail Ariaspes
# Fail Augusta Raurica
# Fail Ariassos
# Fail Ariobarzanes
# Fail Herodes Atticus
# Fail Demosthenes (Militär)
# Fail Alpheios (Mythologie)
# Fail Aristarete
# Fail Delphin (Sternbild)
# Fail Agrippa (Philosoph)
# Fail Sextus Aelius Catus
# Fail Sallustius Bonosus



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
            wde_title = re.get(9).value
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

while True:
    print("Running query 3")
    processing = []
    while True:
        if len(processing) == 50 or not len(intermediate_result2):
            break
        item = intermediate_result2.pop()
        if not item[1]:
            final_result.append(item)
        else:
            processing.append(item)
    if not processing:
        break
    titles = [str(page[1]) for page in processing]
    payload['titles'] = '|'.join(titles)
    entities = requests.get(base_url, params=payload).json()['entities']
    for e in entities.values():
        if not 'sitelinks' in e:
            continue
        title = e['sitelinks']['dewiki']['title']
        q = e['title']
        try:
            index = titles.index(title)
        except:
            print("Fail", title)
            continue
        elem = processing[index]
        processing[index] = None
        elem[3] = q
        final_result.append(elem)
    final_result.extend([x for x in processing if x])

print("*** STEP THREE COMPLETE ***")


with open('fastpaulyre.csv', 'w') as csvfile:
    fieldnames = ['title', 'wikipedia', 'wikidata', 'subject']
    writer = csv.writer(csvfile)
    writer.writerow(fieldnames)
    for row in final_result:
        writer.writerow(row)

print("*** ALL COMPLETE ***")
