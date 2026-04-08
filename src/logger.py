import logging
import sys

from telegram import Update
from telegram.ext import ContextTypes


def setup_logger(name: str = "clarity") -> logging.Logger:
    """Configure and return a structured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger()


def log_update(update: Update, action: str, extra: str = "") -> None:
    """Log Telegram update with context."""
    user = update.effective_user
    user_info = f"user={user.id}" if user else "user=unknown"
    chat_info = f"chat={update.effective_chat.id}" if update.effective_chat else ""
    msg = f"{action} | {user_info} {chat_info}".strip()
    if extra:
        msg += f" | {extra}"
    logger.info(msg)


async def async_log_update(update: Update, action: str, extra: str = "") -> None:
    """Async wrapper for logging updates."""
    log_update(update, action, extra)


def log_error(location: str, error: Exception, context: str = "") -> None:
    """Log error with context."""
    ctx = f"{location} | {error.__class__.__name__}: {error}"
    if context:
        ctx += f" | context: {context}"
    logger.error(ctx)


async def async_log_error(
    update: Update, location: str, error: Exception, context: str = ""
) -> None:
    """Async wrapper for logging errors."""
    log_error(location, error, context)
