from __future__ import annotations

import pytest


def test_get_percentage_derives_progress(load_source_module, stubbed_dislevel_imports):
    utils = load_source_module("test_dislevel_utils", "dislevel/utils.py")

    data = {"xp": 7070, "level": 12}
    result = utils.get_percentage(data)

    assert result["next_level_xp"] == 1420
    assert pytest.approx(result["percentage"], rel=1e-6) == 2.816901408450704


@pytest.mark.asyncio
async def test_prepare_db_creates_expected_tables(
    load_source_module, stubbed_dislevel_imports, monkeypatch
):
    utils = load_source_module("test_dislevel_utils_db", "dislevel/utils.py")
    models = stubbed_dislevel_imports["models"]
    monkeypatch.setenv("DISLEVEL_TABLE", "dislevel_data")

    class FakeDatabase:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)

    database = FakeDatabase()
    extra_fields = [models.Field(name="bio", type="TEXT")]

    await utils.prepare_db(database, extra_fields)

    assert len(database.statements) == 2
    assert "CREATE TABLE IF NOT EXISTS dislevel_data(" in database.statements[0]
    assert "member_id BIGINT NOT NULL" in database.statements[0]
    assert "bio TEXT" in database.statements[0]
    assert "CREATE TABLE IF NOT EXISTS server_settings(" in database.statements[1]
