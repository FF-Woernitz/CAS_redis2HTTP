#!/usr/bin/python3
import socket, time, sys, threading, subprocess
from datetime import datetime, time as dtime
import requests
import pprint
import json
from pprint import pprint

from CASlib import Config, Logger, RedisMB


class redis2divera247:
    logger = None

    def __init__(self):
        self.logger = Logger.Logger(self.__name__).getLogger()
        self.config = Config.Config().getConfig()
        self.redisMB = RedisMB.RedisMB()


    def newAlert(self, zvei):
        self.logger.info("{}Received alarm.".format("[" + str(zvei) + "]: "))

        trigger = self.checkIfAlertinFilter(zvei)
        if not trigger:
            self.logger.info("{}Received alarm not in filter. Stopping...".format("[" + str(zvei) + "]: "))
            return
        self.logger.info("{}!!!Received alarm in filter {} (Time: {}) Starting...".format("[" + str(zvei) + "]: ", trigger["name"], str(datetime.now().time())))
        if self.isTestAlert(trigger):
            self.logger.info("{}Testalart time. Stopping...".format("[" + str(zvei) + "]: "))
            return
        self.logger.info("{}Start alarm tasks...".format("[" + str(zvei) + "]: "))
        self.doAlertThings(zvei, trigger)
        return

    def checkIfAlertinFilter(self, zvei):
        for key, config in self.config['triggers'].items():
            if key == zvei:
                return config
        return False

    def isTestAlert(self, trigger):
        begin_time = dtime(trigger["testalarm"]["hour_start"], trigger["testalarm"]["minute_start"])
        end_time = dtime(trigger["testalarm"]["hour_end"], trigger["testalarm"]["minute_end"])
        check_time = datetime.now().time()
        return datetime.today().weekday() == trigger["testalarm"]["weekday"] and check_time >= begin_time and check_time <= end_time

    def doAlertThings(self, zvei, trigger):
        payload = trigger["request"]
        for request_try in range(self.config["retries"]):
            r = requests.get(self.config["url"], params=payload)
            self.logger.debug(pprint.saferepr(r.url))
            self.logger.debug(pprint.saferepr(r.status_code))
            self.logger.debug(pprint.saferepr(r.content))
            self.logger.debug(pprint.saferepr(r.headers))
            if not r.status_code == requests.codes.ok:
                self.logger.error("{}Failed to send alert. Try: {}/{}".format("[" + str(zvei) + "]: ", str(request_try + 1), str(self.config["retries"])))
                time.sleep(self.config["retry_delay"])
                continue
            else:
                self.logger.info("{}Successfully send alert".format("[" + str(zvei) + "]: "))
                break


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
        self.logger.info("starting...")



if __name__ == '__main__':
    c = redis2divera247()
    c.main()
