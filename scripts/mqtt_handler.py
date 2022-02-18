#!/usr/bin/env python

import paho.mqtt.client as mqtt
import rospy
import json
import threading

class MqttHandler():
    def __init__(self, name, broker='localhost', port=1883, log=False):
        """ Mqtt Client

            :name       : Unique Client Name
            :broker     : Mqtt broker host address
            :port       : Mqtt broker port

            Note:
                The returned message string will be decoded with "utf-8".
                Hence make sure your mqtt messages are utf-8 decodable
        """

        self.name = name
        self.broker = broker
        self.port = port
        self.log = log

        self.client = mqtt.Client(name)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.msg_callback

        rospy.loginfo("%s: Client %s attempting connection with broker %s..."%(rospy.get_name(), self.name, self.broker))
        # Spawn a thread to handle Mqtt connection. Thread will retry connection upon error.
        # Unless, an error is generated if broker is not available at connection time.
        thread = threading.Thread(target=self.start_connection)
        thread.start()

        self.callbacks = {}

    def start_connection(self):
        rate = rospy.Rate(0.1)
        connection_success = False

        while (not(rospy.is_shutdown()) and not(connection_success)):
            try:
                self.client.connect(self.broker, self.port)
                self.client.loop_start()
                connection_success = True
            except Exception as ex:
                rospy.logerr("%s: Client %s error connecting to %s. Retrying..."%(rospy.get_name(), self.name, self.broker))
            rate.sleep()


    def __del__(self):
        """ Destructor
        """
        self.client.disconnect()
        self.client.loop_stop()

    def subscribe(self, topic, callback):
        if not(topic in self.callbacks):
            self.callbacks[topic] = [callback]
        else:
            self.callbacks[topic].append(callback)

    def publish(self, topic, msg):
        # Convert message in case raw dictionary is received
        if (type(msg) == dict):
            msg = json.dumps(msg)

        self.client.publish(topic, msg)

    def on_connect(self, client, userdata, flags, rc):
        """ Client Connected Callback
        """
        rospy.loginfo("%s: Client %s connected with result code %s"%(rospy.get_name(), self.name, str(rc)))
        # Subscribe to all topics
        self.client.subscribe("#")

    def msg_callback(self, client, userdata, msg):
        """ Message Callback Function
        """
        # Process message only if subscribed
        if msg.topic in self.callbacks:
            message = msg.payload.decode("utf-8")
            # Print messages if 'log' is enabled
            if self.log:
                rospy.loginfo("%s: [Topic %s]: %s"%(rospy.get_name(), msg.topic, message))
            # Message Callback
            for callback in self.callbacks[msg.topic]:
                if not(callback is None):
                    callback(message)


###### Example Code #######

# Callback functions
def printTest(msg):
    rospy.loginfo("onTest: " + msg)
    # Can add aditional code here (i.e. ROS Message publishing .etc)
def printStatus(msg):
    rospy.loginfo("onStatus: " + msg)
    # Can add aditional code here (i.e. ROS Message publishing .etc)

# Main function
if __name__ == "__main__":
    rospy.init_node("mqtt_handler")
    rospy.loginfo("MQTT Handler Unit Test")

    # Create mqtt handler 
    mqtt_client = MqttHandler(name="testClient")

    # Subscribe to topics. Upon reception of a message, the provided callback function will be invoked
    mqtt_client.subscribe("/pose_correction", printTest)
    
    # Publish to topics. 
    rate = rospy.Rate(22)
    while not rospy.is_shutdown():
        payload = {"x": 1.0,
                   "y": 0.0,
                   "z": 2.0,
                   
                  }

        mqtt_client.publish("/sensor/data", payload)
        rate.sleep()