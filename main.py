import configparser
import os
import re
import sys
import urllib.request as request
import zipfile


def main():
    if not os.path.isfile('config.ini'):
        print('Error: File "config.ini" cannot be found.', file=sys.stderr)
        return

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read('config.ini')

    database = configparser.ConfigParser()
    database.optionxform = str

    if os.path.isfile(config['wow-addon-manager']['Database']):
        database.read(config['wow-addon-manager']['Database'])

    for addon in config.sections():
        if addon in ['wow-addon-manager', 'Example']:
            continue

        print('[' + addon + '] ', end='', flush=True)

        if 'URL' not in config[addon]:
            print('Invalid configuration.')
            continue

        version, link = get_addon_info(config[addon]['URL'])

        if version is None or link is None:
            print('Not found.')
            continue

        if addon not in database:
            database[addon] = {
                'Version': '',
                'Files': '',
            }

        if config[addon].get('IgnoreVersion', 'no') != 'yes' and database[addon]['Version'] == version:
            print('Already up-to-date.')
            continue

        filename, _ = request.urlretrieve(link)

        for file in reversed(database[addon]['Files'].split('\n')[1:]):
            path = os.path.join(config['wow-addon-manager']['WoWAddonPath'], file)

            if os.path.isdir(path):
                os.rmdir(path)
            elif os.path.isfile(path):
                os.remove(path)

        with zipfile.ZipFile(filename, 'r') as file:
            file.extractall(config['wow-addon-manager']['WoWAddonPath'])
            database[addon]['Version'] = version
            database[addon]['Files'] = '\n' + '\n'.join(file.namelist())

        print('Installed version ' + version + '.')

    with open(config['wow-addon-manager']['Database'], 'w') as file:
        database.write(file)


def get_addon_info(url):
    version, link = None, None

    if not re.match(r'^https?://', url):
        url = 'https://' + url

    # WoWInterface.
    if re.search(r'wowinterface.com/downloads/info', url):
        with request.urlopen(url) as response:
            html = str(response.read())
            version = find(html, '<div id="version">Version: ', '</div>')

        with request.urlopen(url.replace('info', 'download')) as response:
            html = str(response.read())
            link = find(html, r'Problems with the download\? <a href="', '"')

    # CurseForge.
    elif re.search(r'curseforge.com/wow/addons/[^/]*$', url):
        with request.urlopen(url + '/files') as response:
            html = str(response.read())
            version = find(html, '<span class="table__content file__name full">', '</span>')
            link = 'https://www.curseforge.com' + find(html, '<a class="button button--download download-button mg-r-05" href="', '"') + '/file'

    # CurseForge.
    elif re.search(r'wow.curseforge.com/projects/[^/]*$', url):
        with request.urlopen(url + '/files?sort=releasetype') as response:
            html = str(response.read())
            version = find(html, r'<a class="overflow-tip twitch-link".*?data-name="', '"')
            link = 'https://wow.curseforge.com' + find(html, '<a class="button tip fa-icon-download icon-only" href="', '"')

    # Curse.
    elif re.search(r'mods.curse.com/addons/wow/[^/]*$', url):
        url = url.replace('mods.curse.com/addons/wow', 'curseforge.com/wow/addons')
        version, link = get_addon_info(url)

    # Tukui and ElvUI.
    elif re.search(r'https://www.tukui.org/download.php\?ui=', url):
        with request.urlopen(url) as response:
            html = str(response.read())
            version = find(html, '<b class="Premium">', '</b>')
            link = 'https://www.tukui.org' + find(html, r'id="download".*?<div class="mb-10">.*?<a href="', '"')

    return version, link


def find(string, left, right):
    match = re.search(left + '(.*?)' + right, string)

    if match is None:
        return

    match = match.group(1).strip()
    return match if match else None


if __name__ == '__main__':
    main()
