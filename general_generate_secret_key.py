import os
import binascii
import os.path

if os.path.isfile("MasterMarketplace/secret.py"):
    print("secret file already exists!")
else:
    key = binascii.hexlify(os.urandom(24)).decode()
    with open("MasterMarketplace/secret.py", "w") as stream:
        stream.write("SECRET_KEY_IMPORT = '{}'\nDATABASE_PASSWORD_IMPORT = 'banaan'\n"
                     "SHEN_RING_CLIENT_ID=\"\"\nSHEN_RING_CLIENT_SECRET=\"\"\n".format(key))
    print("secret file generated")

