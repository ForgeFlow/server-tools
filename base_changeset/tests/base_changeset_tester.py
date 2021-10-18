# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BaseChangesetTester(models.Model):
    _name = "base.changeset.tester"
    _description = "Base Changeset Tester"
    _inherit = ["base.changeset"]

    test_field_char = fields.Char()
    test_field_txt = fields.Text()
    test_field_bool = fields.Boolean()
    test_field_date = fields.Date()
    test_field_int = fields.Integer()
    test_field_float = fields.Float()
    test_field_sel = fields.Selection(
        selection=[("one", "One"), ("two", "Two")], default="one",
    )
    test_field_binary = fields.Binary()
    test_field_m2o = fields.Many2one("base.changeset.tester2")
    test_field_m2m = fields.Many2many("base.changeset.tester2")
    test_field_o2m = fields.One2many(
        "base.changeset.tester2", inverse_name="test_field_m2o"
    )


class BaseChangesetTester2(models.Model):
    _name = "base.changeset.tester2"
    _description = "Base Changeset Tester 2"
    _inherit = ["base.changeset"]

    name = fields.Char()
    test_field_m2o = fields.Many2one("base.changeset.tester")
