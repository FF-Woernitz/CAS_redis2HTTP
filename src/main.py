#!/usr/bin/python3
import time, requests, pprint
from datetime import datetime
from logbook import INFO, NOTICE, WARNING
from CASlib import Config, Logger, RedisMB, Helper


class redis2divera247:
    logger = None

    def __init__(self):
        self.logger = Logger.Logger(self.__class__.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()
        self.helper = Helper.Helper()

    def log(self, level, log, zvei="No ZVEI"):
        self.logger.log(level, "[{}]: {}".format(zvei, log))

    def newAlert(self, message):
        zvei = message['zvei']
        self.log(INFO, "Received alarm. UUID: {}".format(message['uuid']), zvei)

        trigger = self.checkIfAlertinFilter(zvei)
        if not trigger:
            self.log(INFO, "Received alarm not in filter. Stopping...", zvei)
            return
        self.log(INFO, "Received alarm in filter {} (Time: {}) Starting...".format(trigger["name"],
                                                                                      str(datetime.now().time())), zvei)
        if self.helper.isTestAlert(trigger):
            self.log(INFO, "Testalart time. Stopping...", zvei)
            return
        self.log(INFO, "Start alarm tasks...", zvei)
        self.doAlertThings(zvei, trigger)
        return

    def checkIfAlertinFilter(self, zvei):
        for key, config in self.config['triggers'].items():
            if key == zvei:
                return config
        return False

    def doAlertThings(self, zvei, trigger):
        payload = trigger["request"]
        divera247Config = self.config["divera247"]
        for request_try in range(divera247Config["retries"]):
            r = requests.get(divera247Config["url"], params=payload)
            self.logger.debug(pprint.saferepr(r.url))
            self.logger.debug(pprint.saferepr(r.status_code))
            self.logger.debug(pprint.saferepr(r.content))
            self.logger.debug(pprint.saferepr(r.headers))
            if not r.status_code == requests.codes.ok:
                self.log(NOTICE,
                         "Failed to send alert. Try: {}/{}".format(str(request_try + 1), str(divera247Config["retries"])),
                         zvei)
                time.sleep(divera247Config["retry_delay"])
                continue
            else:
                self.log(INFO, "Successfully send alert", zvei)
                return

        self.log(WARNING, "Giving up after {} tries. Failed to send alert.".format(str(self.configdivera247Config["retries"])), zvei)

        # if trigger["local"]:
        #     try:
        #         self.logger.info("Starting light control")
        #         debugOutput = subprocess.check_output('/usr/bin/python3 /opt/light/FFWLightControlTrigger.py', shell=True)
        #         self.logger.debug(pprint.saferepr(debugOutput))
        #     except:
        #         self.logger.error("Light control exception")
        #
        #     try:
        #         self.logger.info("Starting TV control")
        #         subprocess.check_output('/usr/bin/php /usr/local/bin/automate_tv 900 &', shell=True)
        #     except:
        #         self.logger.info("TV control exception")

        return

    def main(self):
        self.log(INFO, "starting...")
        t = self.redisMB.subscribeToType("new_zvei", self.newAlert)


if __name__ == '__main__':
    c = redis2divera247()
    c.main()
