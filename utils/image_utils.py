import base64
import os
import shutil


def get_base_dir() -> str:
    return os.environ.get(
        'HIANDCO_BASE_DIR',
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def get_app_dir() -> str:
    return os.environ.get('HIANDCO_APP_DIR', get_base_dir())


def get_image_cache_dir() -> str:
    return os.path.join(get_app_dir(), "image_cache")


def image_to_base64(file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def base64_to_file(base64_str: str, dest_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(base64.b64decode(base64_str))
        return True
    except Exception:
        return False


def save_entity_image(source_path: str, entity_type: str, entity_id: int) -> tuple[str, str | None]:
    ext = os.path.splitext(source_path)[1].lower()

    if entity_type == "products":
        import time
        filename = f"product_{entity_id}_{int(time.time() * 1000)}{ext}"
    else:
        singular = entity_type.rstrip("s")
        filename = f"{singular}_{entity_id}{ext}"

    relative_path = f"{entity_type}/{filename}"
    cache_dir = get_image_cache_dir()
    dest = os.path.join(cache_dir, relative_path)

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(source_path, dest)

    base64_data = image_to_base64(dest)
    return relative_path, base64_data


def resolve_image_path(relative_path: str, image_data: str = None) -> str | None:
    if not relative_path:
        return None

    cache_dir = get_image_cache_dir()
    abs_path = os.path.join(cache_dir, relative_path)

    if os.path.exists(abs_path):
        return abs_path

    if image_data:
        if base64_to_file(image_data, abs_path):
            return abs_path

    if os.path.isabs(relative_path) and os.path.exists(relative_path):
        return relative_path

    return None
