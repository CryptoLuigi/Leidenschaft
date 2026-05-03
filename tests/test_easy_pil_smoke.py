from __future__ import annotations

from PIL import Image

from easy_pil import Canvas, Editor, Font, Text


def test_editor_smoke_operations():
    canvas = Canvas((200, 120), color=(10, 20, 30, 255))
    editor = Editor(canvas)

    assert editor.image.mode == "RGBA"

    editor.resize((100, 60))
    assert editor.image.size == (100, 60)

    editor = Editor(Image.new("RGBA", (240, 120), (255, 0, 0, 255)))
    editor.resize((80, 80), crop=True)
    assert editor.image.size == (80, 80)

    editor.rounded_corners(radius=8).circle_image().rotate(15).blur("box", 1).blur(
        "gussian", 1
    )
    assert editor.image.mode == "RGBA"


def test_text_and_image_roundtrip():
    font = Font.poppins(size=18)
    editor = Editor(Image.new("RGBA", (300, 100), (255, 255, 255, 255)))
    texts = [Text("One", font, "red"), Text("Two", font, "blue")]

    editor.text((10, 10), "Hello", font=font, color="black", align="left")
    editor.multi_text((150, 50), texts, align="center")
    editor.rectangle((5, 5), 50, 20, fill="green", radius=4)
    editor.bar((10, 70), 200, 12, percentage=50, fill="gray", stroke_width=2)

    output = Image.open(editor.image_bytes)

    assert output.size == editor.image.size
    assert output.mode == "RGBA"
