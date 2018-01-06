#!/usr/bin/env python3
"""A simple addon manager for World of Warcraft."""

from configparser import ConfigParser
import os
import re
from urllib.parse import urljoin
from urllib.request import urlopen, urlretrieve
import zipfile


def main():
    """Install or update all addons."""
    if not os.path.isfile('config.ini'):
        print('Error: The configuration file cannot be found.')
        return 1

    config = ConfigParser()
    # Enable case sensitivity.
    config.optionxform = str
    config.read('config.ini')

    database = ConfigParser()
    database.optionxform = str

    if os.path.isfile('database.ini'):
        database.read('database.ini')

    addon_folder = config['Settings']['WoWAddonFolder']
    tracked_files = []

    for addon in config.sections():
        if addon in ['Settings', 'Example']:
            continue

        print('[' + addon + '] ', end='', flush=True)

        if 'URL' not in config[addon]:
            print('No URL specified.')
            continue

        url = config[addon]['URL']
        ignore_version = config[addon].get('IgnoreVersion')

        version, link = get_addon_info(url)

        if version is None or link is None:
            print('The addon cannot be found.')
            continue

        if addon not in database:
            database[addon] = {
                'Version': '',
                'Files': '',
            }

        installed_version = database[addon]['Version']
        files = database[addon]['Files'].split('\n')[1:]
        missing_files = False

        for file in files:
            if not os.path.exists(os.path.join(addon_folder, file)):
                missing_files = True
                break

        if ignore_version != 'yes' and installed_version == version and not missing_files:
            tracked_files.extend(files)
            print('Already up-to-date.')
            continue

        try:
            filename, _ = urlretrieve(link)

            with zipfile.ZipFile(filename, 'r') as file:
                file.extractall(addon_folder)
                files = file.namelist()
                tracked_files.extend(files)

                database[addon]['Version'] = version
                database[addon]['Files'] = '\n' + '\n'.join(files)

            print('Installed version ' + version + '.')
        except zipfile.BadZipFile:
            if re.search('wowinterface.com', url):
                print('The latest version is currently awaiting approval.')
            else:
                print('The file cannot be found.')

        with open('database.ini', 'w') as file:
            database.write(file)

    cleanup(config, database, tracked_files)


def get_addon_info(url):
    """Find the version information and download link from the addon page."""
    version, link = None, None

    # Force HTTPS.
    url = 'https://' + re.sub(r'^https?://', '', url)

    # WoWInterface.
    if re.search('wowinterface.com/downloads/info', url):
        with urlopen(url) as response:
            html = str(response.read())
            version = find(html, '<div id="version">Version: ', '</div>')

        with urlopen(url.replace('info', 'download')) as response:
            html = str(response.read())
            link = find(html, r'Problems with the download\? <a href="', '"')

    # CurseForge.
    elif re.search(r'curseforge.com/wow/addons/[^/]*$', url):
        with urlopen(url + '/files') as response:
            html = str(response.read())
            version = find(html, '<span class="table__content file__name full">', '</span>')
            link = find(html, 'class="button button--download download-button mg-r-05" href="', '"')
            link = urljoin(response.geturl(), link + '/file')

    # CurseForge and WowAce.
    elif re.search(r'(wow.curseforge|wowace).com/projects/[^/]*$', url):
        with urlopen(url + '/files?sort=releasetype') as response:
            html = str(response.read())
            version = find(html, r'<a class="overflow-tip twitch-link".*?data-name="', '"')
            link = find(html, '<a class="button tip fa-icon-download icon-only" href="', '"')
            link = urljoin(response.geturl(), link)

    # Curse.
    elif re.search(r'mods.curse.com/addons/wow/[^/]*$', url):
        url = url.replace('mods.curse.com/addons/wow', 'curseforge.com/wow/addons')
        version, link = get_addon_info(url)

    # Tukui and ElvUI.
    elif re.search(r'tukui.org/download.php\?ui=', url):
        with urlopen(url) as response:
            html = str(response.read())
            version = find(html, r'id="version">.*?<b class="Premium">', '</b>')
            link = find(html, r'id="download".*?<div class="mb-10">.*?<a href="', '"')
            link = urljoin(response.geturl(), link)

    # Tukui and ElvUI addons.
    elif re.search(r'tukui.org/addons.php\?id=', url):
        with urlopen(url) as response:
            html = str(response.read())
            version = find(html, r'id="extras">.*?<b class="VIP">', '</b>')
            link = urljoin(response.geturl(), url.replace('id', 'download'))

    return version, link


def find(string, left, right):
    """Return text between two strings. Supports regular expressions."""
    match = re.search(left + '(.*?)' + right, string)

    if match is None:
        return

    # The text must not be empty.
    match = match.group(1).strip()
    return match if match else None


def cleanup(config, database, tracked_files):
    """Remove missing addons and untracked files."""
    for addon in database.sections():
        if addon not in config.sections():
            database.remove_section(addon)

    with open('database.ini', 'w') as file:
        database.write(file)

    addon_folder = config['Settings']['WoWAddonFolder']
    tracked_files = [os.path.join(addon_folder, file) for file in tracked_files]

    for root, folders, files in os.walk(addon_folder, topdown=False):
        for name in files:
            file = os.path.join(root, name)
            if file not in tracked_files:
                os.remove(file)

        for name in folders:
            folder = os.path.join(root, name) + '/'
            # Try to remove empty folders that cannot be tracked.
            if folder not in tracked_files:
                try:
                    os.rmdir(folder)
                except OSError:
                    pass


if __name__ == '__main__':
    main()
