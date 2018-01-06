"""A simple addon manager for World of Warcraft."""

from configparser import ConfigParser
import os
import re
from urllib.parse import urljoin
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile


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

    if os.path.isfile(config['Settings']['Database']):
        database.read(config['Settings']['Database'])

    for addon in config.sections():
        if addon in ['Settings', 'Example']:
            continue

        print('[' + addon + '] ', end='', flush=True)

        if 'URL' not in config[addon]:
            print('No URL specified.')
            continue

        version, link = get_addon_info(config[addon]['URL'])

        if version is None or link is None:
            print('The addon cannot be found.')
            continue

        if addon not in database:
            database[addon] = {
                'Version': '',
                'Files': '',
            }

        if config[addon].get('IgnoreVersion') != 'yes' and database[addon]['Version'] == version:
            print('Already up-to-date.')
            continue

        filename, _ = urlretrieve(link)

        # Remove existing files and folders.
        for file in reversed(database[addon]['Files'].strip().split('\n')):
            path = os.path.join(config['Settings']['WoWAddonPath'], file)

            if os.path.isdir(path):
                os.rmdir(path)
            elif os.path.isfile(path):
                os.remove(path)

        with ZipFile(filename, 'r') as file:
            file.extractall(config['Settings']['WoWAddonPath'])
            database[addon]['Version'] = version
            database[addon]['Files'] = '\n' + '\n'.join(file.namelist())

        print('Installed version ' + version + '.')

    with open(config['Settings']['Database'], 'w') as file:
        database.write(file)


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

    # CurseForge projects.
    elif re.search(r'wow.curseforge.com/projects/[^/]*$', url):
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


if __name__ == '__main__':
    main()
