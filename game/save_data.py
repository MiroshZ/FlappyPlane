from __future__ import annotations

import json

from game import settings


DEFAULT_SAVE = {
    "coins": 0,
    "best_score": 0,
    "selected_skin": "classic",
    "unlocked_skins": ["classic"],
}


def load_save() -> dict[str, object]:
    if not settings.SAVE_FILE.exists():
        return DEFAULT_SAVE.copy()

    try:
        raw_data = json.loads(settings.SAVE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_SAVE.copy()

    data = DEFAULT_SAVE.copy()
    data.update(raw_data)

    unlocked_skins = [skin["id"] for skin in settings.SKINS if skin["id"] in set(data.get("unlocked_skins", []))]
    if "classic" not in unlocked_skins:
        unlocked_skins.insert(0, "classic")
    data["unlocked_skins"] = unlocked_skins

    available_skin_ids = {skin["id"] for skin in settings.SKINS}
    if data.get("selected_skin") not in available_skin_ids:
        data["selected_skin"] = "classic"

    return data


def save_save(data: dict[str, object]) -> None:
    settings.SAVE_FILE.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
