# PyMySQL adapter for Django MySQL support on Windows/Cross-platform
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
