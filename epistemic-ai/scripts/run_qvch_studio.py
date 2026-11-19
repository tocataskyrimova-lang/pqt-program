from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.qvch_studio.server import create_server  # noqa: E402


def main() -> None:
    server = create_server(host="127.0.0.1", port=8765)
    print("QVCH_v3 Studio: http://127.0.0.1:8765")
    print("LM Studio endpoint: http://100.75.52.51:1234/v1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nQVCH_v3 Studio stopped")
    finally:
        server.service.close()  # type: ignore[attr-defined]
        server.server_close()


if __name__ == "__main__":
    main()
