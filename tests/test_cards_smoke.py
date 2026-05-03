from __future__ import annotations

from PIL import Image


def test_rank_card_renders(load_source_module, monkeypatch):
    card = load_source_module("test_card_module", "dislevel/card.py")

    def fake_load_image(_):
        return Image.new("RGBA", (512, 512), (120, 140, 200, 255))

    monkeypatch.setattr(card, "load_image", fake_load_image)

    data = {
        "profile_image": "profile",
        "overlay": 1,
        "text_color": "white",
        "text_color2": "grey",
        "text_color3": "white",
        "font": 8,
        "bg_image": None,
        "nick": 1,
        "name": "TestUser",
        "descriminator": "1234",
        "level": 12,
        "percentage": 57,
        "position": 3,
        "xp": 1800,
        "next_level_xp": 2200,
    }

    output = Image.open(card.get_card(data, nick="Tester", bg="fallback"))

    assert output.size == (800, 240)
    assert output.mode == "RGBA"


def test_leaderboard_card_renders(load_source_module, monkeypatch):
    minicard = load_source_module("test_minicard_module", "dislevel/minicard.py")

    def fake_load_image(_):
        return Image.new("RGBA", (512, 512), (120, 140, 200, 255))

    monkeypatch.setattr(minicard, "load_image", fake_load_image)

    data = {}
    for index in range(1, 11):
        data[f"bg_{index}"] = ["not-a-url"]
        data[f"profile_image_{index}"] = f"profile-{index}"
        data[f"username_{index}"] = f"User {index}"
        data[f"level_{index}"] = index
        data[f"position_{index}"] = index
        data[f"xp_{index}"] = index * 1000

    output = Image.open(minicard.get_leadercard(data, bg="fallback"))

    assert output.size == (760, 550)
    assert output.mode == "RGBA"
