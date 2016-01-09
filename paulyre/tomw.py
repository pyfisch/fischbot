import csv

import mwparserfromhell

fieldnames = ['title', 'wikipedia', 'wikidata', 'subject']

print('''{|
! RE Artikel
! Wikipediaartikel
! Wikidata
! Thema''')

with open('fastpaulyre.csv', 'r') as csvfile:
    for line in csv.DictReader(csvfile):
        print('|-')
        print('|[[wikisource:de:{}]]'.format(line['title']))
        if line['wikipedia'].startswith("???"):
            print('| not found: [[w:de:{}]]'.format(line['wikipedia'][4:]))
        else:
            print('|[[w:de:{}]]'.format(line['wikipedia']))
        print('|[[{}]]'.format(line['wikidata']))
        print('|[[{}]]'.format(line['subject']))

print('|}')
