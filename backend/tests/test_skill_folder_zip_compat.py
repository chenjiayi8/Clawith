from pathlib import Path


def test_build_skill_folder_zip_source_marks_filenames_as_utf8():
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "frontend" / "src" / "utils" / "skillFolderZip.ts").read_text()

    assert "const ZIP_UTF8_FLAG = 0x0800;" in source
    assert "localHeader.setUint16(6, ZIP_UTF8_FLAG, true);" in source
    assert "centralHeader.setUint16(8, ZIP_UTF8_FLAG, true);" in source
