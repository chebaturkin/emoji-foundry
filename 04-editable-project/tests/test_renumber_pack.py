from pathlib import Path


def test_renumber_mapping_is_a_complete_unique_pack_with_ira_last():
    from renumber_pack import OLD_TO_NEW

    assert len(OLD_TO_NEW) == 27
    assert len(set(OLD_TO_NEW)) == 27
    assert len(set(OLD_TO_NEW.values())) == 27
    assert [int(stem[:2]) for stem in OLD_TO_NEW.values()] == list(range(1, 28))
    assert list(OLD_TO_NEW.values())[-1] == "27-ira-heart"


def test_two_phase_moves_handle_number_collisions_and_rewrite_references(tmp_path: Path):
    from renumber_pack import OLD_TO_NEW, apply_moves, build_moves, rewrite_text_references

    (tmp_path / "AGENTS.md").write_text("fixture")
    assets = tmp_path / "assets"
    modules = tmp_path / "04-editable-project" / "frame_motions"
    assets.mkdir()
    modules.mkdir(parents=True)
    for old in OLD_TO_NEW:
        (assets / f"{old}.tgs").write_text(old)
        number, slug = old.split("-", 1)
        (modules / f"m{number}_{slug.replace('-', '_')}.py").write_text(
            f'STEM = "{old}"\n'
        )

    moves = build_moves(tmp_path)
    assert len({destination for _, destination in moves}) == len(moves)
    apply_moves(moves)
    rewrite_text_references(tmp_path)

    for new in OLD_TO_NEW.values():
        assert (assets / f"{new}.tgs").exists()
        number, slug = new.split("-", 1)
        module = modules / f"m{number}_{slug.replace('-', '_')}.py"
        assert module.exists()
        assert f'"{new}"' in module.read_text()
    assert not any(path.name.startswith(".renumber-stage-") for path in tmp_path.rglob("*"))
