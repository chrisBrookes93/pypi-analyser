import requests
from lxml import html
import urlparse
import json
import logging
from distutils.version import LooseVersion
from collections import OrderedDict
from PyPi_Py3_Analyser.exceptions import Exception404

logger = logging.getLogger(__file__)

DOMAIN = 'https://pypi.org'
HTTP_SUCCESS = 200
HTTP_NOT_FOUND = 404
UNSET_VAL = -1


def get_json_blob_for_package(package_name, url_format='https://pypi.org/pypi/{}/json'):
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
    logger.debug('Executing GET on {}'.format(url))

    response = requests.get(url)
    if response.status_code == HTTP_NOT_FOUND:
        raise Exception404(url)
    elif response.status_code != HTTP_SUCCESS:
        raise Exception('HTTP Error: {} on {}'.format(str(response.status_code), url))

    return json.loads(response.content)


def get_package_metadata(package_name, url_format='https://pypi.org/pypi/{}/json', truncate_description=None,
                         truncate_releases=None):
    """
    Download the metadata for a given package and optionally description and the releases dictionary. The description is
    often the largest part of the metadata and can be truncated to save space. This limit is also applied to the
    Summary field.  Similarly you may not care about old releases, so you have the option to truncate the list and only
     return the X most recent

    :param package_name: Name of the package
    :type package_name: str
    :param url_format: URL format to download from e.g. https://pypi.org/pypi/{}/json
    :type url_format: str
    :param truncate_description: How many characters to truncate the description to.
    :type truncate_description: int
    :param truncate_releases: How many releases to truncate to
    :type truncate_releases: int

    :return: Package metadata
    :rtype: dict
    """
    metadata_dict = get_json_blob_for_package(package_name, url_format)
    if truncate_description is not None:
        description = metadata_dict['info']['description']
        if description:
            metadata_dict['info']['description'] = description[:truncate_description]

        summary = metadata_dict['info']['summary']
        if summary:
            metadata_dict['info']['summary'] = summary[:truncate_description]

    if truncate_releases is not None:
        releases = metadata_dict['releases'] or {}
        # In Py3 by default, we can't rely on the order of the release dictionary
        ordered_releases_names = sorted(metadata_dict['releases'].keys(), key=LooseVersion, reverse=True)[:truncate_releases]
        ordered_releases = OrderedDict()
        for release_name in ordered_releases_names:
            ordered_releases[release_name] = releases[release_name]
        metadata_dict['releases'] = ordered_releases

    return metadata_dict


def get_package_list(domain='https://pypi.org/'):
    """
    Download the list of packages from a given mirror from the /simple index

    :param domain: Domain to download from, e.g. https://pypi.org/
    :type domain: str

    :return: List of package name strings
    :rtype: str
    """
    url = urlparse.urljoin(domain, 'simple')
    response = requests.get(url)
    tree = html.fromstring(response.content)
    packages = tree.xpath('//body/a')
    # x.text.lower().replace('-', '_')
    package_names = [x.text.lower().replace('-', '_') for x in packages]
    logger.debug('Found {} packages from the index {}'.format(len(package_names), url))
    return package_names






# def build_cache():
#     cache = {}
#     package_list = get_packaged_list()
#     i = 0
#     successes = 0
#     for package in package_list:
#         try:
#             i = i + 1
#             print('Processing {}, package {} of {}'.format(package, i, len(package_list)))
#             meta_data = get_json_blob_for_package(package)
#             cache[package] = meta_data
#             successes = successes + 1
#         except Exception, e:
#             print(e)
#
#     with open('pypi_cache.json', 'w') as fp:
#         json.dump(cache, fp, indent=4)
#
#     print('Successfully processed {} of {}'.format(successes, len(package_list)))





