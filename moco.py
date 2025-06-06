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


def get_book_date() -> str:
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        return config['book_date']


def get_activity_sum() -> str:
    book_date = get_book_date()
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


def create_activity(project_id: int, task_id: int, activity: str, book_time: int) -> None:
    requests.post(
        url=get_moco_url() + "/activities",
        headers={
            "Authorization": "Token token=" + get_token()
        },
        json={
            "date": get_book_date(),
            "description": activity,
            "project_id": int(project_id),
            "task_id": int(task_id),
            "seconds": int(book_time)
        }
    )


def print_menu(stdscr, selected_row_idx, menu_entries):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    date = get_book_date()
    hours = get_activity_sum()
    headline = f"Total hours on {date}: {hours}"
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


def navigate_menu(stdscr, menu_entries):
    current_row = 0
    print_menu(stdscr, current_row, menu_entries)
    while True:
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_entries) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return current_row
        elif key == ord('q'):
            exit(0)
        print_menu(stdscr, current_row, menu_entries)


def main(stdscr):
    # Clear screen
    stdscr.clear()

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    while True:
        projects = get_projects()
        project_row = navigate_menu(stdscr, projects)
        tasks = get_tasks(project_row)
        task_row = navigate_menu(stdscr, tasks)
        hours = [round(x * 0.5, 1) for x in range(1, 21)]
        hour_row = navigate_menu(stdscr, hours)
        activities = get_activities()
        activity_row = navigate_menu(stdscr, activities)

        create_activity(
            project_id=get_project_id(project_row),
            task_id=get_task_id(project_row, task_row),
            activity=get_activity_by_id(activity_row),
            book_time=int(hours[hour_row] * 3600)
        )

        stdscr.clear()
        stdscr.refresh()


curses.wrapper(main)
