#!/usr/bin/env python3

import csv
from datetime import date, timedelta
import json
import re

import requests
from requests.adapters import HTTPAdapter
from requests_html import HTML
from urllib3.util import Retry


# www.in-pocasi.cz obcas prestane na chvili odpovidat, protoze posilame moc dotazu
# Proto potrebujeme specialni session pro knihovnu requests, ktera opakuje chybujici requesty
# Adaptovano z https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
    retries=10,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


retry_session = requests_retry_session()


# Stahne seznam stanic z www.in-pocasi.cz
# U kazde vrati jeji ID, nazev a polohu
def stahni_seznam_stanic():
    print('Stahuji seznam stanic...')
    req = retry_session.get('https://www.in-pocasi.cz/aktualni-pocasi/ajax/stations.json.php')

    stanice = []
    for zaznam_stanice in json.loads(req.text)['points']:
        stanice.append({
            'id_stanice': zaznam_stanice['id'],
            'nazev_stanice': zaznam_stanice['name'],
            'lat': zaznam_stanice['lat'],
            'lon': zaznam_stanice['lng'],
        })

    return stanice


# Nascrapuje pocasi daneho regionu v dany den z www.in-pocasi.czc
# Vrati seznam udaju ze vsech stanic a dni obsahujici id_stanice, datum, max_teplota, srazky a naraz_vetru
def stahni_pocasi_regionu(cislo_regionu, datum):
    req = retry_session.get(f'https://www.in-pocasi.cz/archiv/archiv.php?historie={datum.isoformat()}&region={cislo_regionu}')

    html = HTML(html=req.text)

    # Prvni dve tabulky odpovidajici tomuto selektoru obsahuji data z klimatickych, respektive soukromych stanic
    tabulky_s_pocasim = html.find('.page table tbody')[:2]

    pocasi_na_stanicich = []

    # Projde tabulky radek po radku a vytahni z nich spravna data
    for tabulka in tabulky_s_pocasim:
        for radek in tabulka.find('tr'):
            bunky = radek.find('td')

            # ID stanice je obsazene v prvni bunce v HTML odkazu na jeji stranku
            # vytahneme jej specialnim regularnim vyrazem
            adresa_stanice = bunky[0].find('a', first=True).attrs['href']
            id_stanice = re.search(r'/([^/]+)/$', adresa_stanice).group(1)

            # Max teplota je v druhe bunce ve formatu -12.3 °C
            if bunky[1].text != '-':
                max_teplota = bunky[1].text[:-3]
            else:
                max_teplota = None

            # Vitr je ve ctvrte bunce ve formatu 12.3 km/h
            if bunky[3].text != '-':
                naraz_vetru = bunky[3].text[:-5]
            else:
                naraz_vetru = None

            # Srazky jsou v pate bunce ve formatu 12.3 mm
            if bunky[4].text != '-':
                srazky = bunky[4].text[:-3]
            else:
                srazky = None

            pocasi_na_stanicich.append({
                'id_stanice': id_stanice,
                'datum': datum,
                'max_teplota': max_teplota,
                'srazky': srazky,
                'naraz_vetru': naraz_vetru
            })

    return pocasi_na_stanicich


# Nascrapuje seznam stanic do souboru stanice.csv
# a pocasi v zadanem casovem rozpeti v zadanych regionech do souboru pocasi.csv
def stahni_pocasi(datum_od, datum_do, regiony):
    # Stahne seznam stanic a ulozi ho ve spravnem formatu do souboru stanice.csv
    seznam_stanic = stahni_seznam_stanic()
    with open('stanice.csv', 'w', newline='') as stanice_csv:
        fieldnames = ['id_stanice', 'nazev_stanice', 'lat', 'lon']
        writer = csv.DictWriter(stanice_csv, fieldnames=fieldnames)
        writer.writeheader()
        for stanice in seznam_stanic:
            writer.writerow(stanice)

    # Pripravi si seznam datumu, ktere stahnout
    datumy = []
    datum = datum_od
    den = timedelta(days=1)
    while datum <= datum_do:
        datumy.append(datum)
        datum += den

    # Stahne pocasi v zadanem casovem rozpeti v zadanych regionech do souboru pocasi.csv
    with open('pocasi.csv', 'w', newline='') as pocasi_csv:
        fieldnames = ['datum', 'id_stanice', 'max_teplota', 'srazky', 'naraz_vetru']
        writer = csv.DictWriter(pocasi_csv, fieldnames=fieldnames)
        writer.writeheader()
        for datum in datumy:
            for cislo_regionu in regiony:
                print(f'\rStahuji pocasi ze dne {datum.isoformat()} z regionu {cislo_regionu}...', end='')
                pocasi_v_regionu = stahni_pocasi_regionu(cislo_regionu, datum)
                writer.writerows(pocasi_v_regionu)

            print()


# Spusteni hlavni funkce skriptu, pokud je skript volany naprimo z terminalu
if __name__ == "__main__":
    # Vstupni parametry pro stahovani
    datum_od = date(2016, 1, 1)
    datum_do = date(2020, 6, 30)
    regiony = [
        2,   # Jihomoravsky
        4,   # Kralovehradecky
        10,  # Stredocesky
        11,  # Ustecky
    ]

    stahni_pocasi(datum_od, datum_do, regiony)
