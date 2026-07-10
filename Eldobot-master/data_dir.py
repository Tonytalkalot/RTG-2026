import os
import shutil

# Use /app/data on Railway (set DATA_DIR env var), otherwise current directory
DATA_DIR = os.environ.get("DATA_DIR", ".")

os.makedirs(os.path.join(DATA_DIR, "exports"), exist_ok=True)

# On first deploy, seed persistent volume with repo copies
for fname in ['servers.json', 'serversb.json', 'tracking.json']:
    dest = os.path.join(DATA_DIR, fname)
    if not os.path.exists(dest) and os.path.exists(fname):
        shutil.copy2(fname, dest)
        print(f'Seeded {dest} from repo')

def data_path(filename):
    """Return the full path for a data file."""
    return os.path.join(DATA_DIR, filename)
