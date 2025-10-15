"""Config flow for Google Tasks."""

from collections.abc import Mapping
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
import voluptuous as vol

from .const import (
    DOMAIN,
    OAUTH2_SCOPES,
    CONF_NOTIFICATION_ENABLED,
    CONF_NOTIFICATION_SERVICE,
    CONF_NOTIFICATION_TIME,
    CONF_NOTIFICATION_METHOD,
    NOTIFICATION_METHOD_PUSH,
    NOTIFICATION_METHOD_EMAIL,
    CONF_EMAIL_SENDER,
    CONF_EMAIL_RECIPIENT,
    CONF_EMAIL_SERVER,
    CONF_EMAIL_PORT,
    CONF_EMAIL_USERNAME,
    CONF_EMAIL_PASSWORD,
)

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle OAuth2 login for Google Tasks."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra OAuth parameters."""
        return {
            "scope": " ".join(OAUTH2_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create config entry after OAuth."""
        credentials = Credentials(token=data[CONF_TOKEN][CONF_ACCESS_TOKEN])
        try:
            user_resource = build("oauth2", "v2", credentials=credentials)
            user_cmd: HttpRequest = user_resource.userinfo().get()
            user_info = await self.hass.async_add_executor_job(user_cmd.execute)

            resource = build("tasks", "v1", credentials=credentials)
            cmd: HttpRequest = resource.tasklists().list()
            await self.hass.async_add_executor_job(cmd.execute)

        except HttpError as ex:
            return self.async_abort(
                reason="access_not_configured",
                description_placeholders={"message": ex.reason},
            )
        except Exception as err:
            _LOGGER.exception("Unknown error during OAuth2: %s", err)
            return self.async_abort(reason="unknown")

        user_id = user_info["id"]
        await self.async_set_unique_id(user_id)

        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_info["name"], data=data)

        reauth_entry = self._get_reauth_entry()
        if reauth_entry.unique_id:
            self._abort_if_unique_id_mismatch(reason="wrong_account")

        return self.async_update_reload_and_abort(
            reauth_entry, unique_id=user_id, data=data
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow handler."""
        return GoogleTasksOptionsFlowHandler(config_entry)


# ---------------------------------------------------------------------
# Options Flow with Dynamic Email/Push Fields
# ---------------------------------------------------------------------
class GoogleTasksOptionsFlowHandler(OptionsFlow):
    """Handle dynamic options for notifications."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Main options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self._config_entry.options

        # --- Base schema (always shown) ---
        base_schema = {
            vol.Optional(
                CONF_NOTIFICATION_ENABLED, default=opts.get(CONF_NOTIFICATION_ENABLED, False)
            ): bool,
            vol.Optional(
                CONF_NOTIFICATION_METHOD,
                default=opts.get(CONF_NOTIFICATION_METHOD, NOTIFICATION_METHOD_PUSH),
            ): vol.In(
                {
                    NOTIFICATION_METHOD_PUSH: "Push Notification",
                    NOTIFICATION_METHOD_EMAIL: "Email Notification",
                }
            ),
        }

        # Determine selected method
        selected_method = opts.get(CONF_NOTIFICATION_METHOD, NOTIFICATION_METHOD_PUSH)

        # --- Conditional fields for each method ---
        if selected_method == NOTIFICATION_METHOD_EMAIL:
            # Email-specific fields
            base_schema.update(
                {
                    vol.Optional(
                        CONF_EMAIL_SERVER,
                        default=opts.get(CONF_EMAIL_SERVER, "smtp.gmail.com"),
                    ): str,
                    vol.Optional(
                        CONF_EMAIL_PORT, default=opts.get(CONF_EMAIL_PORT, 587)
                    ): int,
                    vol.Optional(
                        CONF_EMAIL_SENDER, default=opts.get(CONF_EMAIL_SENDER, "")
                    ): str,
                    vol.Optional(
                        CONF_EMAIL_RECIPIENT,
                        default=opts.get(CONF_EMAIL_RECIPIENT, ""),
                    ): str,
                    vol.Optional(
                        CONF_EMAIL_USERNAME,
                        default=opts.get(CONF_EMAIL_USERNAME, ""),
                    ): str,
                    vol.Optional(
                        CONF_EMAIL_PASSWORD,
                        default=opts.get(CONF_EMAIL_PASSWORD, ""),
                    ): str,
                }
            )
        else:
            # Push-specific fields
            base_schema.update(
                {
                    vol.Optional(
                        CONF_NOTIFICATION_SERVICE,
                        default=opts.get(CONF_NOTIFICATION_SERVICE, "persistent_notification"),
                    ): str,
                }
            )

        # Common to both
        base_schema.update(
            {
                vol.Optional(
                    CONF_NOTIFICATION_TIME, default=opts.get(CONF_NOTIFICATION_TIME, "08:00")
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(base_schema),
        )
