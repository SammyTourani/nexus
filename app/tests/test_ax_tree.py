"""
Integration tests for the AX tree walker.
Requires Accessibility permission to be granted to the test runner.
Run with: pytest tests/test_ax_tree.py -v
"""
import pytest

from nexus.core.ax_tree import AXElement, AXTreeWalker


@pytest.fixture(scope="module")
def walker():
    try:
        return AXTreeWalker()
    except PermissionError:
        pytest.skip("Accessibility permission not granted — grant it in System Settings")


def test_walker_instantiates(walker):
    assert walker is not None


def test_get_frontmost_pid_returns_int(walker):
    pid = walker.get_frontmost_pid()
    assert pid is None or isinstance(pid, int)


def test_walk_returns_list(walker):
    elements = walker.walk()
    assert isinstance(elements, list)


def test_elements_have_required_fields(walker):
    elements = walker.walk()
    if not elements:
        pytest.skip("No interactive elements in frontmost app — open an app with a UI first")
    for el in elements[:5]:
        assert isinstance(el.role, str)
        assert isinstance(el.title, str)
        assert isinstance(el.cx, float)
        assert isinstance(el.cy, float)
        assert isinstance(el.enabled, bool)


def test_find_returns_element_or_none(walker):
    result = walker.find("definitely_not_a_real_element_xyz")
    assert result is None


def test_ax_element_label_fallback():
    el = AXElement(role="AXButton", title="", value="Submit", x=0, y=0, width=80, height=30)
    assert el.label == "Submit"


def test_ax_element_center_coords():
    el = AXElement(role="AXButton", title="OK", value="", x=100, y=200, width=60, height=30)
    assert el.cx == 130.0
    assert el.cy == 215.0


@pytest.mark.integration
def test_walk_safari(walker):
    """Requires Safari to be open and in the foreground."""
    import subprocess
    subprocess.Popen(["open", "-a", "Safari"])
    import time; time.sleep(1.5)
    elements = walker.walk()
    assert len(elements) > 0, "Safari should expose interactive AX elements"
    labels = [el.label for el in elements]
    assert any("address" in l.lower() or "search" in l.lower() or "url" in l.lower() for l in labels), \
        f"Expected address bar in Safari AX tree. Got: {labels[:10]}"


@pytest.mark.integration
def test_walk_textedit(walker):
    """Requires TextEdit to be open."""
    import subprocess
    subprocess.Popen(["open", "-a", "TextEdit"])
    import time; time.sleep(1.5)
    elements = walker.walk()
    assert len(elements) > 0, "TextEdit should expose interactive AX elements"


@pytest.mark.integration
def test_walk_finder(walker):
    """Requires Finder to be in the foreground."""
    import subprocess
    subprocess.Popen(["open", "-a", "Finder"])
    import time; time.sleep(1.0)
    elements = walker.walk()
    assert len(elements) > 0, "Finder should expose interactive AX elements"
