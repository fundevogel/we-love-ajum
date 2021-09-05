import os
import re
import glob
import time
import urllib

import requests
from bs4 import BeautifulSoup as bs

from src.helpers import load_json, dump_json


class Ajum():
    """
    Tools for interacting with the AJuM database
    """

    VERSION = '0.1.0'


    # Cache directory
    cache_dir = '.db'


    # Request headers
    headers = {
        'From': 'maschinenraum@fundevogel.de',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
    }


    # Waiting time after each request
    timer = 3.0


    def __init__(self, index_file: str = 'index.json', db_file: str = 'database.json'):
        self.db_file = db_file
        self.index_file = index_file


    # GENERAL

    def call_api(self, params: dict):
        """
        Connects to database API
        """

        return requests.get('https://www.ajum.de/index.php', params=params, headers=self.headers)


    # RESULTS PAGE

    def extract_reviews(self, html: str) -> list:
        """
        Extracts review IDs from results page HTML
        """

        # Take care of duplicates since review IDs appear twice per page
        reviews = set()

        # Loop over all hyperlinks inside the main table element
        for link in bs(html, 'html.parser').find('td', {'class': 'td_body'}).find_all('a'):
            # Parse their URL & extract query parameters
            query = urllib.parse.parse_qs(urllib.parse.urlparse(link['href']).query)

            # If URL links to review ..
            if 'id' in query:
                # .. store its ID
                reviews.add(query['id'][0])

        return list(reviews)


    def get_review_ids(self, params: dict) -> list:
        """
        Fetches review IDs for results page
        """

        # Send request
        response = self.call_api(params)

        # Extract reviews
        return self.extract_reviews(response.text)


    # SINGLE REVIEW PAGE

    def extract_data(self, html) -> dict:
        """
        Extracts data from review page HTML
        """

        # Prepare review data
        data = {}

        for tag in bs(html, 'html.parser').find('td', {'class': 'td_body'}).find_all('td'):
            # Extract data
            for term in [
                # Left column
                'Autor',
                'Titel',
                'Übersetzer',
                'Illustrator',
                'Verlag',
                'Reihe',
                'Preis',
                'Inhalt',
                'Wolgast Preis',
                'Schlagwörter',
                'Anmerkungen',
                'Beurteilungstext',

                # Right column
                'ISBN',
                'Originalsprache',
                'Seitenanzahl',
                'Gattung',
                'Jahr',
                'Einsatzmöglichkeiten',
                'Bewertung',
            ]:
                if tag.text.strip() == term + ':':
                    # Prepare text for further processing
                    texts = [line.strip() for line in re.split('\n', tag.find_next_sibling('td').text)]

                    # Determine text separator
                    separator = '\n' if term in ['Inhalt', 'Anmerkungen', 'Beurteilungstext'] else ' '

                    # Trim whitespaces
                    data[term] = separator.join(texts).strip()

            # Make adjustments
            # (1) If author has trailing comma ..
            if 'Autor' in data and data['Autor'][-1] == ',':
                # .. remove it
                data['Autor'] = data['Autor'][:-1]

            # (2) Since it has no label ..
            if tag.text.strip() == 'Preis:':
                # .. build binding manually
                data['Einband'] = tag.find_next_sibling('td').find_next_sibling('td').find_next_sibling('td').text.strip()

        return data


    def fetch_review(self, review: str) -> dict:
        """
        Fetches data for single review
        """

        # Define HTML file for review page
        html_file = '{}/{}.html'.format(self.cache_dir, review)

        # If not cached yet ..
        if not os.path.exists(html_file):
            # (1) .. send request
            response = self.call_api({
                's': 'datenbank',
                'id': review,
            })

            # (2) Validate response by checking for disclaimer
            if 'Namenskürzel' not in response.text:
                return {}

            # (2) .. save response
            with open(html_file, 'w') as file:
                file.write(response.text)

        # Load review page from HTML file
        with open(html_file, 'r') as file:
            html = file.read()

        # Extract review data
        return self.extract_data(html)


    # MULTIPLE REVIEW PAGES

    def fetch_reviews(self, reviews: list) -> dict:
        """
        Fetches data for multiple reviews
        """

        # Prepare review data store
        data = {}

        # Loop over review IDs & fetch their dara
        for review in reviews:
            data[review] = self.fetch_review(review)

        return data


    # DATABASE QUERIES

    def query(self,
        search_term: str = '',
        tag: str = '',
        title: str = '',
        first_name: str = '',
        last_name: str = '',
        illustrator: str = '',
        rating: str = '',
        application: str = '',
        media_type: str = '',
        age: str = '',
        genre: str = '',
        archive: bool = False,
        wolgast: bool = False,
    ) -> dict:
        """
        Queries remote database for matching reviews
        """

        # Build query parameters
        params = {
            # 'id': '',
            's': 'datenbank',
            'do': 'suchen',
            'suchtext': search_term,
            'schlagwort': '0',
            'titel': title,
            'autor1': first_name,
            'autor2': last_name,
            'illustrator': illustrator,
            'bewertung': '0',
            'einsatz': '0',
            'medienart': '0',
            'alter': '0',
            'gattung': '0',
            'archiv': '',
            'wolgast': '',
            'Submit': 'Suchen',
        }

        # Respect 'select' fields
        # (1) Tag
        if tag in [
            'Abenteuer',
            'Aggressivität',
            'AIDS',
            'Alter',
            'Angst',
            'Arbeitslosigkeit',
            'Arbeitswelt',
            'Aufklärung',
            'Außenseiter',
            'Behinderung',
            'Bildende Kunst',
            'Biografie',
            'Computer',
            'Emanzipation',
            'Ethik',
            'Fabeln',
            'Familie',
            'Fantastik',
            'Fernsehen',
            'Flucht',
            'Fremde Kulturen',
            'Freundschaft',
            'Frieden',
            'Geschichte',
            'Homosexualität',
            'Indianer',
            'Interkulturelle Kommunikation',
            'Junge',
            'Krankheit',
            'Krieg',
            'Kriminalität',
            'LesePeter',
			'Liebe/Erste Liebe',
            'Literatur',
            'Mädchen',
            'Märchen',
            'Medien',
            'Missbrauch',
            'Musik',
            'Nationalsozialismus',
            'Natur',
            'Naturschutz/Umweltschutz',
            'Philosophie',
            'Politik',
            'Rassismus',
            'Rechtsextremismus',
            'Religion',
            'Sagen',
            'Schüler',
            'Schwangerschaft',
            'Seefahrt',
            'Seeräuber',
            'Sekte',
            'Sexualität',
            'Spannung',
            'Sport',
            'Spuk',
            'Sterben',
            'Sucht',
            'Technik',
            'Terrorismus',
            'Tiere',
            'Tod',
            'Trennung',
            'Ungleichheit',
            'Virtuelle Realität',
            'Weihnachten',
            'Zukunft',
        ]:
            params['schlagwort'] = urllib.parse.quote_plus(tag)

        # (2) Rating
        if rating in [
            'empfehlenswert',
            'sehr empfehlenswert',
            'nicht empfehlenswert',
        ]:
            params['bewertung'] = urllib.parse.quote_plus(rating)

        # (3) Field of application
        if application in [
            'Klassenlesestoff',
            'Büchereigrundstock für Arbeitsbücherei',
        ]:
            params['einsatz'] = urllib.parse.quote_plus(application)

        # (4) Media type
        if media_type in [
            'Abreißkalender',
            'Arbeitsheft',
            'Audio-CD',
            'Audio-CD / Hörbuch / Musik',
            'Audio-Kassette',
            'Bilderbuch',
            'Block',
            'broschiert',
            'Broschur',
            'Buch',
            'Buch (Print, gebunden)',
            'Buch, gebunden',
            'Buch: Aufklappbuch',
            'Buch: Badewannenbuch',
            'Buch: Broschur',
            'Buch: Fühl- oder Spiel(Bilder)buch',
            'Buch: Hardcover',
            'Buch: Hartpappe',
            'Buch: Heftbindung',
            'Buch: Pop-up-Buch',
            'Buch: Softcover',
            'Buch: Spielbuch',
            'Buch: Taschenbuch',
            'Buch: Zieh- oder Drehbuch',
            'CD',
            'CD-ROM',
            'CD/DVD-ROM / Software',
            'DVD',
            'Halbleinen',
            'Hardcover',
            'Hartpappe',
            'Heft',
            'Hörbuch',
            'Kalender',
            'Karten',
            'Kartenspiel',
            'Klappbroschur',
            'Klappenbroschur',
            'Lernheft',
            'Paperback',
            'Pappbilderbuch',
            'Softcover',
            'Spiel',
            'Spiel / Arbeitsheft',
            'Spielbuch',
            'Spielkarten',
            'Spiralblock',
            'Tagesabreißkalender',
            'Taschenbuch',
            'Taschenbuch / Heft / Broschur',
        ]:
            params['medienart'] = urllib.parse.quote_plus(media_type)

        # (5) Recommendable age range
        if age in [
            '0-3',
            '4-5',
            '6-7',
            '8-9',
            '10-11',
            '12-13',
            '14-15',
            '16-17',
            'ab 18',
        ]:
            params['alter'] = urllib.parse.quote_plus(age)

        # (6) Genre
        if genre in [
            'Abenteuererzählung',
            'Adoleszenzroman',
            'Adventskalender',
            'Anthologie',
            'Atlas',
            'Autobiografie/Autobiografische Erzählung',
            'Bastelbuch',
            'Bastelheft',
            'Bilderbuch',
            'Bilderbucherzählung',
            'Bilderbuchkino',
            'Bildergeschichte',
            'Biografie',
            'Biografie/Biografische Erzählung',
            'Briefroman',
            'Cartoon',
            'Comic',
            'Comic / Graphic Novel',
            'Detektivgeschichte',
            'Erstlesebuch',
            'Erstlesetext',
            'erzählendes Sachbuch',
            'Erzählung',
            'Erzählung / Roman',
            'Erzählungen',
            'Fabel',
            'Fachbuch',
            'Fachliteratur',
            'Fantastik',
            'Fantastische Erzählung',
            'Fantasy',
            'Gedichte',
            'Geschichte',
            'Geschichten',
            'Geschichtensammlung',
            'Graphic Novel',
            'Gruselgeschichte',
            'Gutenachtgeschichten',
            'Historische Erzählung',
            'Historischer Roman',
            'Hörbuch',
            'Hörspiel',
            'Jugendbuch',
            'Jugendroman',
            'Jugendthriller',
            'Kalender',
            'Kinderbuch',
            'Kindergeschichten',
            'Kinderlieder',
            'Kinderroman',
            'Kochbuch',
            'Kriminalerzählung',
            'Kunstbuch',
            'Kurzgeschichten',
            'Lernbuch',
            'Lernspiel',
            'Lernspiel(e)',
            'Lesebuch',
            'Lexikon',
            'Liebesroman',
            'Lieder',
            'Liederbuch',
            'Liedersammlung',
            'Lyrik',
            'Lyrik / Lieder',
            'Malbuch',
            'Musical',
            'Musik',
            'Mädchenbuch',
            'Mädchenroman',
            'Märchen',
            'Märchen / Fabeln / Sagen',
            'Quiz',
            'Ratgeber',
            'Reisebericht',
            'Reiseführer',
            'Roman',
            'Rätsel',
            'Rätsel(spiele)',
            'Sach-Bilderbuch',
            'Sachbilderbuch',
            'Sachbuch',
            'Sachliteratur',
            'Sachliteratur / Sachbilderbuch',
            'Sachliteratur/Sachbilderbuch',
            'Sagen',
            'Schülerhilfe',
            'Science Fiction',
            'Sonstige',
            'Spiel',
            'Spiel- und Bastelbuch',
            'Spielbuch',
            'Tagebuchroman',
            'Texte von Jugendlichen',
            'Texte von Kindern',
            'Theater',
            'Thriller',
            'Tierbuch',
            'Tiergeschichte',
            'Tiergeschichten',
            'Vorlesebuch',
            'Vorlesegeschichten',
            'Wahrnehmungsspiel(e)',
            'Weihnachtsgeschichte',
            'Weihnachtsgeschichten',
            'Wimmelbuch',
            'Witze',
            'Wörterbuch',
            'Zieh-, Dreh, Aufklapp-, Fühl- oder Spiel(bilder)buch',
        ]:
            params['gattung'] = urllib.parse.quote_plus(genre)

        # Respect 'checkbox' fields
        # (1) Whether to include archived reviews
        if wolgast is True:
            params['wolgast'] = 'JA'

        # (2) Whether to show Wolgast winners only
        if archive is True:
            params['archiv'] = 'JA'

        # Send request
        response = self.call_api(params)

        # Check number of results
        matches = re.findall('wurden\s(\d+)\sRezensionen', response.text)

        # if not matches or matches.len() != 2:
        # Skip if no results
        if not matches:
            return []

        # Extract review IDs from results pages
        # (1) Initial page (first 50 reviews)
        reviews = self.extract_reviews(response.text)

        # (2) Subsequent pages
        for i in range(1, (int(matches[0]) // 50) + 1):
            # Set starting point
            params['start'] = str(i * 50)

            # Fetch them review IDs
            reviews.extend(self.get_review_ids(params))

        # Extract data for each review
        return self.fetch_reviews(reviews)


    # LOCAL DATABASE BACKUP

    def backup_db(self, force: bool = False) -> None:
        """
        Backs up remote database
        """

        # If 'force' mode is activated ..
        if force:
            # .. clear exisiting cache first
            self.clear_cache()

        # Loop over 'AJuM' database results pages
        for i in range(0, 176):
            json_file = '{}/{}.json'.format(self.cache_dir, str(i))

            # If not cached yet ..
            if not os.path.exists(json_file):
                print('Fetching {} ..'.format(json_file))

                # (1) .. fetch all review IDs
                reviews = self.get_review_ids({
                    's': 'datenbank',
                    'start': str(i * 50),
                    'do': 'suchen',
                    'bewertung': '0',
                    'titel': '',
                    'autor1': '',
                    'autor2': '',
                    'illustrator': '',
                    'suchtext': '',
                    'alter': '0',
                    'einsatz': '0',
                    'schlagwort': '0',
                    'gattung': '0',
                    'medienart': '0',
                    'wolgast': '',
                    'archiv': '',
                })

                # (2) .. store them
                dump_json(reviews, json_file)

                # (3) .. and wait three seconds
                time.sleep(self.timer)

            # Load review IDs
            reviews = load_json(json_file)

            # Fetch all review pages
            for review in set(reviews):
                # Define HTML file for review page
                html_file = '{}/{}.html'.format(self.cache_dir, review)

                # If not cached yet ..
                if not os.path.exists(html_file):
                    print('Fetching {} ..'.format(html_file))

                    # (1) .. fetch data
                    self.fetch_review(review)

                    # (2) .. and wait three seconds
                    time.sleep(self.timer)


    def clear_cache(self) -> None:
        """
        Removes cached index files
        """
        for file in glob.glob(self.cache_dir + '/*.json'):
            os.remove(file)


    # INDEX SEARCH

    def build_index(self) -> None:
        """
        Builds index of reviews per ISBN
        """

        # Prepare index storage
        index = {}

        for html_file in glob.glob(self.cache_dir + '/*.html'):
            # Get review ID from filename
            review = os.path.splitext(os.path.basename(html_file))[0]

            # Determine ISBN
            # (1) Fetch review data
            data = self.fetch_review(review)

            # (2) Check if ISBN is present ..
            if 'ISBN' not in data:
                # .. otherwise we got a problem
                continue

            # (3) Assign reviewed ISBN
            isbn = data['ISBN']

            # Create record (if not present)
            if isbn not in index:
                index[isbn] = []

            # Add review to ISBN
            index[isbn].append(review)

        # Create index file
        dump_json(index, self.index_file)


    def get_reviews(self, isbn) -> dict:
        """
        Fetches review(s) for given ISBN
        """
        if not os.path.exists(self.index_file):
            raise

        index = load_json(self.index_file)

        if isbn not in index:
            return {}

        return self.fetch_reviews(index[isbn])


    # LOCAL DATABASE

    def build_db(self) -> None:
        """
        Builds local database
        """

        # Ensure that index file exists
        if not os.path.exists(self.index_file):
            raise

        # Prepare database store
        data = {}

        for isbn, reviews in load_json(self.index_file).items():
            # Create record
            data[isbn] = {}

            for review in reviews:
                # Define HTML file for review page
                html_file = '{}/{}.html'.format(self.cache_dir, review)

                # If not cached yet ..
                if not os.path.exists(html_file):
                    # .. we got a problem
                    raise

                # Load review page from HTML file
                with open(html_file, 'r') as file:
                    html = file.read()

                # Extract data & store it
                data[isbn][review] = self.extract_data(html)

        # Create database file
        dump_json(data, self.db_file)
