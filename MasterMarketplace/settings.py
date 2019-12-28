import os

conffiles = [
    'MasterMarketplace/config/common/01-marketplace.py',
    'MasterMarketplace/config/common/02-base.py',
    'MasterMarketplace/config/common/03-security.py',

    'MasterMarketplace/config/production/01-auth.py',
    'MasterMarketplace/config/production/02-database.py',
    'MasterMarketplace/config/production/03-email.py',
    'MasterMarketplace/config/production/05-logging.py',
]

DEBUG = False
HOSTNAME = 'master.ele.tue.nl'

for f in conffiles:
    fo = open(os.path.abspath(f))
    exec(fo.read())
    fo.close()

# in case of overrides
DEBUG = False