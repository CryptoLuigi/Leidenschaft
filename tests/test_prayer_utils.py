def test_get_prayer_cooldown_remaining(load_source_module, stubbed_dislevel_imports):
    utils = load_source_module("test_prayer_utils", "dislevel/utils.py")

    assert utils.get_prayer_cooldown_remaining(1_000, now=1_000) == 86_400
    assert utils.get_prayer_cooldown_remaining(1_000, now=1_000 + 86_400) == 0
    assert utils.get_prayer_cooldown_remaining(1_000, now=1_000 + 90_000) == 0
