"""Config flow for Google Tasks integration with custom Pushbullet and Email notifications."""

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
    CONF_NOTIFY_TIME,
    CONF_NOTIFY_METHOD,
    NOTIFY_METHOD_PUSH,
    NOTIFY_METHOD_EMAIL,
    CONF_PUSHBULLET_API_KEY,
    CONF_EMAIL_SENDER,
    CONF_EMAIL_PASSWORD,
    CONF_EMAIL_RECIPIENT,
    CONF_EMAIL_SERVER,
    CONF_EMAIL_PORT,
    DEFAULT_EMAIL_SERVER,
    DEFAULT_EMAIL_PORT,
)

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle Google Tasks OAuth2 authentication."""

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
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry after OAuth2 authentication."""
        credentials = Credentials(token=data[CONF_TOKEN][CONF_ACCESS_TOKEN])

        try:
            user_resource = build("oauth2", "v2", credentials=credentials)
            user_resource_cmd: HttpRequest = user_resource.userinfo().get()
            user_resource_info = await self.hass.async_add_executor_job(
                user_resource_cmd.execute
            )

            resource = build("tasks", "v1", credentials=credentials)
            cmd: HttpRequest = resource.tasklists().list()
            await self.hass.async_add_executor_job(cmd.execute)

        except HttpError as ex:
            return self.async_abort(
                reason="access_not_configured",
                description_placeholders={"message": ex.reason},
            )
        except Exception:
            self.logger.exception("Unknown error occurred during OAuth2 flow")
            return self.async_abort(reason="unknown")

        user_id = user_resource_info["id"]
        await self.async_set_unique_id(user_id)

        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title= user_resource_info["name"], data=data)

        reauth_entry = self._get_reauth_entry()
        if reauth_entry.unique_id:
            self._abort_if_unique_id_mismatch(reason="wrong_account")

        return self.async_update_reload_and_abort(
            reauth_entry, unique_id=user_id, data=data
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Perform reauth."""
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
        """Return the options flow handler."""
        return GoogleTasksOptionsFlowHandler(config_entry)


class GoogleTasksOptionsFlowHandler(OptionsFlow):
    """Handle options flow for notification settings."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Options flow for selecting notification method and credentials."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Common fields
        options_schema = {
            vol.Optional(
                CONF_NOTIFY_ENABLED,
                default=self._config_entry.options.get(CONF_NOTIFY_ENABLED, False),
            ): bool,
            vol.Optional(
                CONF_NOTIFY_METHOD,
                default=self._config_entry.options.get(
                    CONF_NOTIFY_METHOD, NOTIFY_METHOD_PUSH
                ),
            ): vol.In(
                {
                    NOTIFY_METHOD_PUSH: "Pushbullet Notification",
                    NOTIFY_METHOD_EMAIL: "Email (SMTP) Notification",
                }
            ),
            vol.Optional(
                CONF_NOTIFY_TIME,
                default=self._config_entry.options.get(CONF_NOTIFY_TIME),
            ): str,
        }

        # Add fields based on selected method
        method = self._config_entry.options.get(CONF_NOTIFY_METHOD, NOTIFY_METHOD_PUSH)
        if method == NOTIFY_METHOD_PUSH:
            options_schema.update(
                {
                    vol.Required(
                        CONF_PUSHBULLET_API_KEY,
                        default=self._config_entry.options.get(CONF_PUSHBULLET_API_KEY, ""),
                    ): str,
                }
            )
        elif method == NOTIFY_METHOD_EMAIL:
            options_schema.update(
                {
                    vol.Required(
                        CONF_EMAIL_SERVER,
                        default=self._config_entry.options.get(
                            CONF_EMAIL_SERVER, DEFAULT_EMAIL_SERVER
                        ),
                    ): str,
                    vol.Required(
                        CONF_EMAIL_PORT,
                        default=self._config_entry.options.get(
                            CONF_EMAIL_PORT, DEFAULT_EMAIL_PORT
                        ),
                    ): int,
                    vol.Required(
                        CONF_EMAIL_SENDER,
                        default=self._config_entry.options.get(CONF_EMAIL_SENDER, ""),
                    ): str,
                    vol.Required(
                        CONF_EMAIL_PASSWORD,
                        default=self._config_entry.options.get(CONF_EMAIL_PASSWORD, ""),
                    ): str,
                    vol.Required(
                        CONF_EMAIL_RECIPIENT,
                        default=self._config_entry.options.get(CONF_EMAIL_RECIPIENT, ""),
                    ): str,
                }
            )

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options_schema))
