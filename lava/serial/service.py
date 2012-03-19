# Copyright (C) 2011-2012 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of LAVA Serial
#
# LAVA Serial is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA Serial is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA Serial.  If not, see <http://www.gnu.org/licenses/>.

import logging

from kombu import (
    Connection,
    Exchange,
    Producer,
)


SerialOutputExchange = Exchange(
    name="lava.serial.output",
    type="topic",
    auto_delete=False,  # Don't remove this exchange once all queues are removed
    durable=True,  # Don't remove it after server restart
    delivery_mode="transient"
)  # Don't store messages on the server disk


class BrokerBridgeService(object):
    """
    Service that exposes serial messages to a message broker
    """

    def __init__(self, device_path, broker_url): 
        """
        Initialize the service with the specified device path and broker URL
        """
        self.device_path = device_path
        self.broker_url = broker_url

    @property
    def routing_key(self):
        """
        Routing key used to send messages
        """
        return self.device_path

    def run_forever(self):
        """
        Run forever.

        This will take any output and send it back to the exchange
        """
        logging.debug("Connecting to %r", self.broker_url)
        # We'll talk to this broker
        connection = Connection(self.broker_url)
        with connection:
            logging.debug("Creating exchange...")
            exchange = SerialOutputExchange(connection) 
            # We'll use this exchange for our messages
            logging.debug("Creating producer...")
            producer = Producer(
                channel=connection,
                exchange=exchange,
                routing_key=self.routing_key)
            # We'll use this to publish messages
            logging.debug("Ready to transmit messages!")
            while True:
                logging.debug("Waiting for input...")
                # Get some fake input
                try:
                    text = raw_input("Tell me something (CTRL+C to exit): ")
                except (KeyboardInterrupt, EOFError):
                    break
                # And publish it
                logging.debug("Sending message...")
                producer.publish({"text": text})
            logging.info("Shutting down")
