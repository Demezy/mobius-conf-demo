from datetime import datetime


def humanize(dt):
    if not dt:
        return ""
    delta = datetime.utcnow() - dt
    s = int(delta.total_seconds())
    if s < 60:
        return f"{s}s ago"
    if s < 3600:
        return f"{s // 60}m ago"
    return f"{s // 3600}h ago"
