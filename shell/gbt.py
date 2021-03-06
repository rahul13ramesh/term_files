#!/usr/bin/python3

# Git bulk toolkit

from argparse import ArgumentParser
from pathlib import Path
from subprocess import Popen, PIPE, check_output
from threading import Thread
from time import sleep
import configparser
import os
import re
import shutil
import sys
import datetime
import math


class ConfigValue:

    DEVELOPMENT_DIR = "home/rahul/"
    REPO_BLACKLIST = "repo_blacklist"


class TerminalStyle:

    WHITE = "\033[97m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    CLEAR = "\033[0m"


class LogEntry:
    def __init__(self, repo, timestamp, relative_date, author, message):

        self._repo = repo
        self._timestamp = timestamp
        self._relative_date = relative_date
        self._author = author
        self._message = message

    def repo(self):
        return self._repo

    def timestamp(self):
        return self._timestamp

    def relative_date(self):
        return self._relative_date

    def author(self):
        return self._author

    def message(self):
        return self._message


class GitStatusWorker:
    def __init__(self, directory, worker_id, submodule_depth):

        self._directory = directory
        self._worker_id = worker_id
        self._submodule_depth = submodule_depth

        self._work_in_progress = False
        self._repo_id = ""
        self._branch = "unknown"
        self._location = "Up to date"
        self._modified_files = []
        self._untracked_files = []
        self._log_entries = []

        self._error_pulling = 0
        self._error_checking_out = 0
        self._error_getting_status = 0
        self._error_fetching = 0
        self._error_getting_log = 0

    def status(self):

        if self._work_in_progress is False:
            self._error_getting_status = 0
            self._work_in_progress = True
            self._thread = Thread(target=self._thread_method_status)
            self._thread.start()

    def fetch(self):

        if self._work_in_progress is False:
            self._error_fetching = 0
            self._work_in_progress = True
            self._thread = Thread(target=self._thread_method_fetch)
            self._thread.start()

    def pull(self):

        if self._work_in_progress is False:
            self._error_pulling = 0
            self._work_in_progress = True
            self._thread = Thread(target=self._thread_method_pull)
            self._thread.start()

    def checkout(self, branch_name):

        if self._work_in_progress is False:
            self._error_checking_out = 0
            self._work_in_progress = True
            self._thread = Thread(target=self._thread_method_checkout, args=(branch_name,))
            self._thread.start()

    def log(self, days_to_log):

        if self._work_in_progress is False:
            self._error_getting_log = 0
            self._work_in_progress = True
            self._thread = Thread(target=self._thread_method_log, args=(days_to_log,))
            self._thread.start()

    def directory(self):

        return self._directory

    def is_submodule(self):

        return self._submodule_depth > 0

    def short_name(self):

        return os.path.basename(os.path.normpath(self._directory))

    def display_name(self):

        if self.is_submodule():
            return (" " * (self._submodule_depth - 1)) + "↳ " + self.short_name()
        else:
            return self.short_name()

    def branch(self):

        return self._branch

    def is_gbt_repo(self):

        return self._repo_id == "a5eab786a76c18fb765ae60742f970da2f5408fc"

    def location(self):

        return self._location[0].upper() + self._location[1:]

    def modified_files(self):

        return self._modified_files

    def untracked_files(self):

        return self._untracked_files

    def log_entries(self):

        return self._log_entries

    def work_in_progress(self):

        return self._work_in_progress

    def error_pulling(self):

        return self._error_pulling

    def error_checking_out(self):

        return self._error_checking_out

    def error_getting_status(self):

        return self._error_getting_status

    def error_fetching(self):

        return self._error_fetching

    def error_getting_log(self):

        return self._error_getting_log

    def error_occurred(self):

        return self.error_pulling() != 0 or self.error_checking_out() != 0 or self.error_getting_status() != 0 or self.error_fetching() != 0 or self.error_getting_log() != 0

    def join(self):

        self._thread.join()

    def _thread_method_status(self):

        self._modified_files.clear()
        self._untracked_files.clear()

        try:
            output = check_output(["git", "rev-list", "HEAD"], cwd=self._directory, stderr=FNULL)
            output = output.decode("UTF-8")
            self._repo_id = output.split("\n")[-2]
        except:
            pass

        output = check_output(["git", "status", "-sb"], cwd=self._directory)
        output = output.decode("UTF-8")

        self._process_status_output(output)

        self._work_in_progress = False

    def _thread_method_log(self, days_to_log):

        try:
            delimiter = "~|~"
            since_date = (datetime.date.today() - datetime.timedelta(days=days_to_log)).strftime("%Y-%m-%d")
            output = check_output(["git", "log", "--pretty=format:%ct" + delimiter + "%cr" + delimiter + "%cn" + 


delimiter + "%s %d", "--since=" + since_date, "--branches"], cwd=self._directory)
            output = output.decode("UTF-8")
            lines = output.split("\n")

            for line in lines:
                if len(line) > 0:
                    parts = line.split(delimiter)

                    if len(parts) == 4:
                        entry = LogEntry(self.short_name(), parts[0], parts[1], parts[2], parts[3])
                        self._log_entries.append(entry)
                    else:
                        self._error_getting_log += 1

        except:
            self._error_getting_log += 1

        self._work_in_progress = False

    def _thread_method_fetch(self):

        if self.is_submodule() == False:
            process = Popen(["git", "fetch"], stdout=PIPE, stderr=PIPE, cwd=self._directory)
            process.communicate()
            self._error_fetching = process.returncode

        self._work_in_progress = False

    def _thread_method_checkout(self, branch_name):

        if self.is_submodule() == False:
            process = Popen(["git", "checkout", branch_name], stdout=PIPE, stderr=PIPE, cwd=self._directory)
            process.communicate()
            self._error_checking_out = process.returncode

        self._work_in_progress = False

    def _thread_method_pull(self):

        if self.is_submodule() == False:
            process = Popen(["git", "pull", "--recurse-submodules"], stdout=PIPE, stderr=PIPE, cwd=self._directory)
            process.communicate()
            self._error_pulling = process.returncode

        self._work_in_progress = False

    def _process_status_output(self, output):

        lines = output.split("\n")

        for line in lines:
            if line.startswith("##"):
                line = line.replace("## ", "")
                if "..." in line:
                    self._branch = line[: line.find("...")]
                else:
                    self._branch = line

                result = re.search("\[(.*)\]", line)
                if result:
                    self._location = result.group(1)

                if "No commits yet on" in self._branch:
                    self._branch = self._branch.split()[-1]
                    self._location = "Empty"

            else:
                parts = line.split()

                if len(parts) == 2:
                    indicator = parts[0]
                    filename = parts[1]

                    if "M" in indicator:
                        self._modified_files.append(filename)

                    if "??" in indicator:
                        self._untracked_files.append(filename)


def get_repositories(parent_directory, git_workers, repo_blacklist, submodule_depth = 0):

    allRepos = [
        "/home/rahul/Documents/config/term_files/",
        "/home/rahul/Documents/config/Vim__files/",
        "/home/rahul/Documents/personal/wikiNotes/",
        "/home/rahul/Documents/personal/texTemplates/",
    ]
    for path in allRepos:
        abs_path = os.path.join(parent_directory, path)
        git_config_path = os.path.join(abs_path, ".git")
        git_workers.append(GitStatusWorker(abs_path, len(git_workers), submodule_depth))

def upgrade_existing_config():

    config_file_path = get_config_file_path()
    development_dir = ""


def get_config_value(name):

    config_file_path = get_config_file_path()
    config = configparser.ConfigParser()

    config.read(config_file_path)

    if "default" not in config:
        return ""

    default_section = config["default"]

    if name not in default_section:
        return ""

    return default_section[name]


def set_config_value(name, value):

    config_file_path = get_config_file_path()
    config = configparser.ConfigParser()

    config.read(config_file_path)

    if "default" not in config:
        config["default"] = {}

    config["default"][name] = value

    with open(config_file_path, "w") as config_file:
        config.write(config_file)


def get_progress_bar_string(progress):
    progress_bar_width = 30
    bar_characters = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉"]

    progress_bar = "▕" + TerminalStyle.DIM + TerminalStyle.BLUE

    total_width = math.floor(progress * progress_bar_width)
    remaining_width = (progress * progress_bar_width) % 1

    partial_width = math.floor(remaining_width * len(bar_characters))
    partial_char = bar_characters[partial_width]
    if (progress_bar_width - total_width - 1) < 0:
        partial_char = ""
    progress_bar += "█" * total_width + partial_char + " " * (progress_bar_width - total_width - 1)
    progress_bar += TerminalStyle.CLEAR + "▏"

    return progress_bar


def display_progress(action_text, action_error_method):

    while True:
        workers_busy = sum(1 for worker in git_workers if worker.work_in_progress())
        
        workers_complete = len(git_workers) - workers_busy
        progress_bar = get_progress_bar_string(workers_complete / len(git_workers))
        progress_line = "\r" + progress_bar + " " + action_text + " (" + str(workers_busy) + " workers still busy) "
        sys.stdout.write(progress_line)

        if workers_busy == 0:
            sys.stdout.write("\r")
            sys.stdout.flush()
            break

    for worker in git_workers:
        worker.join()


def pull_all(git_workers):

    for worker in git_workers:
        worker.pull()

    display_progress("Pulling", "error_pulling")


def checkout_all(git_workers, branch_name):

    for worker in git_workers:
        worker.checkout(branch_name)

    display_progress("Checking out " + branch_name, "error_checking_out")


def log_all(git_workers, days_to_log):

    for worker in git_workers:
        worker.log(days_to_log)

    display_progress("Getting logs for last " + str(days_to_log) + " day(s)", "error_getting_log")


def fetch_all(git_workers):

    for worker in git_workers:
        worker.fetch()

    display_progress("Fetching", "error_fetching")


def status_all(git_workers):

    for worker in git_workers:
        worker.status()

    display_progress("Getting status", "error_getting_status")


def get_config_file_path():

    return str(Path.home()) + "/.config/gbt.conf"


def get_development_dir():

    return " "


def print_statuses(git_workers):

    horizontal_line()

    longest_subdirectory_name = 0
    longest_branch_name = 0
    longest_location = 0

    for worker in git_workers:
        if len(worker.display_name()) > longest_subdirectory_name:
            longest_subdirectory_name = len(worker.display_name())

        if len(worker.branch()) > longest_branch_name:
            longest_branch_name = len(worker.branch())

        if len(worker.location()) > longest_location:
            longest_location = len(worker.location())

    output_lines = []
    work_to_do = False
    gbt_has_update = False

    for worker in git_workers:

        if worker.error_occurred():
            status_string = TerminalStyle.RED + worker.display_name().ljust(longest_subdirectory_name + longest_branch_name + longest_location + 10)
            status_string += "Error(s): "

            if worker.error_fetching() != 0:
                status_string += "Fetching (" + str(worker.error_fetching()) + ")"

            if worker.error_pulling() != 0:
                status_string += "Pulling (" + str(worker.error_pulling()) + ")"

            if worker.error_checking_out() != 0:
                status_string += "Checking out branch (" + str(worker.error_checking_out()) + ")"

            status_string += TerminalStyle.CLEAR

            print(status_string)

        else:
            name_string = TerminalStyle.DIM if worker.is_submodule() else ""
            name_string += worker.display_name().ljust(longest_subdirectory_name)
            name_string += TerminalStyle.CLEAR if worker.is_submodule() else ""

            location_string = ""

            if "behind" in worker.location().lower():

                gbt_has_update = worker.is_gbt_repo()

                if len(worker.modified_files()) + len(worker.untracked_files()) > 0:
                    location_string += TerminalStyle.RED
                else:
                    location_string += TerminalStyle.YELLOW

                location_string += worker.location().rjust(longest_location)
                work_to_do = True

            elif "ahead" in worker.location().lower():
                location_string += TerminalStyle.GREEN + worker.location().rjust(longest_location)
                work_to_do = True

            else:
                location_string += worker.location().rjust(longest_location)

            location_string += TerminalStyle.CLEAR

            branch_string = worker.branch().ljust(longest_branch_name)

            if worker.branch() != "master":
                branch_string = TerminalStyle.WHITE + worker.branch().ljust(longest_branch_name) + TerminalStyle.CLEAR

            status_string = ""

            if len(worker.modified_files()) + len(worker.untracked_files()) == 0:
                status_string += TerminalStyle.BLUE + "Nothing to commit" + TerminalStyle.CLEAR

            else:
                work_to_do = True
                status_string += TerminalStyle.YELLOW
                status_string += str(len(worker.modified_files()) + len(worker.untracked_files())) + " file(s) modified/untracked"
                status_string += TerminalStyle.CLEAR

            print(
                name_string
                + TerminalStyle.DIM
                + " [ "
                + TerminalStyle.CLEAR
                + location_string
                + TerminalStyle.DIM
                + " on "
                + TerminalStyle.CLEAR
                + branch_string
                + TerminalStyle.DIM
                + " ] "
                + TerminalStyle.CLEAR
                + status_string
            )

    horizontal_line()

    return work_to_do, gbt_has_update


def print_logs(git_workers):

    horizontal_line()

    all_log_entries = []

    for worker in git_workers:
        all_log_entries.extend(worker.log_entries())

    all_log_entries.sort(key=lambda x: x.timestamp(), reverse=True)

    longest_date = 0
    longest_repo = 0
    longest_author = 0

    for entry in all_log_entries:
        if len(entry.relative_date()) > longest_date:
            longest_date = len(entry.relative_date())

        if len(entry.repo()) > longest_repo:
            longest_repo = len(entry.repo())

        if len(entry.author()) > longest_author:
            longest_author = len(entry.author())

    term_columns, term_lines = shutil.get_terminal_size((80, 20))

    for entry in all_log_entries:
        repo_string = entry.repo().ljust(longest_repo)
        date_string = entry.relative_date().ljust(longest_date)
        author_string = entry.author().ljust(longest_author)

        meta_data_string = repo_string + TerminalStyle.DIM + " [ " + TerminalStyle.CLEAR + author_string + " " + date_string + TerminalStyle.DIM + " ] " + TerminalStyle.CLEAR
        message = entry.message()
        space_remaining = term_columns - len(meta_data_string)
        message_string = (message[: space_remaining - 3] + "...") if len(message) > space_remaining else message

        print(meta_data_string + TerminalStyle.BLUE + message_string + TerminalStyle.CLEAR)

    horizontal_line()


def horizontal_line():

    term_columns, term_lines = shutil.get_terminal_size((80, 20))
    print(TerminalStyle.DIM + "─" * term_columns + TerminalStyle.CLEAR)


def create_workers():

    repo_blacklist = get_config_value(ConfigValue.REPO_BLACKLIST)
    repo_blacklist = repo_blacklist.split(",")

    git_workers = []

    get_repositories(development_dir, git_workers, repo_blacklist)

    git_workers.sort(key=lambda x: x.directory())

    return git_workers


def show_help():
    print(TerminalStyle.YELLOW + "Git Bulk Toolkit (gbt) by Ben Pring" + TerminalStyle.CLEAR)
    print("")
    print("gbt status")
    print(" - Show status for all repositories under development directory")
    print("")
    print("gbt fetch")
    print(" - Run 'git fetch' on all repositories under development directory")
    print("")
    print("gbt pull")
    print(" - Run 'git pull --recurse-submodules' on all repositories under development directory")
    print("")
    print("gbt fetch status")
    print(" - Run 'git fetch' on all repositories under development directory, and show status")
    print("")
    print("gbt pull status")
    print(" - Run 'git pull' on all repositories under development directory, and show status")
    print("")
    print("gbt checkout <branch_name>")
    print(" - Run 'git checkout <branch_name>' on all repositories under development directory")
    print("")
    print("gbt log [<days_to_log>]")
    print(" - Run 'git log' on all repositories under development directory, and display <days_to_log> worth of commits (default 7)")
    print("")


# Start program

args = sys.argv[1:]

fetch = "fetch" in args
log = "log" in args
pull = "pull" in args
status = "status" in args
checkout = "checkout" in args
help = "help" in args or "--help" in args

branch_name = None
days_to_log = 7

if help:
    show_help()
    exit(0)

if pull and fetch:
    print("fetch and pull are incompatible")
    exit(1)

if checkout and (pull or fetch or status or log):
    print("checkout is not compatible with other commands")
    exit(1)

if log and (pull or fetch or status or checkout):
    print("log is not compatible with other commands")
    exit(1)

# Check that there's a branch param for checkout

if checkout:
    if len(args) == 2:
        branch_name = args[1]
    else:
        print("checkout requires a branch name")
        exit(1)

# Get the optional days to log param

if log:
    if len(args) == 2:
        days_to_log = int(args[1])

# Set the defaults

if (fetch or pull or status or checkout or log) is False:
    fetch = True
    status = True

# Upgrade any old config file

upgrade_existing_config()

# Get the configured development directory, or ask for it

development_dir = get_development_dir()
#  print("Working on [ " + development_dir + " ]")

# Do the work

git_workers = create_workers()

if checkout:
    checkout_all(git_workers, branch_name)

elif log:
    log_all(git_workers, days_to_log)
    print_logs(git_workers)

else:
    if pull:
        pull_all(git_workers)

    elif fetch:
        fetch_all(git_workers)

    if status:
        status_all(git_workers)
        work_to_do, gbt_has_update = print_statuses(git_workers)

        if work_to_do is False:
            print(TerminalStyle.GREEN + "Everything up to date" + TerminalStyle.CLEAR)

        if gbt_has_update is True:
            print(TerminalStyle.GREEN + "Update available for gbt" + TerminalStyle.CLEAR)
