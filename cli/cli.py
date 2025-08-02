import json
import sys
from pathlib import Path
from src import thread_create


config_path = Path(__file__).parents[1] / 'config' / 'settings.json'

main_menu = '''
Select an option:
1) Start tasks
2) Manage webhook
3) Quit
Enter choice: '''


def load_settings():
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}")
        sys.exit(10)


def main():
    while True:
        choice = input(main_menu).strip()
        if choice == '1':
            thread_create.start_threads_from_csv()
        elif choice == '2':
            settings = load_settings()

            url = input("Enter Discord webhook URL: ").strip()
            settings['webhook'] = url
            delay = input(f"Enter the desired delay (current {settings['delay']}ms): ")
            settings['delay'] = delay

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

                print("Settings updated successfully.\n")
        elif choice == '3':
            sys.exit(0)
        else:
            print("Invalid choice. Please enter a number between 1 and 3.\n")
