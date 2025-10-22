"""Custom Pushbullet notification for Google Tasks."""

import logging

from aiohttp import ClientSession

from .const import ACCESS_TOKEN

_LOGGER = logging.getLogger(__name__)


async def send_pushbullet_notification(config_entry, task_list):
    """Send a Pushbullet notification."""
    access_token = config_entry.options.get(ACCESS_TOKEN)
    api_endpoint = config_entry.options.get("api_endpoint")

    if not task_list:
        _LOGGER.info("No tasks to notify; skipping Pushbullet notification")
        return

    title = "Home Assistant - Daily Task Summary"
    message = "Today's Google Tasks:\n" + "\n".join(f"- {t}" for t in task_list)

    if not access_token:
        _LOGGER.warning("Pushbullet API key not set; skipping notification")
        return

    async with ClientSession() as session:
        try:
            async with session.post(
                api_endpoint,
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
                    _LOGGER.info("Pushbullet notification sent successfully")
        except Exception:
            _LOGGER.exception("Error sending Pushbullet notification")

