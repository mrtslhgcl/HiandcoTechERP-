from utils.session import Session


def has_permission(permission_key: str) -> bool:
    session = Session()
    if not session.is_logged_in:
        return False

    if session.is_admin():
        return True

    return permission_key in session.permissions


def require_permission(permission_key: str) -> dict:
    if has_permission(permission_key):
        return {"allowed": True}
    return {
        "allowed": False,
        "message": "Bu işlem için yetkiniz bulunmamaktadır."
    }


def get_user_permissions() -> list[str]:
    session = Session()
    return session.permissions


def is_admin() -> bool:
    session = Session()
    return session.is_admin()