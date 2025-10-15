"""Config flow for Google Tasks."""

from collections.abc import Mapping
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest

from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow
import voluptuous as vol

from .const import (
    DOMAIN,
    OAUTH2_SCOPES,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TIME,
)

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Google Tasks OAuth2 authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data appended to the authorize URL."""
        return {
            "scope": " ".join(OAUTH2_SCOPES),
            # Ensure refresh token is always returned
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow."""
        credentials = Credentials(token=data[CONF_TOKEN][CONF_ACCESS_TOKEN])
        try:
            # Verify credentials with Google OAuth2 API
            user_resource = build("oauth2", "v2", credentials=credentials)
            user_resource_cmd: HttpRequest = user_resource.userinfo().get()
            user_resource_info = await self.hass.async_add_executor_job(
                user_resource_cmd.execute
            )

            # Verify access to Google Tasks API
            resource = build("tasks", "v1", credentials=credentials)
            cmd: HttpRequest = resource.tasklists().list()
            await self.hass.async_add_executor_job(cmd.execute)

        except HttpError as ex:
            error = ex.reason
            return self.async_abort(
                reason="access_not_configured",
                description_placeholders={"message": error},
            )
        except Exception:
            self.logger.exception("Unknown error occurred during OAuth2 flow")
            return self.async_abort(reason="unknown")

        user_id = user_resource_info["id"]
        await self.async_set_unique_id(user_id)

        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_resource_info["name"], data=data)

        reauth_entry = self._get_reauth_entry()
        if reauth_entry.unique_id:
            self._abort_if_unique_id_mismatch(reason="wrong_account")

        return self.async_update_reload_and_abort(
            reauth_entry, unique_id=user_id, data=data
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler."""
        return GoogleTasksOptionsFlowHandler(config_entry)


class GoogleTasksOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Google Tasks notifications."""

    def __init__(self, config_entry):
        # ✅ Use a private variable to avoid deprecated assignment
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_NOTIFY_ENABLED,
                    default=self._config_entry.options.get(CONF_NOTIFY_ENABLED, False),
                ): bool,
                vol.Optional(
                    CONF_NOTIFY_SERVICE,
                    default=self._config_entry.options.get(
                        CONF_NOTIFY_SERVICE, "persistent_notification"
                    ),
                ): str,
                vol.Optional(
                    CONF_NOTIFY_TIME,
                    default=self._config_entry.options.get(CONF_NOTIFY_TIME, "08:00"),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
