import os

conffiles = [
    'MasterMarketplace/config/common/01-marketplace.py',
    'MasterMarketplace/config/common/02-base.py',
    'MasterMarketplace/config/common/03-security.py',

    'MasterMarketplace/config/development/01-auth.py',
    'MasterMarketplace/config/development/02-database.py',
    'MasterMarketplace/config/development/03-email.py',
    'MasterMarketplace/config/development/05-logging.py',
    'MasterMarketplace/config/development/10-overrides.py',
]

DEBUG = True
HOSTNAME = 'localhost'

for f in conffiles:
    fo = open(os.path.abspath(f))
    exec(fo.read())
    fo.close()
