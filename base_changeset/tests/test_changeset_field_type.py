# Copyright 2015-2017 Camptocamp SA
# Copyright 2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase

from .base_changeset_tester import BaseChangesetTester, BaseChangesetTester2
from .common import ChangesetTestCommon, setup_test_model, teardown_test_model


class TestChangesetFieldType(ChangesetTestCommon, TransactionCase):
    """ Check that changeset changes are stored expectingly to their types """

    def _setup_rules(self):
        ChangesetFieldRule = self.env["changeset.field.rule"]
        ChangesetFieldRule.search([]).unlink()
        fields = (
            ("char", "test_field_char"),
            ("text", "test_field_txt"),
            ("boolean", "test_field_bool"),
            ("date", "test_field_date"),
            ("integer", "test_field_int"),
            ("float", "test_field_float"),
            ("selection", "test_field_sel"),
            ("many2one", "test_field_m2o"),
            ("many2many", "test_field_m2m"),
            ("one2many", "test_field_o2m"),
            ("binary", "test_field_binary"),
        )
        for field_type, field in fields:
            attr_name = "field_%s" % field_type
            field_record = self.env["ir.model.fields"].search(
                [("model", "=", "base.changeset.tester"), ("name", "=", field)]
            )
            self.assertTrue(field_record, "Field %s not available" % field)
            # set attribute such as 'self.field_char' is a
            # ir.model.fields record of the field res_partner.ref
            setattr(self, attr_name, field_record)
            ChangesetFieldRule.create(
                {"field_id": field_record.id, "action": "validate"}
            )

    def setUp(self):
        super().setUp()
        setup_test_model(self.env, [BaseChangesetTester, BaseChangesetTester2])

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
        self._setup_rules()
        self.test2_record = self.env["base.changeset.tester2"].create({"name": "Test2"})
        self.test_record = self.env["base.changeset.tester"].create()

    def tearDown(self):
        teardown_test_model(self.env, [BaseChangesetTester, BaseChangesetTester2])
        super().tearDown()

    def test_new_changeset_char(self):
        """ Add a new changeset on a Char field """
        self.test_record.write({self.field_char.name: "New value"})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_char,
                    self.test_record[self.field_char.name],
                    "New value",
                    "draft",
                )
            ],
        )

    def test_new_changeset_text(self):
        """ Add a new changeset on a Text field """
        self.test_record.write({self.field_text.name: "New comment\non 2 lines"})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_text,
                    self.test_record[self.field_text.name],
                    "New comment\non 2 lines",
                    "draft",
                )
            ],
        )

    def test_new_changeset_boolean(self):
        """ Add a new changeset on a Boolean field """
        # ensure the changeset has to change the value
        self.test_record.with_context(__no_changeset=True).write(
            {self.field_boolean.name: False}
        )

        self.test_record.write({self.field_boolean.name: True})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_boolean,
                    self.test_record[self.field_boolean.name],
                    True,
                    "draft",
                )
            ],
        )

    def test_new_changeset_date(self):
        """ Add a new changeset on a Date field """
        self.test_record.write({self.field_date.name: "2015-09-15"})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_date,
                    self.test_record[self.field_date.name],
                    fields.Date.from_string("2015-09-15"),
                    "draft",
                )
            ],
        )

    def test_new_changeset_integer(self):
        """ Add a new changeset on a Integer field """
        self.test_record.write({self.field_integer.name: 42})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_integer,
                    self.test_record[self.field_integer.name],
                    42,
                    "draft",
                )
            ],
        )

    def test_new_changeset_float(self):
        """ Add a new changeset on a Float field """
        self.test_record.write({self.field_float.name: 3.1415})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_float,
                    self.test_record[self.field_float.name],
                    3.1415,
                    "draft",
                )
            ],
        )

    def test_new_changeset_selection(self):
        """ Add a new changeset on a Selection field """
        self.test_record.write({self.field_selection.name: "two"})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_selection,
                    self.test_record[self.field_selection.name],
                    "two",
                    "draft",
                )
            ],
        )

    def test_new_changeset_many2one(self):
        """ Add a new changeset on a Many2one field """
        self.test_record.write({self.field_many2one.name: self.test2_record.id})
        self.assert_changeset(
            self.test_record,
            self.env.user,
            [
                (
                    self.field_many2one,
                    self.test_record[self.field_many2one.name],
                    self.env.ref("base.ch"),
                    "draft",
                )
            ],
        )

    def test_new_changeset_many2many(self):
        """ Add a new changeset on a Many2many field is not supported """
        with self.assertRaises(NotImplementedError):
            self.test_record.write({self.field_many2many.name: [self.test2_record.id]})

    def test_new_changeset_one2many(self):
        """ Add a new changeset on a One2many field is not supported """
        with self.assertRaises(NotImplementedError):
            self.test_record.write({self.field_one2many.name: [self.test2_record.id]})

    def test_new_changeset_binary(self):
        """ Add a new changeset on a Binary field is not supported """
        with self.assertRaises(NotImplementedError):
            self.test_record.write({self.field_binary.name: "xyz"})

    def test_apply_char(self):
        """ Apply a change on a Char field """
        changes = [(self.field_char, "New Ref", "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertEqual(self.test_record[self.field_char.name], "New Ref")

    def test_apply_text(self):
        """ Apply a change on a Text field """
        changes = [(self.field_text, "New comment\non 2 lines", "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertEqual(
            self.test_record[self.field_text.name], "New comment\non 2 lines"
        )

    def test_apply_boolean(self):
        """ Apply a change on a Boolean field """
        # ensure the changeset has to change the value
        self.test_record.write({self.field_boolean.name: False})

        changes = [(self.field_boolean, True, "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertEqual(self.test_record[self.field_boolean.name], True)

        # Cannot do this while it is on the same transaction. The cache may not
        # be updated
        # changes = [(self.field_boolean, False, 'draft')]
        # changeset = self._create_changeset(self.test_record, changes)
        # changeset.change_ids.apply()
        # self.assertEqual(self.test_record[self.field_boolean.name], False)

    def test_apply_date(self):
        """ Apply a change on a Date field """
        changes = [(self.field_date, "2015-09-15", "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertAlmostEqual(
            self.test_record[self.field_date.name],
            fields.Date.from_string("2015-09-15"),
        )

    def test_apply_integer(self):
        """ Apply a change on a Integer field """
        changes = [(self.field_integer, 42, "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertAlmostEqual(self.test_record[self.field_integer.name], 42)

    def test_apply_float(self):
        """ Apply a change on a Float field """
        changes = [(self.field_float, 52.47, "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertAlmostEqual(self.test_record[self.field_float.name], 52.47)

    def test_apply_selection(self):
        """ Apply a change on a Selection field """
        changes = [(self.field_selection, "two", "draft")]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertAlmostEqual(self.test_record[self.field_selection.name], "two")

    def test_apply_many2one(self):
        """ Apply a change on a Many2one field """
        changes = [
            (
                self.field_many2one,
                "base.changeset.tester2,%d" % self.test2_record.id,
                "draft",
            )
        ]
        changeset = self._create_changeset(self.test_record, changes)
        changeset.change_ids.apply()
        self.assertEqual(
            self.test_record[self.field_many2one.name], self.test2_record.id
        )

    def test_apply_many2many(self):
        """ Apply a change on a Many2many field is not supported """
        changes = [(self.field_many2many, self.test2_record.id.id, "draft")]
        with self.assertRaises(NotImplementedError):
            self._create_changeset(self.test_record, changes)

    def test_apply_one2many(self):
        """ Apply a change on a One2many field is not supported """
        changes = [(self.field_one2many, [self.test2_record.id.id], "draft",)]
        with self.assertRaises(NotImplementedError):
            self._create_changeset(self.test_record, changes)

    def test_apply_binary(self):
        """ Apply a change on a Binary field is not supported """
        changes = [(self.field_one2many, "", "draft")]
        with self.assertRaises(NotImplementedError):
            self._create_changeset(self.test_record, changes)
