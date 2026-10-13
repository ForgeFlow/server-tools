# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import SUPERUSER_ID, api, fields, models, tools
from odoo.http import request

from ..rpc import RPC_CALL

STANDARD_ROUTE_AUTHS = ("user", "public", "none", "bearer")
BEARER_TOKEN_RE = re.compile(r"^bearer\s+(.+)$", re.IGNORECASE)


class AuditlogAuthMethod(models.Model):
    _name = "auditlog.auth.method"
    _description = "Auditlog - Authentication method"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, readonly=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(translate=True)

    _code_uniq = models.Constraint(
        "unique(code)",
        "The code of the authentication method must be unique.",
    )

    @api.model
    @tools.ormcache("code")
    def _get_id_by_code(self, code):
        return self.search([("code", "=", code)], limit=1).id

    @api.model
    def _get_current_auth_info(self):
        rpc_call = RPC_CALL.get()
        if rpc_call and rpc_call[0] == self.env.cr.dbname:
            code, api_key_name = (
                self.env["res.users"]
                .sudo()
                ._auditlog_get_rpc_credential(rpc_call[1], rpc_call[2])
            )
            return code, None, api_key_name
        if not request:
            return "server", None, None
        return self._get_request_auth_info()

    @api.model
    def _get_request_auth_info(self):
        users = self.env["res.users"].sudo()
        session = request.session
        route_auth, route_uid = getattr(request, "_auditlog_route_auth", (None, None))
        if route_auth == "bearer" and route_uid:
            token = self._get_request_bearer_token()
            if token:
                code, api_key_name = users._auditlog_get_rpc_credential(
                    route_uid, token
                )
                return code, None, api_key_name
        if (
            route_auth
            and route_auth not in STANDARD_ROUTE_AUTHS
            and route_uid
            and route_uid != session.uid
            and not users.browse(route_uid)._is_public()
        ):
            return "route_token", None, None
        if session.uid:
            mfa_method = session.get("auditlog_mfa_method")
            if session.uid == SUPERUSER_ID:
                return "web_superuser", mfa_method, None
            code = session.get("auditlog_auth_method") or "web_unknown"
            return code, mfa_method, None
        env = getattr(request, "env", None)
        if env and env.uid and users.browse(env.uid)._is_public():
            return "public", None, None
        return "server", None, None

    @api.model
    def _get_request_bearer_token(self):
        header = request.httprequest.headers.get("Authorization") or ""
        match = BEARER_TOKEN_RE.match(header)
        return match.group(1) if match else None
