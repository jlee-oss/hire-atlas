import pathlib
import sys

# Vercel에서 프로젝트 루트와 scripts/ 디렉토리를 sys.path에 추가
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
for p in (str(SCRIPTS_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from server import AppHandler  # noqa: E402


class handler(AppHandler):
    """Vercel 서버리스 핸들러 — 정적 파일은 Vercel CDN이 처리, /api/* 만 여기서 처리."""
    pass
