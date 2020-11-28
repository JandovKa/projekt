#!/usr/bin/env python3

import csv
from datetime import date
import json
import re
from requests_html import HTMLSession
import requests

html_session = HTMLSession()
requests_sesion = requests.Session()


# Nascrapuje seznam oblasti s citaci z www.mereninavstevnosti.cz
# Vrati seznam oblasti (pro kazdou jeji ID a nazev)
def stahni_oblasti():
    print('Stahuji oblasti...')
    req = html_session.get('https://www.mereninavstevnosti.cz/')

    # Seznamy oblasti jsou v elementu tridy seznam_chko
    seznamy_oblasti = req.html.find('.seznam_chko')[1:]

    oblasti = []
    for seznam_oblasti in seznamy_oblasti:
        # Jednotlive oblasti jsou reprezentovany jako odkazy s tridou polozka_chko
        odkazy = seznam_oblasti.find('.polozka_chko')
        for odkaz in odkazy:
            nazev_oblasti = odkaz.text
            # ID oblasti je obsazeno v odkazu na jeji stranku
            # vytahneme jej specialnim regularnim vyrazem
            id_oblasti = re.search(r'nodeid=(\d+)', odkaz.attrs['href']).group(1)
            oblasti.append({
                'id_oblasti': id_oblasti,
                'nazev_oblasti': nazev_oblasti
            })

    return oblasti


# Stahne citace v dane oblasti
# Vrati seznam citacu (u kazdeho jeho ID, nazev a polohu)
def stahni_citace_v_oblasti(id_oblasti):
    print(f'Stahuji citace v oblasti ID {id_oblasti}')
    citace = []
    req = html_session.get(f'http://www.mereninavstevnosti.cz/Stezka2.aspx?nodeid={id_oblasti}')

    # Polohy citacu ziskame z elementu pro vytvareni mapy citacu v Mapy.cz
    # Tento element ma specialni atribut ng-init, ktery obsahuje seznam citacu s jejich nazvem a ID
    # Tento seznam je ve tvaru Javascriptoveho pole s objekty
    # Nemuzeme ho nacist jako JSON, ale musime je trochu upravit (dat klice a hodnoty do dvojitych uvozovek)
    element_citacu = req.html.find('div[ng-init^=init_counters]', first=True)
    pole_citacu = element_citacu.attrs['ng-init'][14:-1]
    parsovane_citace = json.loads(re.sub(r'([a-z]+):\'([^\']*)\'', r'"\1":"\2"', pole_citacu))

    # Pro kazdy citac stahneme i jeho polohu, a vsechno ulozime
    for citac in parsovane_citace:
        id_citace = citac['nodeid']
        nazev_citace = citac['name']

        # Stahneme stranku s detaily citace
        # Jeho polohu najdeme ve zdrojovem kodu stranky ve skriptu pro pridani znacky do Google Maps
        # Vytahneme ji specialnim regularnim vyrazem
        req2 = requests_sesion.get(f'https://www.mereninavstevnosti.cz/Scitac.aspx?nodeid={id_citace}')
        poloha = re.search(r'addGoogleMarker\(map, markersArray, ([0-9.]+), ([0-9.]+),', req2.text)
        lat = poloha.group(1)
        lon = poloha.group(2)

        citace.append({
            'id_citace': id_citace,
            'nazev_citace': nazev_citace,
            'lat': lat,
            'lon': lon
        })

    return citace


# Stahne data ze spravneho citace ve spravnem casovem rozpeti
def stahni_data_citace(id_citace, datum_od, datum_do):
    print(f'Stahuji data citace ID {id_citace}')
    # Data jsou dostupna na internim API na mereninavstevnosti.cz
    adresa = f'https://www.mereninavstevnosti.cz/GetData.aspx?counters={id_citace}&d1={datum_od.isoformat()}&d2={datum_do.isoformat()}&period=YMD'
    req = requests_sesion.get(adresa)
    data = json.loads(req.text)

    return data


# Stahne data o citacich a data z citacu ve spravnem casovem rozpeti a ulozi je do CSV souboru
def stahni_data_citacu(datum_od, datum_do):
    # Stahne data o oblastech (ID, nazvy) a ulozi je do souboru oblasti.csv
    oblasti = stahni_oblasti()
    with open('oblasti.csv', 'w', newline='') as oblasti_csv:
        fieldnames = ['id_oblasti', 'nazev_oblasti']
        writer = csv.DictWriter(oblasti_csv, fieldnames=fieldnames)
        writer.writeheader()

        for oblast in oblasti:
            writer.writerow(oblast)

    # Stahne data o citacich (ID, nazvy, polohu) a ulozi je do souboru citace.csv
    # Zaroven pro kazdy citac zaznamena, v jakych oblastech je obsazen, pro budouci ulozeni
    citace = []
    oblasti_x_citace = []
    id_stazenych_citacu = set()
    with open('citace.csv', 'w', newline='') as citace_csv:
        fieldnames = ['id_citace', 'nazev_citace', 'lat', 'lon']
        writer = csv.DictWriter(citace_csv, fieldnames=fieldnames)
        writer.writeheader()

        for oblast in oblasti:
            citace_v_oblasti = stahni_citace_v_oblasti(oblast['id_oblasti'])
            for citac in citace_v_oblasti:
                oblasti_x_citace.append({
                    'id_oblasti': oblast['id_oblasti'],
                    'id_citace': citac['id_citace']
                })
                if not citac['id_citace'] in id_stazenych_citacu:
                    id_stazenych_citacu.add(citac['id_citace'])
                    citace.append(citac)
                    writer.writerow(citac)

    # Ulozi parovani citacu a oblasti do souboru oblasti_x_citace.csv
    # (kazdy citac muze byt soucasti vice nez jedne oblasti)
    with open('oblasti_x_citace.csv', 'w', newline='') as oblasti_x_citace_csv:
        fieldnames = ['id_oblasti', 'id_citace']
        writer = csv.DictWriter(oblasti_x_citace_csv, fieldnames=fieldnames)
        writer.writeheader()
        for oblast_x_citac in oblasti_x_citace:
            writer.writerow(oblast_x_citac)

    # Stahne a ulozi data ze vsech citacu do souboru data.csv
    with open('data.csv', 'w', newline='') as data_csv:
        fieldnames = [
            'id_citace', 'datum',
            'Total', 'TotalIN', 'TotalOUT',
            'PesiTotal', 'PesiIN', 'PesiOUT',
            'CykloTotal', 'CykloIN', 'CykloOUT',
            'AutaTotal', 'AutaIN', 'AutaOUT',
            'AutobusyTotal', 'AutobusyIN', 'AutobusyOUT',
        ]
        writer = csv.DictWriter(data_csv, fieldnames=fieldnames)
        writer.writeheader()

        for citac in citace:
            data_citace = stahni_data_citace(citac['id_citace'], datum_od, datum_do)
            for radek in data_citace:
                # Pred ulozenim prejmenuje nektere zaznamy, aby se lepe parovaly s ostatnimi CSV soubory
                radek['id_citace'] = radek['ScitacNodeID']
                radek['datum'] = radek['YMD']
                del radek['ScitacNodeID']
                del radek['YMD']
                writer.writerow(radek)


# Spusteni hlavni funkce skriptu, pokud je skript volany naprimo z terminalu
if __name__ == "__main__":
    # Vstupni parametry pro stahovani
    datum_od = date(2016, 1, 1)
    datum_do = date(2020, 6, 30)

    stahni_data_citacu(datum_od, datum_do)
