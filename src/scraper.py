import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from src import hook





class RubareInformazioniYahoooo:
    BASE_URL = "https://www.immobiliare.it/api-next/search-list/listings/"
    VRT = (
        "45.485954%2C9.204326%3B45.479035%2C9.217289%3B45.456467%2C9.217289"
        "%3B45.447196%2C9.210507%3B45.445812%2C9.187329%3B45.443343%2C9.179"
        "173%3B45.445089%2C9.16106%3B45.46375%2C9.146724%3B45.476207%2C9.14"
        "329%3B45.48818%2C9.156854%3B45.487578%2C9.17471%3B45.484871%2C9.18"
        "6814%3B45.490827%2C9.191964%3B45.485954%2C9.204326"
    )
    BBOX_COORDS = {
        'minLat': 45.432792, 'maxLat': 45.501414,
        'minLng': 9.115734, 'maxLng': 9.244823
    }
    CITY_BBOX = {
        'minLat': 45.398932, 'maxLat': 45.528479,
        'minLng': 9.138222, 'maxLng': 9.228344
    }
    AREA_STATIC = {
        'fkRegione': 'lom', 'idProvincia': 'MI', 'idComune': '8042', 'idNazione': 'IT'
    }
    ZONE_IDS = [10054, 10061, 10060, 10059, 10050, 10057, 10055, 10056, 10047, 10053, 10046, 10049]
    QUARTIERI_IDS = [10295, 12635, 12799, 11805, 12805, 12682, 10268, 12276, 10270]
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15"
                      " (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
        "DNT": "1",
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "if-none-match": "W/\"h4me1yagm23v0d\"",
        "priority": "u=1, i",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-arch": "\"x86\"",
        "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"137.0.7151.120\","
                                       " \"Chromium\";v=\"137.0.7151.120\", \"Not/A)Brand\";v=\"24.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }

    def __init__(self, row):
        config_path = Path(__file__).parents[1] / 'config' / 'filter.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            data_filter = json.load(f)

        config_path = Path(__file__).parents[1] / 'config' / 'settings.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            data_settings = json.load(f)

        self.config_filter = config_path
        self.filters = data_filter['seen_ids']
        self.webhook = data_settings['webhook']
        self.delay = int(data_settings['delay']) / 1000
        self.row = row
        self.task_name = row['task_name']
        self.mode = row['mode']
        self.row['min_price'] = round(int(row['room_min_price']) * int(row['people']))
        self.row['max_price'] = round(int(row['room_max_price']) * int(row['people']))

    def format_me(self, update):
        t = datetime.now().strftime("%H:%M:%S")
        txt = f'[ {t} ] [ {self.task_name} ] [ {update} ]'
        return txt

    def build_house(self, house):
        real = house.get('realEstate', {})
        title = real.get('title', 'No title')
        url = house.get('seo', {}).get('url', 'No URL')
        code = int(url.split('annunci/')[1].split('/')[0])

        if code in self.filters:
            return False

        props = real.get('properties', [{}])[0]
        price = real.get('price', {}).get('self.format_metedValue', 'N/A')
        price_integer = int(real.get('price', {}).get('value', 'N/A'))
        bathrooms = props.get('bathrooms', 'N/A')
        bedrooms = props.get('bedRoomsNumber', 'N/A')
        surface = props.get('surface', 'N/A')
        price_per_room = round(price_integer / int(bedrooms))
        photos = props.get('multimedia', {}).get('photos', [])
        img = photos[0].get('urls', {}).get('small') if photos else None
        balcony = 'No'

        for feat in props.get('featureList', []):
            if feat.get('type') == 'balcony' or 'balcone' in feat.get('label', '').lower():
                balcony = 'Yes'
                break

        return {
            'title': title,
            'price': price,
            'bathrooms': bathrooms,
            'bedrooms': bedrooms,
            'surface': surface,
            'img': img,
            'url': url,
            'balcony': balcony,
            'price_per_room': price_per_room,
            'task_name': self.task_name,
            'code': code
        }

    def check_listing(self, listings_list):
        good = []
        for house in listings_list:
            real = house.get('realEstate', {})
            price = int(real.get('price', {}).get('value', 'N/A'))
            props = real.get('properties', [{}])[0]
            bedrooms = int(props.get('bedRoomsNumber', 'N/A'))
            furniture = next(
                (item['label'] for item in props.get('featureList', {}) if item.get('type') == 'furniture'), 'N/A')
            if furniture == 'Arredato' or furniture == 'arredato':
                if bedrooms == int(self.row['bedrooms']):
                    price_per_bedroom = price / bedrooms
                    if int(self.row['room_min_price']) <= price_per_bedroom <= int(self.row['room_max_price']):
                        house_data = self.build_house(house)
                        if house_data:
                            good.append(house_data)
        return good

    def get_listings(self, i):
        def include(param, name):
            val = self.row.get(param, '')
            return f"&{name}={val}" if val not in ('', '-') else ''

        if self.mode == 'coords':
            url = [
                f"{self.BASE_URL}?vrt={self.VRT}",
                "&idContratto=2&idCategoria=1",
                include('min_price', 'prezzoMinimo'),
                include('max_price', 'prezzoMassimo'),
                include('min_sqr', 'superficieMinima'),
                include('max_sqr', 'superficieMassima'),
                include('min_rooms', 'localiMinimo'),
                include('max_rooms', 'localiMassimo'),
                "&__lang=it",
                f"&minLat={self.BBOX_COORDS['minLat']}&maxLat={self.BBOX_COORDS['maxLat']}",
                f"&minLng={self.BBOX_COORDS['minLng']}&maxLng={self.BBOX_COORDS['maxLng']}",
                f"&pag={i}&paramsCount=10",
                "&path=%2Fsearch-list%2F"
            ]
            complete_url = ''.join(url)

        elif self.mode == 'areas':
            parts = [
                f"{self.BASE_URL}?fkRegione={self.AREA_STATIC['fkRegione']}"
                f"&idProvincia={self.AREA_STATIC['idProvincia']}"
                f"&idComune={self.AREA_STATIC['idComune']}"
            ]
            for i, zid in enumerate(self.ZONE_IDS):
                parts.append(f"&idMZona[{i}]={zid}")
            for i, qid in enumerate(self.QUARTIERI_IDS):
                parts.append(f"&idQuartiere[{i}]={qid}")
            parts.append(
                f"&idNazione={self.AREA_STATIC['idNazione']}"
                "&idContratto=2&idCategoria=1"
                + include('min_price', 'prezzoMinimo')
                + include('max_price', 'prezzoMassimo')
                + include('min_sqm', 'superficieMinima')
                + include('max_sqm', 'superficieMassima')
                + include('min_rooms', 'localiMinimo')
                + include('max_rooms', 'localiMassimo') +
                f"&__lang=it&pag={i}&paramsCount=11"
                "&path=%2Fsearch-list%2F"
            )
            complete_url = ''.join(parts)

        elif self.mode == 'city':
            url = [
                f"{self.BASE_URL}?fkRegione={self.AREA_STATIC['fkRegione']}"
                f"&idProvincia={self.AREA_STATIC['idProvincia']}"
                f"&idComune={self.AREA_STATIC['idComune']}"
                f"&idNazione={self.AREA_STATIC['idNazione']}"
                "&idContratto=2&idCategoria=1",
                include('min_price', 'prezzoMinimo'),
                include('max_price', 'prezzoMassimo'),
                include('min_sqm', 'superficieMinima'),
                include('max_sqm', 'superficieMassima'),
                include('min_rooms', 'localiMinimo'),
                include('max_rooms', 'localiMassimo'),
                "&__lang=it",
                f"&pag={i}&paramsCount=6",
                "&path=%2Faffitto-case%2Fmilano%2F"
            ]
            complete_url = ''.join(url)
        else:
            print(self.format_me('Error getting endpoint url.'))
            return False

        resp = requests.get(complete_url, headers=self.HEADERS)
        if resp.status_code == 404:
            return False

        listings = resp.json()['results']
        return self.check_listing(listings)

    def update_filter(self, code):
        with open(self.config_filter, "r", encoding="utf-8") as f:
            data = json.load(f)['seen_ids']

        data.append(code)

        with open(self.config_filter, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def loop_pages(self):
        i = 1
        filtered_houses = []
        print(self.format_me(f'Getting listings - page {i}...'))

        # get them fatass listings
        while True:
            new_houses = self.get_listings(i)
            if not new_houses:
                break
            filtered_houses.extend(new_houses)
            i += 1

        # send them hooks and update them shi
        for house in filtered_houses:
            print(self.format_me('Successfully found a new listing!'))
            hook.send_house_hook(house)
            #self.update_filter(house['code'])

        if len(filtered_houses) == 0:
            print(self.format_me('Cannot find new listings.'))

        print(self.format_me(f'Sleeping {round(self.delay)}s...'))
        time.sleep(self.delay)


def main(row):
    bot = RubareInformazioniYahoooo(row)
    bot.loop_pages()

