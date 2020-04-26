import json
from lxml import html
import requests
import six.moves.urllib as urllib
from pypianalyser.exceptions import Exception404
from pypianalyser.utils import normalize_package_name


HTTP_SUCCESS = 200
HTTP_NOT_FOUND = 404
UNSET_VAL = -1


def get_metadata_for_package(package_name, url_format='https://pypi.org/pypi/{}/json'):
    """
    Downloads the metadata JSON for given package

    :param package_name: Name of the package
    :type package_name: str
    :param url_format: Format URL string
    :type url_format: str

    :return: Package metadata
    :rtype: dict
    """
    url = url_format.format(package_name)

    response = requests.get(url)
    if response.status_code == HTTP_NOT_FOUND:
        raise Exception404(url)
    elif response.status_code != HTTP_SUCCESS:
        raise Exception('HTTP Error: {} on {}'.format(str(response.status_code), url))

    return json.loads(response.content)


def get_package_list(domain='https://pypi.org/'):
    """
    Download the list of packages from a given mirror from the /simple index

    :param domain: Domain to download from, e.g. https://pypi.org/
    :type domain: str

    :return: List of package name strings
    :rtype: str
    """
    url = urllib.parse.urljoin(domain, 'simple')
    response = requests.get(url)
    tree = html.fromstring(response.content)
    packages = tree.xpath('//body/a')
    package_names = [normalize_package_name(x.text) for x in packages]
    return package_names
