import logging
import threading
from ._config import load as config_loader
from .filter import create_filters
from .monitor import Monitor
from .notifiers import NotifierFactory
from ._utils import _notify_boot


class CLI(object):
    def __init__(self, logger):
        self._logger = logger
        self._notifier_factory = NotifierFactory(logger)

    def init(self, config_file, verbose=False):
        self._config = config_loader(config_file)
        if verbose:
            self._logger.setLevel(logging.DEBUG)

    def run(self, boot_file_path):
        notifier = self._notifier_factory.create_notifiers(self._config.notifiers)

        boot_settings = self._config.get_settings("boot", {})
        if boot_settings.get("notify", False):
            # Notification of boot should not hold up reading from journal ASAP
            boot_notify_thread = threading.Thread(target=_notify_boot, args=(notifier, boot_file_path, boot_settings), daemon=True)
            boot_notify_thread.start()

        filters = create_filters(self._config.filters)
        reader_settings = self._config.get_settings("reader", {})
        monitor = Monitor(notifier, filters, reader_settings)
        monitor.monitor(self._config.get_settings("journal_reader_timeout", None))

    def test_filters(self):
        notifier = self._notifier_factory.create_notifiers({"stdout": {"type": "stdout"}})
        filters = create_filters(self._config.filters)
        # Force all filters to accept all notifiers, so that the stdout notifier is always used
        for f in filters:
            f.notifiers = []
        reader_settings = self._config.get_settings("reader", {})
        monitor = Monitor(notifier, filters, reader_settings)
        monitor.scan()

    def test_notifiers(self):
        notifier = self._notifier_factory.create_notifiers(self._config.notifiers)
        notifier.notify("This is a test message", "This is the message body")
