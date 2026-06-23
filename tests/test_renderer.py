from notes_app.renderer import render_markdown


def test_heading_1():
    assert "<h1>Hello</h1>" in render_markdown("# Hello")


def test_heading_2():
    assert "<h2>World</h2>" in render_markdown("## World")


def test_heading_3():
    assert "<h3>Sub</h3>" in render_markdown("### Sub")


def test_bold():
    assert "<strong>bold</strong>" in render_markdown("**bold**")


def test_italic():
    assert "<em>italic</em>" in render_markdown("*italic*")


def test_inline_code():
    assert "<code>x = 1</code>" in render_markdown("`x = 1`")


def test_link():
    result = render_markdown("[click](https://example.com)")
    assert '<a href="https://example.com">click</a>' in result


def test_unordered_list():
    result = render_markdown("- item one\n- item two")
    assert "<ul>" in result
    assert "<li>item one</li>" in result
    assert "<li>item two</li>" in result
    assert "</ul>" in result


def test_code_block():
    result = render_markdown("```python\nprint('hi')\n```")
    assert "<pre><code" in result
    assert "print(&#x27;hi&#x27;)" in result or "print('hi')" in result
    assert "</code></pre>" in result


def test_paragraph():
    assert "<p>Hello world</p>" in render_markdown("Hello world")


def test_html_escaping_in_code_block():
    result = render_markdown("```\n<script>alert(1)</script>\n```")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result
