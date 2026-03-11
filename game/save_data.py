from __future__ import annotations

import json

from game import settings


DEFAULT_SAVE = {
    "coins": 0,
    "best_score": 0,
    "selected_skin": "classic",
    "selected_skins": ["classic", "classic"],
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
    selected_skins = data.get("selected_skins", [data["selected_skin"], "classic"])
    normalized_selected_skins: list[str] = []
    fallback_cycle = [skin["id"] for skin in settings.SKINS]
    unlocked_skin_ids = set(unlocked_skins)
    for index in range(2):
        skin_id = selected_skins[index] if index < len(selected_skins) else fallback_cycle[min(index, len(fallback_cycle) - 1)]
        if skin_id not in available_skin_ids or skin_id not in unlocked_skin_ids:
            skin_id = "classic"
        normalized_selected_skins.append(skin_id)
    data["selected_skins"] = normalized_selected_skins

    return data


def save_save(data: dict[str, object]) -> None:
    settings.SAVE_FILE.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
