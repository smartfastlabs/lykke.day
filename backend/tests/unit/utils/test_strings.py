"""Unit tests for strings utility functions."""

import pytest

from planned.infrastructure.utils.strings import slugify


def test_slugify_basic():
    """Test basic slugify functionality."""
    result = slugify("Hello World")
    assert result == "hello-world"


def test_slugify_with_special_chars():
    """Test slugify with special characters."""
    result = slugify("Hello World! How's it going?")
    assert result == "hello-world-hows-it-going"


def test_slugify_with_unicode():
    """Test slugify with unicode characters."""
    result = slugify("Café résumé")
    assert result == "cafe-resume"


def test_slugify_with_underscores():
    """Test slugify converts underscores to hyphens."""
    result = slugify("hello_world_test")
    assert result == "hello-world-test"


def test_slugify_with_multiple_spaces():
    """Test slugify handles multiple spaces."""
    result = slugify("hello    world")
    assert result == "hello-world"


def test_slugify_with_consecutive_hyphens():
    """Test slugify removes consecutive hyphens."""
    result = slugify("hello---world")
    assert result == "hello-world"


def test_slugify_strips_leading_trailing_hyphens():
    """Test slugify strips leading and trailing hyphens."""
    result = slugify("-hello-world-")
    assert result == "hello-world"


def test_slugify_empty_string():
    """Test slugify with empty string."""
    result = slugify("")
    assert result == ""


def test_slugify_numbers():
    """Test slugify preserves numbers."""
    result = slugify("Version 2.0 Release")
    assert result == "version-20-release"

