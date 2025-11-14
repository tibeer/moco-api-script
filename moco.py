# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyyaml==6.0.2",
#     "requests==2.32.3",
# ]
# ///
#
# Script to book times in moco easily
#
##########################################
import curses
import requests
import yaml
from datetime import datetime, timedelta

config_file = './moco.yaml'
secret_file = './secret.yaml'


def get_projects() -> list:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return [project['name'] for project in config['projects']]


def get_project_id(project_row: int) -> int:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['projects'][project_row]['id']


def get_tasks(project_row: int) -> list:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return [task['name'] for task in config['projects'][project_row]['tasks']]


def get_task_id(project_row: int, task_row: int) -> int:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['projects'][project_row]['tasks'][task_row]['id']


def get_activities() -> list:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['activities']


def get_activity_by_id(activity_row: int) -> str:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['activities'][activity_row]


def get_moco_url() -> str:
    with open(secret_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['moco_url']


def get_token() -> str:
    with open(secret_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['token']


def get_base_date() -> str:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        book_date = config.get('book_date', '').strip()
        if book_date:
            return book_date
        else:
            return datetime.today().strftime("%Y-%m-%d")


def get_date_selection(base_date_str: str, direction: str) -> list:
    """Generates a list of the last 5 days from the base date."""
    dates = []
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")

    if direction == "Past 5 days":
        for i in range(5):
            day = base_date - timedelta(days=i)
            dates.append(day.strftime("%Y-%m-%d"))
    elif direction == "Next 7 days":
        for i in range(7):
            day = base_date + timedelta(days=i + 1)
            dates.append(day.strftime("%Y-%m-%d"))
    return dates


def get_activity_sum(book_date: str) -> str:
    response = requests.get(
        url=get_moco_url() + f"/activities?from={book_date}&to={book_date}",
        headers={
            "Authorization": "Token token=" + get_token()
        }
    )
    total = 0
    for activity in response.json():
        total += activity['seconds']
    return str(total / 3600)


def create_activity(project_id: int, task_id: int, activity: str, book_time: int, book_date: str) -> None:
    requests.post(
        url=get_moco_url() + "/activities",
        headers={
            "Authorization": "Token token=" + get_token()
        },
        json={
            "date": book_date,
            "description": activity,
            "project_id": int(project_id),
            "task_id": int(task_id),
            "seconds": int(book_time)
        }
    )


def print_menu(stdscr, selected_row_idx, menu_entries, headline: str):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(0, w // 2 - len(headline) // 2, headline)
    for idx, row in enumerate(menu_entries):
        x = w // 2 - len(str(row)) // 2
        y = h // 2 - len(menu_entries) // 2 + idx + 1
        if 0 <= y < h:
            if idx == selected_row_idx:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, str(row))
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, str(row))
    stdscr.refresh()


def navigate_menu(stdscr, menu_entries, headline: str):
    current_row = 0
    filtered_entries = menu_entries.copy()
    search_mode = False
    search_query = ""

    print_menu(stdscr, current_row, filtered_entries, headline)

    while True:
        key = stdscr.getch()

        if search_mode:
            if key in (10, 13):  # Enter: exit search mode
                search_mode = False
                current_row = 0
            elif key in (27,):  # Esc: cancel search
                search_mode = False
                search_query = ""
                filtered_entries = menu_entries.copy()
                current_row = 0
            elif key in (curses.KEY_BACKSPACE, 127):
                search_query = search_query[:-1]
            else:
                search_query += chr(key)

            # Update filtered list
            filtered_entries = [entry for entry in menu_entries if search_query.lower() in str(entry).lower()]
            current_row = min(current_row, len(filtered_entries) - 1)
            print_menu(stdscr, current_row, filtered_entries, f"{headline} /{search_query}")
            continue

        # --- Normal navigation ---
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(filtered_entries) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return menu_entries.index(filtered_entries[current_row])
        elif key == ord('q'):
            exit(0)
        elif key == ord('/'):  # Start search mode
            search_mode = True
            search_query = ""
            filtered_entries = menu_entries.copy()

        print_menu(stdscr, current_row, filtered_entries, headline)



def main(stdscr):
    # Clear screen
    stdscr.clear()

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)


    # --- Select direction (past or future) ---
    direction_options = ["Past 5 days", "Next 7 days"]
    direction_idx = navigate_menu(stdscr, direction_options, "Select Date Range")
    direction = direction_options[direction_idx]

    while True:
        # --- New Date Selection ---
        date_options = get_date_selection(get_base_date(), direction)
        date_idx = navigate_menu(stdscr, date_options, "Select a Date")
        selected_date = date_options[date_idx]

        # --- Dynamic Headline with selected date ---
        hours_on_day = get_activity_sum(selected_date)
        projects_headline = f"Select Project for {selected_date} (Total: {hours_on_day}h)"

        projects = get_projects()
        project_row = navigate_menu(stdscr, projects, projects_headline)

        tasks_headline = f"Select Task for {selected_date}"
        tasks = get_tasks(project_row)
        task_row = navigate_menu(stdscr, tasks, tasks_headline)
        
        hours_headline = f"Select Hours for {selected_date}"
        hours = [round(x * 0.5, 1) for x in range(1, 21)]
        hour_row = navigate_menu(stdscr, hours, hours_headline)
        
        activities_headline = f"Select Activity for {selected_date}"
        activities = get_activities()
        activity_row = navigate_menu(stdscr, activities, activities_headline)

        create_activity(
            project_id=get_project_id(project_row),
            task_id=get_task_id(project_row, task_row),
            activity=get_activity_by_id(activity_row),
            book_time=int(hours[hour_row] * 3600),
            book_date=selected_date
        )

        stdscr.clear()
        stdscr.refresh()


curses.wrapper(main)