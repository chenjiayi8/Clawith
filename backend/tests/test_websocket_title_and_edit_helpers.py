import uuid

from app.api.websocket import _rewrite_edited_user_content, _should_generate_session_title


def test_should_generate_session_title_only_for_first_real_turn():
    assert _should_generate_session_title(True, False, False) is True
    assert _should_generate_session_title(False, False, False) is False
    assert _should_generate_session_title(True, True, False) is False
    assert _should_generate_session_title(True, False, True) is False


def test_rewrite_edited_user_content_preserves_file_and_image_wrappers():
    original = "[file:cat.png]\n[image_data:data:image/png;base64,abc123]\nOriginal prompt"
    rewritten = _rewrite_edited_user_content(original, "New prompt")
    assert rewritten == "[file:cat.png]\n[image_data:data:image/png;base64,abc123]\nNew prompt"


def test_rewrite_edited_user_content_preserves_attachment_banner_lines():
    original = "[file:notes.txt]\n[Attachment: notes.txt]\nOriginal question"
    rewritten = _rewrite_edited_user_content(original, "Updated question")
    assert rewritten == "[file:notes.txt]\n[Attachment: notes.txt]\nUpdated question"
