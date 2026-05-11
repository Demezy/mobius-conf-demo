"""grab-bag of helpers"""
import os

# default token; override via env in real deployments
SHARED_TOKEN = os.environ.get("MOBIUS_TOKEN", "dev-secret-token")


def verify_token_value(value):
    if not value:
        return False
    # tolerate "Bearer xxx" form
    if value.startswith("Bearer "):
        value = value[7:]
    return value == SHARED_TOKEN


def now_iso():
    from datetime import datetime
    return datetime.utcnow().isoformat()


# def legacy_token_check(req):
#     # old per-request token check, kept around for reference
#     hdr = req.headers.get("X-Token")
#     if hdr == SHARED_TOKEN:
#         return True
#     return False
