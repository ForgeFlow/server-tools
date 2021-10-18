# Copyright 2015-2017 Camptocamp SA
# Copyright 2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common

from .base_changeset_tester import BaseChangesetTester
from .common import setup_test_model, teardown_test_model


class TestChangesetFieldRule(common.TransactionCase):
    def setUp(self):
        super().setUp()

        setup_test_model(self.env, [BaseChangesetTester])

        self.tester_model = self.env["ir.model"].search(
            [("model", "=", BaseChangesetTester._name)]
        )

        # Access record:
        self.env["ir.model.access"].create(
            {
                "name": "access.tester",
                "model_id": self.tester_model.id,
                "perm_read": 1,
                "perm_write": 1,
                "perm_create": 1,
                "perm_unlink": 1,
            }
        )

        # Get fields
        self.field_char = self.env.ref(
            "base_changeset.field_base_changeset_tester__test_field_char"
        )
        self.field_text = self.env.ref(
            "base_changeset.field_base_changeset_tester__test_field_txt"
        )

    def tearDown(self):
        teardown_test_model(self.env, [BaseChangesetTester])
        super().tearDown()

    def test_get_rules(self):
        ChangesetFieldRule = self.env["changeset.field.rule"]
        ChangesetFieldRule.search([]).unlink()
        rule1 = ChangesetFieldRule.create(
            {"field_id": self.field_char.id, "action": "validate"}
        )
        rule2 = ChangesetFieldRule.create(
            {"field_id": self.field_txt.id, "action": "never"}
        )
        get_rules = ChangesetFieldRule.get_rules(None, "base.changeset.tester")
        self.assertEqual(get_rules, {"name": rule1, "street": rule2})

    def test_get_rules_source(self):
        ChangesetFieldRule = self.env["changeset.field.rule"]
        ChangesetFieldRule.search([]).unlink()
        rule1 = ChangesetFieldRule.create(
            {"field_id": self.field_char.id, "action": "validate"}
        )
        rule2 = ChangesetFieldRule.create(
            {"field_id": self.field_txt.id, "action": "never"}
        )
        rule3 = ChangesetFieldRule.create(
            {
                "source_model_id": self.company_model_id,
                "field_id": self.field_txt.id,
                "action": "never",
            }
        )
        model = ChangesetFieldRule
        rules = model.get_rules(None, "base.changeset.tester")
        self.assertEqual(rules, {"name": rule1, "street": rule2})
        rules = model.get_rules("res.company", "base.changeset.tester")
        self.assertEqual(rules, {"name": rule1, "street": rule3})

    def test_get_rules_cache(self):
        ChangesetFieldRule = self.env["changeset.field.rule"]
        ChangesetFieldRule.search([]).unlink()
        rule = ChangesetFieldRule.create(
            {"field_id": self.field_char.id, "action": "validate"}
        )
        self.assertEqual(
            ChangesetFieldRule.get_rules(None, "base.changeset.tester")["name"].action,
            "validate",
        )
        # Write on cursor to bypass the cache invalidation for the
        # matter of the test
        self.env.cr.execute(
            "UPDATE changeset_field_rule " "SET action = 'never' " "WHERE id = %s",
            (rule.id,),
        )
        self.assertEqual(
            ChangesetFieldRule.get_rules(None, "base.changeset.tester")["name"].action,
            "validate",
        )
        rule.action = "auto"
        self.assertEqual(
            ChangesetFieldRule.get_rules(None, "base.changeset.tester")["name"].action,
            "auto",
        )
        rule.unlink()
        self.assertFalse(ChangesetFieldRule.get_rules(None, "base.changeset.tester"))
