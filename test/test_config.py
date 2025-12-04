import os
import unittest

from autopr.config import (
    CREDENTIALS_SCHEMA,
    PR_TEMPLATE_SCHEMA,
    Credentials,
    PrTemplate,
    expand_env_vars,
)


class TestPrTemplate(unittest.TestCase):
    def test_pr_template_default_draft_false(self):
        """Test that PrTemplate defaults draft to False"""
        template = PrTemplate()
        self.assertFalse(template.draft)

    def test_pr_template_explicit_draft_true(self):
        """Test that PrTemplate can be created with draft=True"""
        template = PrTemplate(draft=True)
        self.assertTrue(template.draft)

    def test_pr_template_explicit_draft_false(self):
        """Test that PrTemplate can be explicitly set to draft=False"""
        template = PrTemplate(draft=False)
        self.assertFalse(template.draft)

    def test_pr_template_schema_serialization_default(self):
        """Test that PR_TEMPLATE_SCHEMA correctly serializes default template"""
        template = PrTemplate()
        data = PR_TEMPLATE_SCHEMA.dump(template)

        self.assertIn("draft", data)
        self.assertFalse(data["draft"])

        # Check other default values are present
        self.assertEqual(data["title"], "Automatically generated PR")
        self.assertEqual(data["message"], "Automatically generated commit")
        self.assertEqual(data["branch"], "autopr")
        self.assertEqual(data["body"], "This is an automatically generated PR")

    def test_pr_template_schema_serialization_draft_true(self):
        """Test that PR_TEMPLATE_SCHEMA correctly serializes template with draft=True"""
        template = PrTemplate(draft=True)
        data = PR_TEMPLATE_SCHEMA.dump(template)

        self.assertIn("draft", data)
        self.assertTrue(data["draft"])

    def test_pr_template_schema_deserialization_draft_false(self):
        """Test that PR_TEMPLATE_SCHEMA correctly deserializes draft=False"""
        data = {
            "title": "Test PR",
            "message": "Test message",
            "branch": "test-branch",
            "body": "Test body",
            "draft": False,
        }

        template = PR_TEMPLATE_SCHEMA.load(data)

        self.assertEqual(template.title, "Test PR")
        self.assertEqual(template.message, "Test message")
        self.assertEqual(template.branch, "test-branch")
        self.assertEqual(template.body, "Test body")
        self.assertFalse(template.draft)

    def test_pr_template_schema_deserialization_draft_true(self):
        """Test that PR_TEMPLATE_SCHEMA correctly deserializes draft=True"""
        data = {
            "title": "Test PR",
            "message": "Test message",
            "branch": "test-branch",
            "body": "Test body",
            "draft": True,
        }

        template = PR_TEMPLATE_SCHEMA.load(data)

        self.assertEqual(template.title, "Test PR")
        self.assertEqual(template.message, "Test message")
        self.assertEqual(template.branch, "test-branch")
        self.assertEqual(template.body, "Test body")
        self.assertTrue(template.draft)

    def test_pr_template_schema_deserialization_missing_draft(self):
        """Test that PR_TEMPLATE_SCHEMA handles missing draft field gracefully"""
        data = {
            "title": "Test PR",
            "message": "Test message",
            "branch": "test-branch",
            "body": "Test body"
            # Intentionally omitting draft field
        }

        template = PR_TEMPLATE_SCHEMA.load(data)

        self.assertEqual(template.title, "Test PR")
        self.assertEqual(template.message, "Test message")
        self.assertEqual(template.branch, "test-branch")
        self.assertEqual(template.body, "Test body")
        self.assertFalse(template.draft)  # Should default to False

    def test_pr_template_schema_roundtrip_draft_false(self):
        """Test serialize -> deserialize roundtrip with draft=False"""
        original = PrTemplate(
            title="Test PR",
            message="Test message",
            branch="test-branch",
            body="Test body",
            draft=False,
        )

        # Serialize
        data = PR_TEMPLATE_SCHEMA.dump(original)

        # Deserialize
        restored = PR_TEMPLATE_SCHEMA.load(data)

        # Verify all fields match
        self.assertEqual(original.title, restored.title)
        self.assertEqual(original.message, restored.message)
        self.assertEqual(original.branch, restored.branch)
        self.assertEqual(original.body, restored.body)
        self.assertEqual(original.draft, restored.draft)
        self.assertFalse(restored.draft)

    def test_pr_template_schema_roundtrip_draft_true(self):
        """Test serialize -> deserialize roundtrip with draft=True"""
        original = PrTemplate(
            title="Draft PR",
            message="Draft message",
            branch="draft-branch",
            body="Draft body",
            draft=True,
        )

        # Serialize
        data = PR_TEMPLATE_SCHEMA.dump(original)

        # Deserialize
        restored = PR_TEMPLATE_SCHEMA.load(data)

        # Verify all fields match
        self.assertEqual(original.title, restored.title)
        self.assertEqual(original.message, restored.message)
        self.assertEqual(original.branch, restored.branch)
        self.assertEqual(original.body, restored.body)
        self.assertEqual(original.draft, restored.draft)
        self.assertTrue(restored.draft)


class TestExpandEnvVars(unittest.TestCase):
    def test_expand_single_env_var(self):
        """Test expansion of a single environment variable"""
        os.environ["TEST_VAR"] = "test_value"
        result = expand_env_vars("${TEST_VAR}")
        self.assertEqual(result, "test_value")
        del os.environ["TEST_VAR"]

    def test_expand_env_var_in_string(self):
        """Test expansion of environment variable within a string"""
        os.environ["TEST_VAR"] = "test_value"
        result = expand_env_vars("prefix_${TEST_VAR}_suffix")
        self.assertEqual(result, "prefix_test_value_suffix")
        del os.environ["TEST_VAR"]

    def test_expand_multiple_env_vars(self):
        """Test expansion of multiple environment variables"""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        result = expand_env_vars("${VAR1}/${VAR2}")
        self.assertEqual(result, "value1/value2")
        del os.environ["VAR1"]
        del os.environ["VAR2"]

    def test_expand_missing_env_var_raises_error(self):
        """Test that missing environment variable raises ValueError"""
        with self.assertRaises(ValueError) as context:
            expand_env_vars("${NONEXISTENT_VAR}")
        self.assertIn("NONEXISTENT_VAR", str(context.exception))
        self.assertIn("not set", str(context.exception))

    def test_expand_no_env_var(self):
        """Test that strings without env vars are returned unchanged"""
        result = expand_env_vars("plain_string")
        self.assertEqual(result, "plain_string")

    def test_expand_empty_string(self):
        """Test expansion of empty string"""
        result = expand_env_vars("")
        self.assertEqual(result, "")


class TestCredentialsSchema(unittest.TestCase):
    def test_credentials_with_env_vars(self):
        """Test that credentials correctly expand environment variables"""
        os.environ["GITHUB_API_KEY"] = "test_api_key_123"
        os.environ["SSH_KEY_PATH"] = "/home/user/.ssh/id_rsa"

        data = {
            "api_key": "${GITHUB_API_KEY}",
            "ssh_key_file": "${SSH_KEY_PATH}",
        }

        credentials = CREDENTIALS_SCHEMA.load(data)

        self.assertEqual(credentials.api_key, "test_api_key_123")
        self.assertEqual(credentials.ssh_key_file, "/home/user/.ssh/id_rsa")

        del os.environ["GITHUB_API_KEY"]
        del os.environ["SSH_KEY_PATH"]

    def test_credentials_with_partial_env_vars(self):
        """Test credentials with env vars embedded in strings"""
        os.environ["HOME"] = "/home/testuser"
        os.environ["API_KEY"] = "secret123"

        data = {
            "api_key": "prefix_${API_KEY}_suffix",
            "ssh_key_file": "${HOME}/.ssh/id_rsa",
        }

        credentials = CREDENTIALS_SCHEMA.load(data)

        self.assertEqual(credentials.api_key, "prefix_secret123_suffix")
        self.assertEqual(credentials.ssh_key_file, "/home/testuser/.ssh/id_rsa")

        del os.environ["HOME"]
        del os.environ["API_KEY"]

    def test_credentials_without_env_vars(self):
        """Test that plain strings work without env var syntax"""
        data = {
            "api_key": "plain_api_key",
            "ssh_key_file": "/plain/path/to/key",
        }

        credentials = CREDENTIALS_SCHEMA.load(data)

        self.assertEqual(credentials.api_key, "plain_api_key")
        self.assertEqual(credentials.ssh_key_file, "/plain/path/to/key")

    def test_credentials_with_missing_env_var_raises_error(self):
        """Test that missing environment variable raises error during deserialization"""
        data = {
            "api_key": "${MISSING_API_KEY}",
            "ssh_key_file": "/path/to/key",
        }

        with self.assertRaises(ValueError) as context:
            CREDENTIALS_SCHEMA.load(data)
        self.assertIn("MISSING_API_KEY", str(context.exception))
        self.assertIn("not set", str(context.exception))

    def test_credentials_roundtrip_with_env_vars(self):
        """Test that credentials can be serialized and deserialized"""
        os.environ["TEST_API_KEY"] = "api_key_value"
        os.environ["TEST_SSH_KEY"] = "/test/ssh/key"

        # Create credentials from env vars
        data = {
            "api_key": "${TEST_API_KEY}",
            "ssh_key_file": "${TEST_SSH_KEY}",
        }
        credentials = CREDENTIALS_SCHEMA.load(data)

        # Values should be expanded
        self.assertEqual(credentials.api_key, "api_key_value")
        self.assertEqual(credentials.ssh_key_file, "/test/ssh/key")

        # Serialize back (note: serialization will contain the expanded values, not the env var syntax)
        serialized = CREDENTIALS_SCHEMA.dump(credentials)
        self.assertEqual(serialized["api_key"], "api_key_value")
        self.assertEqual(serialized["ssh_key_file"], "/test/ssh/key")

        del os.environ["TEST_API_KEY"]
        del os.environ["TEST_SSH_KEY"]


if __name__ == "__main__":
    unittest.main()
