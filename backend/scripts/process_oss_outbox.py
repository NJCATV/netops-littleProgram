import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app  # noqa: E402
from app.services.oss_work_order_service import dispatch_oss_outbox  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        results = dispatch_oss_outbox(limit=20)
        print({"processed": len(results), "success": sum(item["status"] == "success" for item in results)})


if __name__ == "__main__":
    main()
