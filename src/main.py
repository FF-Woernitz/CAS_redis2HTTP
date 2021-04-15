#!/usr/bin/python3
import signal
import time

from CASlibrary import Action, Config, Logger, RedisMB

import requests


class redis2HTTP:
    logger = None

    def __init__(self):
        self.logger = Logger.Logger(self.__class__.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()
        self.thread = None
        signal.signal(signal.SIGTERM, self.signalHandler)
        signal.signal(signal.SIGHUP, self.signalHandler)

    def signalHandler(self, signum, frame):
        self.logger.info('Signal handler called with signal {}'.format(signum))
        try:
            if self.thread is not None:
                self.thread.kill()
            self.redisMB.exit()
        except BaseException:
            pass
        self.logger.notice('exiting...')
        exit()

    def messageHandler(self, data):
        message = self.redisMB.decodeMessage(data)
        self.logger.debug("Received message: {}".format(message))
        action = message['message']['action']
        for configActionKey, configAction in self.config["action"].items():
            self.logger.debug("Check if action {} requested".format(configActionKey))
            if configActionKey.upper() == action.upper():
                self.logger.debug("Action {}, does match the requested key".format(configActionKey))
                if configAction["type"].upper() == "HTTP":
                    self.logger.info("Executing action {}".format(configAction["name"]))
                    self.doAction(configAction, message['message']['data'])

    def doAction(self, action, param):
        conf_retries = action["data"]["retries"] if "retries" in action["data"] else 3
        conf_retry_delay = action["data"]["retry_delay"] if "retry_delay" in action["data"] else 5
        payload = action["data"]["payload"] if "payload" in action["data"] else {}

        payload = Action.templateData(self.logger, self.config, payload, param)

        for request_try in range(conf_retries):
            self.logger.info(f"Sending request to url {action['data']['url']}")
            result = requests.request(action["data"]["method"], action["data"]["url"], **payload)
            self.logger.debug(result.url)
            self.logger.debug(payload)
            self.logger.debug(result.status_code)
            self.logger.debug(result.content)
            self.logger.debug(result.headers)
            if not result.status_code == requests.codes.ok:
                self.logger.notice(
                    "Failed to send request. Code: {} Try: {}/{}".format(result.status_code, str(request_try + 1),
                                                                         str(conf_retries)))
                time.sleep(conf_retry_delay)
                continue
            else:
                self.logger.info("Successfully send request")
                return

        self.logger.warning("Giving up after {} tries. Failed to send request.".format(str(conf_retries)))
        return

    def main(self):
        self.logger.info("starting...")
        try:
            self.thread = self.redisMB.subscribeToType("action", self.messageHandler, True)
            self.thread.join()
        except KeyboardInterrupt:
            self.signalHandler("KeyboardInterrupt", None)


if __name__ == '__main__':
    c = redis2HTTP()
    c.main()
