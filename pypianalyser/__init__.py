import argparse
import logging
from io import open
from pypianalyser.pypi_metadata_retriever import PyPiMetadataRetriever

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__file__)


def main():
    parser = argparse.ArgumentParser('Script to download PyPi metadata into an SQLite database for easy querying.')
    parser.add_argument('-td', '--trunc_descriptions',
                        help='Truncate the description field to X characters to reduce the size of the database. Use '
                             '-1 for no truncation. Default is 500',
                        type=int,
                        default=500)
    parser.add_argument('-tr', '--trunc_releases',
                        help='Specify the maximum number of releases to store in the database for each package. In many'
                             ' cases you may only be interested in the latest one or two releases. Use -1 for no '
                             'truncation. Default is 2',
                        type=int,
                        default=2)
    parser.add_argument('-t', '--threads',
                        help='Number of threads to spawn to download the metadata. Default is 5',
                        type=int,
                        default=5)
    parser.add_argument('-db', '--database_path',
                        help='Name or path of the database to store the metadata in. If the database already exists '
                             'with entries then it will be read and only packages that are missing from the database '
                             'will be retrieved. This allows you to download the PyPi mirror metadata over a few runs '
                             'rather than a single one. Default is pypi_metadata.sqlite',
                        default='pypi_metadata.sqlite')
    parser.add_argument('-m', '--max_packages',
                        help='Maximum number of packages to retrieve the metadata for. Using this allows you download'
                             ' the metadata over a series of runs rather than spamming PyPi and your network.',
                        type=int)
    parser.add_argument('-pr', '--package_regex',
                        help='Specify a regex to match package names against. Only those that match will be retrieved. '
                             'NOTE: all package names are normalized before this, whereby characters a lowercased and '
                             'underscores are replaced with hyphens. E.g. ^robotframework-.*')
    parser.add_argument('-404', '--file_404_list',
                        help='Path to a file to store a list of package names that returned a HTTP 404. This usually'
                             ' means that the package no longer exists in PyPi. The file is useful for doing future '
                             'runs. Default: 404.txt',
                        default='404.txt')
    parser.add_argument('--dry_run', action='store_true',
                        help='Dry run mode that gives insight into the package metadata that will be retrieved. This '
                             'mode obtains the package list from the index, removes any packages that are already '
                             'present the database (if it exists). If the list of package URLs that returned 404 on '
                             'previous runs exists, these will also be removed from the set. Finally the regex will be '
                             'applied to the remaining packages. If this list is less than 100 then its printed to the'
                             ' console. The entire list will be written out to a file called dry_run_package_list.txt')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose mode.')
        
    parsed_args = parser.parse_args()
    retriever = PyPiMetadataRetriever(parsed_args.trunc_descriptions,
                                      parsed_args.trunc_releases,
                                      parsed_args.threads,
                                      parsed_args.database_path,
                                      parsed_args.max_packages,
                                      parsed_args.package_regex,
                                      parsed_args.file_404_list,
                                      parsed_args.verbose)

    if parsed_args.dry_run:
        package_list = retriever.calculate_package_list()
        with open('dry_run_package_list.txt', 'w', encoding='utf-8') as fp:
            fp.write(u'\n'.join(package_list))

        logger.info('Dry run has calculated {} packages that would be processed. This list has been output to '
                    'dry_run_package_list.txt'.format(len(package_list)))
    else:
        retriever.run()


if __name__ == '__main__':
    main()
