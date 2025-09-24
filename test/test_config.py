import unittest

from autopr.config import PR_TEMPLATE_SCHEMA, PrTemplate


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


if __name__ == "__main__":
    unittest.main()
