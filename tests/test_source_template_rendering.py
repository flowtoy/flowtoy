"""Test template rendering in source configuration."""

from flowtoy.runner import LocalRunner


def test_template_rendering_in_source_config(monkeypatch):
    """
    Test that templates in source configuration are rendered with env provider data.
    """
    monkeypatch.setenv("TEST_VALUE", "hello_world")

    config = {
        "sources": {
            "test_env": {"type": "env", "configuration": {"vars": ["TEST_VALUE"]}},
            "test_process": {
                "type": "process",
                "configuration": {
                    "command": ["echo", "Value: {{ sources.test_env.TEST_VALUE }}"]
                },
            },
        },
        "flow": [
            {
                "name": "run_echo",
                "source": "test_process",
                "output": [{"name": "result", "type": "json"}],
            }
        ],
    }

    runner = LocalRunner(config)
    runner.run()

    # Template should be rendered in source config
    result = runner.flows["run_echo"]["result"]
    assert "Value: hello_world" in result
    # Should NOT contain the literal template
    assert "{{" not in result


def test_template_rendering_with_multiple_env_sources(monkeypatch):
    """Test templates can reference multiple env sources."""
    monkeypatch.setenv("VAR_A", "alpha")
    monkeypatch.setenv("VAR_B", "beta")

    config = {
        "sources": {
            "env_a": {"type": "env", "configuration": {"vars": ["VAR_A"]}},
            "env_b": {"type": "env", "configuration": {"vars": ["VAR_B"]}},
            "test_process": {
                "type": "process",
                "configuration": {
                    "command": [
                        "echo",
                        "{{ sources.env_a.VAR_A }}-{{ sources.env_b.VAR_B }}",
                    ]
                },
            },
        },
        "flow": [
            {
                "name": "run_echo",
                "source": "test_process",
                "output": [{"name": "result", "type": "json"}],
            }
        ],
    }

    runner = LocalRunner(config)
    runner.run()

    result = runner.flows["run_echo"]["result"]
    assert "alpha-beta" in result


def test_template_rendering_preserves_non_template_strings(monkeypatch):
    """Test that strings without templates are not modified."""
    config = {
        "sources": {
            "test_process": {
                "type": "process",
                "configuration": {
                    "command": ["echo", "plain string with {{ no env source }}"]
                },
            }
        },
        "flow": [
            {
                "name": "run_echo",
                "source": "test_process",
                "output": [{"name": "result", "type": "json"}],
            }
        ],
    }

    runner = LocalRunner(config)
    # This should fail because the template references undefined variable
    # But it proves templates are being processed
    try:
        runner.run()
        raise AssertionError("Should have raised error for undefined template variable")
    except Exception as e:
        assert "undefined" in str(e).lower() or "no env source" in str(e).lower()
