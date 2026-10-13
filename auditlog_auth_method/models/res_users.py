# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools
from odoo.http import request

from odoo.addons.base.models.res_users import INDEX_SIZE, KEY_CRYPT_CONTEXT

from .auditlog_log import MFA_METHODS

LOGIN_AUTH_METHODS = {
    "password": "web_password",
    "ldap": "web_password",
    "oauth": "web_oauth",
    "passkey": "web_passkey",
}


class ResUsers(models.Model):
    _inherit = "res.users"

    def _login(self, credential, user_agent_env):
        auth_info = super()._login(credential, user_agent_env=user_agent_env)
        if request and user_agent_env and user_agent_env.get("interactive"):
            user = self.sudo().browse(auth_info["uid"])
            request.session["auditlog_auth_method"] = (
                user._auditlog_get_login_auth_method(auth_info)
            )
            request.session["auditlog_mfa_method"] = user._auditlog_get_mfa_method()
        return auth_info

    def _auditlog_get_login_auth_method(self, auth_info):
        self.ensure_one()
        return LOGIN_AUTH_METHODS.get(auth_info.get("auth_method"), "web_unknown")

    def _auditlog_get_mfa_method(self):
        self.ensure_one()
        mfa_method = self._mfa_type() or "none"
        if mfa_method not in dict(MFA_METHODS):
            return "other"
        return mfa_method

    def _auditlog_is_oauth_access_token(self, token):
        self.ensure_one()
        if "oauth_access_token" not in self._fields:
            return False
        self.env.cr.execute(
            "SELECT 1 FROM res_users WHERE id = %s AND oauth_access_token = %s",
            (self.id, token),
        )
        return bool(self.env.cr.fetchone())

    @api.model
    @tools.ormcache("uid", "passwd")
    def _auditlog_get_rpc_credential(self, uid, passwd):
        self.env.cr.execute(
            """
            SELECT name, key
            FROM res_users_apikeys
            WHERE user_id = %s
                AND index = %s
                AND (scope IS NULL OR scope = 'rpc')
                AND (
                    expiration_date IS NULL
                    OR expiration_date >= now() at time zone 'utc'
                )
            """,
            (uid, passwd[:INDEX_SIZE]),
        )
        for name, key in self.env.cr.fetchall():
            if KEY_CRYPT_CONTEXT.verify(passwd, key):
                return "rpc_api_key", name
        if self.browse(uid)._auditlog_is_oauth_access_token(passwd):
            return "rpc_oauth", None
        return "rpc_password", None
