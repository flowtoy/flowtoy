"""Test secret redaction in logging."""

import logging
from io import StringIO

from flowtoy.providers.process import ProcessProvider


def test_default_redaction_hides_args():
    """By default, only command name and arg count are logged."""
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger("flowtoy.providers.process")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    cfg = {
        "command": ["curl", "-H", "Authorization: Bearer SECRET_TOKEN"],
    }

    provider = ProcessProvider(cfg)

    # Just test the sanitization method
    cmd_list = ["curl", "-H", "Authorization: Bearer SECRET_TOKEN"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    assert sanitized == ["curl", "<2 args>"]
    assert "SECRET_TOKEN" not in str(sanitized)


def test_redact_by_index():
    """Test redacting specific argument indices."""
    cfg = {
        "command": ["curl", "-H", "Authorization: Bearer SECRET"],
        "redact_args": [2],  # Redact 3rd argument
    }

    provider = ProcessProvider(cfg)
    cmd_list = ["curl", "-H", "Authorization: Bearer SECRET"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    assert sanitized == ["curl", "-H", "[REDACTED]"]
    assert "SECRET" not in str(sanitized)


def test_redact_by_pattern():
    """Test redacting arguments containing specific patterns."""
    cfg = {
        "command": ["curl", "-H", "Authorization: Bearer SECRET"],
        "redact_patterns": ["Authorization:", "Bearer"],
    }

    provider = ProcessProvider(cfg)
    cmd_list = ["curl", "-H", "Authorization: Bearer SECRET"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    assert sanitized == ["curl", "-H", "[REDACTED]"]
    assert "SECRET" not in str(sanitized)


def test_redact_multiple_args():
    """Test redacting multiple arguments."""
    cfg = {
        "command": ["script", "--user", "admin", "--password", "secret123"],
        "redact_args": [2, 4],  # Redact 'admin' and 'secret123'
    }

    provider = ProcessProvider(cfg)
    cmd_list = ["script", "--user", "admin", "--password", "secret123"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    assert sanitized == ["script", "--user", "[REDACTED]", "--password", "[REDACTED]"]
    assert "admin" not in str(sanitized)
    assert "secret123" not in str(sanitized)


def test_redact_patterns_case_sensitive():
    """Test that pattern matching is case-sensitive."""
    cfg = {
        "command": ["curl", "-H", "authorization: secret"],
        "redact_patterns": ["Authorization:"],  # Capital A
    }

    provider = ProcessProvider(cfg)
    cmd_list = ["curl", "-H", "authorization: secret"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    # Pattern doesn't match (case sensitive), so arg is NOT redacted
    assert sanitized == ["curl", "-H", "authorization: secret"]


def test_log_full_command_option():
    """Test that log_full_command=True bypasses redaction."""
    cfg = {
        "command": ["curl", "-H", "Authorization: Bearer SECRET"],
        "log_full_command": True,
        "redact_args": [2],  # This should be ignored
    }

    provider = ProcessProvider(cfg)
    cmd_list = ["curl", "-H", "Authorization: Bearer SECRET"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    # With log_full_command=True, everything is logged
    assert sanitized == cmd_list
    assert "SECRET" in str(sanitized)


def test_combining_indices_and_patterns():
    """Test using both redact_args and redact_patterns together."""
    cfg = {
        "command": [
            "tool",
            "--key",
            "KEY123",
            "--token",
            "TOKEN456",
            "--other",
            "safe",
        ],
        "redact_args": [2],  # Redact index 2 (KEY123)
        "redact_patterns": ["TOKEN"],  # Redact anything with TOKEN
    }

    provider = ProcessProvider(cfg)
    cmd_list = ["tool", "--key", "KEY123", "--token", "TOKEN456", "--other", "safe"]
    sanitized = provider._sanitize_for_logging(cmd_list, cfg)

    assert sanitized == [
        "tool",
        "--key",
        "[REDACTED]",
        "--token",
        "[REDACTED]",
        "--other",
        "safe",
    ]
    assert "KEY123" not in str(sanitized)
    assert "TOKEN456" not in str(sanitized)
    assert "safe" in str(sanitized)


def test_empty_command():
    """Test handling of empty command list."""
    cfg = {"command": []}

    provider = ProcessProvider(cfg)
    sanitized = provider._sanitize_for_logging([], cfg)

    assert sanitized == []
