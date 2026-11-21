import logging

from weatherbot.config import quiet_noisy_loggers


def test_httpx_logs_are_quiet_to_avoid_token_leak():
    quiet_noisy_loggers()
    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING