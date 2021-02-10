#!/usr/bin/python3
import requests
import signal
import time
from datetime import datetime

from logbook import INFO, NOTICE, WARNING

from CASlib import Config, Logger, RedisMB


class redis2divera247:
    logger = None

    def __init__(self):
        self.logger = Logger.Logger(self.__class__.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()
        self.thread = None
        signal.signal(signal.SIGTERM, self.signalHandler)
        signal.signal(signal.SIGHUP, self.signalHandler)

    def log(self, level, log, alert=""):
        self.logger.log(level, "[{}]: {}".format(alert, log))

    def signalHandler(self, signum, frame):
        self.log(INFO, 'Signal handler called with signal {}'.format(signum))
        try:
            if self.thread is not None:
                self.thread.kill()
            self.redisMB.exit()
        except Exception:
            pass
        self.log(NOTICE, 'exiting...')
        exit()

    def newAlert(self, data):
        message = self.redisMB.decodeMessage(data)
        zvei = message['zvei']
        self.log(INFO,
                 "Received alarm. UUID: {} (Time: {}) Starting...".format(
                     message['uuid'], str(datetime.now().time())), zvei)

        trigger = self.getAlertFromConfig(zvei)
        if not trigger:
            self.log(WARNING,
                     "Received alarm not in config. "
                     "Different config for the modules?!"
                     " Stopping...",
                     zvei)
            return

        self.log(INFO, "Start alarm tasks...", zvei)
        self.doAlertThings(zvei, trigger)
        return

    def getAlertFromConfig(self, zvei):
        for key, config in self.config['trigger'].items():
            if key == zvei:
                return config
        return False

    def doAlertThings(self, zvei, trigger):
        payload = trigger["request"]
        divera247Config = self.config["divera247"]
        for request_try in range(divera247Config["retries"]):
            r = requests.get(divera247Config["url"], params=payload)
            self.logger.debug(r.url)
            self.logger.debug(r.status_code)
            self.logger.debug(r.content)
            self.logger.debug(r.headers)
            if not r.status_code == requests.codes.ok:
                self.log(NOTICE,
                         "Failed to send alert. Code: {} Try: {}/{}".format(
                             r.status_code, str(request_try + 1),
                             str(divera247Config["retries"])),
                         zvei)
                time.sleep(divera247Config["retry_delay"])
                continue
            else:
                self.log(INFO, "Successfully send alert", zvei)
                return

        self.log(WARNING,
                 "Giving up after {} tries. Failed to send alert.".format(
                     str(divera247Config["retries"])),
                 zvei)
        return

    def main(self):
        self.log(INFO, "starting...")
        try:
            self.thread = self.redisMB.subscribeToType("alertZVEI",
                                                       self.newAlert)
            self.thread.join()
        except KeyboardInterrupt:
            self.signalHandler("KeyboardInterrupt", None)


if __name__ == '__main__':
    c = redis2divera247()
    c.main()
