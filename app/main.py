import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8099, debug=False, use_reloader=False)
