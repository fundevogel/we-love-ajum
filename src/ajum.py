import os
import re
import glob
import time
import urllib

import requests
from bs4 import BeautifulSoup as bs

from .helpers import load_json, dump_json, dict2hash


class Ajum():
    """
    Tools for interacting with the AJuM database
    """

    # Database directory
    cache_dir = '.db'


    # Request headers
    headers = {
        'From': 'maschinenraum@fundevogel.de',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0',
    }


    # Waiting time after each request
    timer = 3.0


    # GENERAL

    def call_api(self, params: dict = {}, headers: dict = {}) -> str:
        """
        Connects to database API
        """

        # Base URL
        base_url = 'https://www.ajum.de/index.php'

        # Build query parameters
        params = {**{'s': 'datenbank'}, **params}

        # Build request headers
        headers = {**self.headers, **headers}

        # Wait some time ..
        time.sleep(self.timer)

        # .. before making an API call
        return requests.get(base_url, params=params, headers=headers).text


    def id2file(self, review: str) -> str:
        return '{}/{}.html'.format(self.cache_dir, review)


    def file2id(self, html_file: str) -> str:
        return os.path.splitext(os.path.basename(html_file))[0]


    def hash2file(self, params: dict) -> str:
        return '{}/{}.json'.format(self.cache_dir, dict2hash(params))


    # RESULTS PAGES

    def fetch_results(self, params: dict) -> bool:
        """
        Fetches results page for a given query & caches its review IDs
        """

        # Determine JSON file
        json_file = self.hash2file(params)

        # If not cached yet ..
        if not os.path.exists(json_file):
            # .. send request
            html = self.call_api(params)

            # .. extract review IDs & store them
            dump_json(self.extract_results(html), json_file)

        return os.path.exists(json_file)


    def extract_results(self, html: str) -> list:
        """
        Extracts review IDs from a single results page
        """

        # Load redirects for ill-conceived review links
        redirects = load_json('redirects.json')

        # Take care of duplicates since review IDs appear twice per page
        reviews = set()

        # Loop over all hyperlinks inside the main table element
        for link in bs(html, 'html.parser').find('td', {'class': 'td_body'}).find_all('a'):
            # Parse their URL & extract query parameters
            query = urllib.parse.parse_qs(urllib.parse.urlparse(link['href']).query)

            # Check for review ID in link
            if 'id' in query:
                # Assign review identifier
                review = query['id'][0]

                # Replace invalid requests ..
                if review in redirects:
                    # .. with valid ones
                    review = redirects[review]

                # If review ID is somehow shady ..
                if not re.match(r'\d+', review):
                    # .. report it
                    click.echo('Invalid review ID "{}", exiting ..'.format(review))

                    # .. abort execution
                    click.Context.abort()

                # Store review ID
                reviews.add(review)

        return list(reviews)


    ##
    # Meta class, combining ..
    #
    # - `fetch_results`   - Fetches results page for a given query & caches its review IDs
    # - `extract_results` - Extracts review IDs from a single results page
    ##
    def get_results(self, params: dict) -> list:
        """
        Collects review IDs of all results pages for a given query
        """

        # Send request
        html = self.call_api(params)

        # Check number of results
        matches = re.findall(r'wurden\s(\d+)\sRezensionen', html)

        # Skip if no results
        if not matches:
            return []

        if not self.fetch_results(params):
            return []

        # Create data file array
        json_files = []

        # Iterate over subsequent results pages
        for i in range(1, (int(matches[0]) // 50) + 1):
            # Set starting point
            params['start'] = str(i * 50)

            # If successfully fetching a results page & storing its review IDs ..
            if self.fetch_results(params):
                # .. add its JSON file representation
                json_files.append(self.hash2file(params))

        # Load review IDs of ..
        # (1) .. initial results page (first 50 reviews)
        reviews = self.extract_results(html)

        # (2) .. subsequent result pages ..
        for json_file in json_files:
            # .. adding their review IDs
            reviews.extend(load_json(json_file))

        return reviews


    # SINGLE REVIEW PAGE

    def fetch_review(self, review: str) -> bool:
        """
        Fetches single review & caches its HTML
        """

        # Define HTML file for review page
        html_file = self.id2file(review)

        # If not cached yet ..
        if not os.path.exists(html_file):
            # (1) .. send request
            html = self.call_api({'id': review})

            # (2) .. validate response by checking for disclaimer
            if 'presserechtliche Verantwortung' not in html:
                return False

            # (3) .. save response text
            with open(html_file, 'w') as file:
                file.write(html)

        return os.path.exists(html_file)


    def extract_review(self, html: str) -> dict:
        """
        Extracts single review data from HTML
        """

        def process(string: str) -> str:
            # Process string
            # (1) Remove surrounding whitespaces
            # (2) Replace unicode characters such as ..
            # (a) .. 'Index' (used as quotation marks)
            # (b) .. 'Set Transmit State' (used as quotation marks)
            # (c) .. 'Next Line' (used as triple dots)
            # (d) .. 'Cancel character' (used as quotation marks in titles)
            # (e) .. 'Start of Protected Area' (used as hyphen/endash)
            return string.strip().replace(u'\u0084', '"').replace(u'\u0093', '"').replace(u'\u0085', '...').replace(u'\u0094', '". ').replace(u'\u0096', '-')
            # TODO: For using a dictionary/table instead,
            # see https://stackoverflow.com/a/54451873

        # Prepare review data
        data = {}

        # Iterate over HTML elements ..
        # (1) .. replacing break tags with newline characters for proper text formatting
        # (2) .. looking for main table (with class `td_body`)
        # (3) .. looking for form element
        # (4) .. looking for its sibling table element
        # (5) .. selecting all data cells in there
        for tag in bs(html.replace('<br>', '\n'), 'html.parser').find('td', {'class': 'td_body'}).find('form').find_next_sibling('table').find_all('td'):
            # When reaching maximum number of data records ..
            if len(data) == 21:
                # .. abort loop for good
                break

            # Since label fields always contain colon ..
            if not ':' in tag.text:
                # .. no colon means no action
                continue

            # Extract data
            for term in [
                'Autor',
                'Titel',
                'ISBN',
                'Übersetzer',
                'Originalsprache',
                'Illustrator',
                'Seitenanzahl',
                'Verlag',
                'Gattung',
                'Reihe',
                'Jahr',
                'Preis',
                'Inhalt',
                'Lesealter',
                'Einsatzmöglichkeiten',
                'WolgastPreis',
                'Bewertung',
                'Schlagwörter',
                'Anmerkungen',
                'Beurteilungstext',
            ]:
                # If information was extracted before ..
                if term in data:
                    # .. skip it
                    continue

                # Process data
                if tag.text.replace('\n', '').replace(' ', '') == term + ':':
                    # Prepare text for further processing
                    texts = [process(line) for line in re.split('\n', tag.find_next_sibling('td').text)]

                    # Check if current field contains  running text ..
                    if term in ['Inhalt', 'Anmerkungen', 'Beurteilungstext']:
                        # .. and keep text parts in list
                        data[term] = [text for text in texts if text]

                    # .. or is a simple text field
                    else:
                        # Trim whitespaces & combine parts
                        data[term] = ' '.join(texts).strip()

                    # Abort loop for current term
                    break

            # Since field 'binding' has no label ..
            if tag.text.strip() == 'Preis:':
                # .. build it manually
                data['Einband'] = tag.find_next_sibling('td').find_next_sibling('td').find_next_sibling('td').text.strip()

        # If field 'ISBN' is present ..
        if 'ISBN' in data:
            # .. remove whitespaces inside
            data['ISBN'] = data['ISBN'].replace(' ', '')

        return data


    ##
    # Meta class, combining ..
    #
    # - `fetch_review`   - Fetches single review & caches its HTML
    # - `extract_review` - Extracts single review data from HTML for single review
    ##
    def get_review(self, review: str) -> dict:
        """
        Collects single review data for given review ID
        """

        if not self.fetch_review(review):
            return {}

        with open(self.id2file(review), 'r') as file:
            html = file.read()

        return self.extract_review(html)


    # MULTIPLE REVIEW PAGES

    def get_reviews(self, reviews: list) -> dict:
        """
        Grabs data for multiple reviews
        """

        # Create data array
        data = {}

        # Loop over reviews ..
        for review in reviews:
            # .. grabbing their data
            data[review] = self.get_review(review)

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
        force: bool = True
    ) -> dict:
        """
        Queries remote database for matching reviews
        """

        # Build query parameters
        params = {
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
            'Audio-CD',  # deprecated but matching 30 archived reviews
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

        # Get review IDs
        reviews = self.get_results(params)

        # Extract data for each review
        return self.get_reviews(reviews)


    # LOCAL DATABASE BACKUP

    def clear_cache(self) -> None:
        """
        Removes cached index files
        """

        # Loop over JSON files ..
        for file in glob.glob(self.cache_dir + '/*.json'):
            # .. deleting each on of them
            os.remove(file)
