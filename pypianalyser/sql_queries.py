CREATE_PACKAGE_TABLE_SQL = \
    """
    CREATE TABLE IF NOT EXISTS packages (
    id integer PRIMARY KEY,
    docs_url text,
    name text NOT NULL UNIQUE,
    maintainer text,
    requires_python text,
    maintainer_email text,
    keywords text,
    package_url text,
    author text,
    author_email text,
    download_url text,
    project_urls text,
    platform text,
    version text,
    description text,
    release_url text,
    description_content_type text,
    requires_dist text,
    project_url text,
    bugtrack_url text,
    license text,
    summary text,
    home_page text);
    """
PACKAGE_TABLE_COLUMNS = \
    ["id", "docs_url", "name", "maintainer", "requires_python", "maintainer_email", "keywords", "package_url", "author",
     "author_email", "download_url", "project_urls", "platform", "version", "description", "release_url",
     "description_content_type", "requires_dist", "project_url", "bugtrack_url", "license", "summary", "home_page"]

CREATE_CLASSIFIER_STRING_TABLE_SQL = \
    """
    CREATE TABLE IF NOT EXISTS classifier_strings (
    id integer PRIMARY KEY,
    name text NOT NULL UNIQUE);
    """
CLASSIFIER_STRING_TABLE_COLUMNS = ["id", "name"]

CREATE_PACKAGE_CLASSIFIERS_TABLE_SQL = \
    """
    CREATE TABLE IF NOT EXISTS package_classifiers (
    id integer PRIMARY KEY,
    package_id integer NOT NULL,
    classifier_id integer NOT NULL,
    FOREIGN KEY(package_id) REFERENCES packages(id) ON DELETE CASCADE,
    FOREIGN KEY(classifier_id) REFERENCES classifier_strings(id));
    """
PACKAGE_CLASSIFIERS_TABLE_COLUMNS = ["id", "package_id", "classifier_id"]

CREATE_RELEASE_TABLE_SQL = \
    """
    CREATE TABLE IF NOT EXISTS package_releases (
    id integer PRIMARY KEY,
    package_id integer NOT NULL,
    version text,
    has_sig BOOL,
    upload_time text,
    comment_text text,
    python_version text,
    url text,
    md5_digest text,
    requires_python text,
    filename text,
    packagetype text,
    upload_time_iso_8601 text,
    size integer,
    FOREIGN KEY(package_id) REFERENCES packages(id) ON DELETE CASCADE);
    """
PACKAGE_RELEASES_TABLE_COLUMNS = \
    ["id", "package_id", "version", "has_sig", "upload_time", "comment_text", "python_version",
     "url", "md5_digest", "requires_python", "filename", "packagetype", "upload_time_iso_8601", "size"]

CREATE_TABLE_SQL_QUERIES = [CREATE_PACKAGE_TABLE_SQL,
                            CREATE_CLASSIFIER_STRING_TABLE_SQL,
                            CREATE_PACKAGE_CLASSIFIERS_TABLE_SQL,
                            CREATE_RELEASE_TABLE_SQL]

INSERT_PACKAGE_SQL = \
    """
    INSERT OR IGNORE INTO packages(
    author,
    author_email,
    bugtrack_url,
    description,
    description_content_type,
    docs_url,
    download_url,
    home_page,
    keywords,
    license,
    maintainer,
    maintainer_email,
    name,
    package_url,
    platform,
    project_url,
    project_urls,
    release_url,
    requires_dist,
    requires_python,
    summary,
    version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

INSERT_CLASSIFIER_STRING_SQL = "INSERT OR IGNORE INTO classifier_strings(name) VALUES (?)"

INSERT_PACKAGE_CLASSIFIER_SQL = "INSERT OR IGNORE INTO package_classifiers(classifier_id, package_id) VALUES (?, ?)"

INSERT_PACKAGE_RELEASES_SQL = \
    """ 
    INSERT OR IGNORE INTO package_releases(
    comment_text,
    filename,
    has_sig,
    md5_digest,
    package_id,
    packagetype,
    python_version,
    requires_python,
    size,
    upload_time,
    upload_time_iso_8601,
    url,
    version) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

SELECT_ID_FOR_CLASSIFIER_STRING_SQL = \
    """
    SELECT id from classifier_strings 
    WHERE name=?
    """

SELECT_CLASSIFIERS_FOR_PACKAGE_SQL = \
    """
    SELECT classifier_strings.name FROM classifier_strings 
    INNER JOIN package_classifiers ON classifier_strings.id = package_classifiers.classifier_id 
    INNER JOIN packages ON packages.id = package_classifiers.package_id 
    WHERE packages.name=?
    """

SELECT_RELEASE_FILES_FOR_PACKAGE_SQL = \
    """
    SELECT package_releases.* FROM package_releases 
    INNER JOIN packages ON packages.id = package_releases.package_id 
    WHERE packages.name = ?
    """

SELECT_PACKAGE_BY_NAME_SQL = \
    """
    SELECT * FROM packages
    WHERE name = ?
    """


SELECT_PACKAGES_WITH_PY3_CLASSIFIER = \
    """
    SELECT DISTINCT packages.name FROM packages 
    INNER JOIN package_classifiers 
        ON packages.id = package_classifiers.package_id 
    INNER JOIN classifier_strings 
        ON classifier_strings.id = package_classifiers.classifier_id
    WHERE
        classifier_strings.name LIKE "Programming Language :: Python :: 3%"
    """