"""Config flow for Google Tasks."""

from collections.abc import Mapping
import logging
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest
import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntry,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    ACCESS_TOKEN,
    API_ENDPOINT,
    DOMAIN,
    NOTIFICATION_EMAIL,
    NOTIFICATION_ENABLED,
    NOTIFICATION_PUSH,
    NOTIFICATION_TIME,
    OAUTH2_SCOPES,
    RECIPIENT_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USERNAME,
)


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
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": " ".join(OAUTH2_SCOPES),
            # Add params to ensure we get back a refresh token
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow."""
        credentials = Credentials(token=data[CONF_TOKEN][CONF_ACCESS_TOKEN])
        try:
            user_resource = build(
                "oauth2",
                "v2",
                credentials=credentials,
            )
            user_resource_cmd: HttpRequest = user_resource.userinfo().get()
            user_resource_info = await self.hass.async_add_executor_job(
                user_resource_cmd.execute
            )
            resource = build(
                "tasks",
                "v1",
                credentials=credentials,
            )
            cmd: HttpRequest = resource.tasklists().list()
            await self.hass.async_add_executor_job(cmd.execute)
        except HttpError as ex:
            error = ex.reason
            return self.async_abort(
                reason="access_not_configured",
                description_placeholders={"message": error},
            )
        except Exception:
            self.logger.exception("Unknown error occurred")
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
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get config entries for Google Task notifications."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Create config options for Google Tasks notifications."""

    def __init__(self, config_entry) -> None:
        """Initialise config entries."""
        self._config_entry = config_entry
        self._options = dict(config_entry.options)

    async def async_step_init(self, user_input: dict[str, Any]) -> ConfigFlowResult:
        """Setup config entries for notifications."""
        if user_input:
            notification_email = user_input[NOTIFICATION_EMAIL]
            notification_push = user_input[NOTIFICATION_PUSH]
            notification_enabled = user_input[NOTIFICATION_ENABLED]

            if notification_enabled:
                self._options.update(user_input)
                self.context["notification_push"] = notification_push  # type: ignore[typeddict-unknown-key]
                if notification_push and not notification_email:
                    return await self.async_step_push()
                return await self.async_step_email()

        options_schema = vol.Schema(
            {
                vol.Optional(
                    NOTIFICATION_ENABLED,
                    default=self.config_entry.options.get(NOTIFICATION_ENABLED, False),
                ): bool,
                vol.Optional(
                    NOTIFICATION_EMAIL,
                    default=self.config_entry.options.get(NOTIFICATION_EMAIL, False),
                ): bool,
                vol.Optional(
                    NOTIFICATION_PUSH,
                    default=self.config_entry.options.get(NOTIFICATION_PUSH, False),
                ): bool,
                vol.Optional(
                    NOTIFICATION_TIME,
                    default=self.config_entry.options.get(NOTIFICATION_TIME, "07:00"),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)

    async def async_step_email(self, user_input=None) -> ConfigFlowResult:
        """Collect email notification configuration."""
        if user_input:
            notification_push = self.context.get("notification_push")
            self._options.update(user_input)
            if notification_push:
                return await self.async_step_push()

            return self.async_create_entry(
                title="Email Notifications", data=self._options
            )

        return self.async_show_form(
            step_id="email",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        SMTP_HOST, default=self.config_entry.options.get(SMTP_HOST)
                    ): str,
                    vol.Required(
                        SMTP_PORT, default=self.config_entry.options.get(SMTP_PORT, 587)
                    ): int,
                    vol.Required(
                        SMTP_USERNAME,
                        default=self.config_entry.options.get(SMTP_USERNAME),
                    ): str,
                    vol.Required(
                        SMTP_PASSWORD,
                        default=self.config_entry.options.get(SMTP_PASSWORD),
                    ): str,
                    vol.Required(
                        RECIPIENT_EMAIL,
                        default=self.config_entry.options.get(RECIPIENT_EMAIL),
                    ): str,
                }
            ),
        )

    async def async_step_push(self, user_input=None) -> ConfigFlowResult:
        """Collect push notification configuration."""
        if user_input:
            self._options.update(user_input)
            return self.async_create_entry(
                title="Push Notifications", data=self._options
            )

        return self.async_show_form(
            step_id="push",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ACCESS_TOKEN,
                        default=self.config_entry.options.get(ACCESS_TOKEN),
                    ): str,
                    vol.Required(
                        API_ENDPOINT,
                        default=self.config_entry.options.get(API_ENDPOINT),
                    ): str,
                },
            ),
        )
