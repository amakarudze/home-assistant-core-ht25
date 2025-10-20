"""Custom Pushbullet notification for Google Tasks."""

from aiohttp import ClientSession
import logging

from .const import ACCESS_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_send_pushbullet_notification(hass, config_entry, task_list):
    """Send a Pushbullet notification."""
    access_token = config_entry.options.get(ACCESS_TOKEN)
    title = "Google Tasks - Daily Summary"
    message = "Today's Google Tasks:\n" + "\n".join(f"- {t}" for t in task_list)
    if not access_token:
        _LOGGER.warning("Pushbullet API key not set; skipping notification.")
        return

    async with ClientSession() as session:
        try:
            async with session.post(
                "https://api.pushbullet.com/v2/pushes",
                headers={
                    "Access-Token": access_token,
                    "Content-Type": "application/json",
                },
                json={"type": "note", "title": title, "body": message},
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(
                        "Failed to send Pushbullet notification [%s]: %s",
                        resp.status,
                        await resp.text(),
                    )
                else:
                    _LOGGER.info("Pushbullet notification sent successfully.")
        except Exception as err:
            _LOGGER.error("Error sending Pushbullet notification: %s", err)