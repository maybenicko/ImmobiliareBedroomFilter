import csv
import threading
from pathlib import Path
from src import scraper


def start_threads_from_csv():
    config_path = Path(__file__).parents[1] / 'tasks.csv'
    with open(config_path, newline='') as f:
        reader = csv.DictReader(f)

        threads = []
        for row in reader:
            thread = threading.Thread(target=scraper.main, args=(row,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
