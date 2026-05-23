#!/usr/bin/env python3
"""CanLand — Canadian Land Use Feasibility Platform.

Convenience launcher. For production we use gunicorn (see Procfile);
this script is meant for local development.
"""

import os

from app import app


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
