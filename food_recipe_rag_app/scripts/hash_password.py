import getpass
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auth import make_password_hash

password = getpass.getpass("Password: ")
print("\nAUTH_PASSWORD_HASH=")
print(make_password_hash(password))
