# prerequisite: pip install paho-mqtt
# see documentation https://www.eclipse.org/paho/clients/python/docs/
# run with: python data_ingestion_example.py
import paho.mqtt.client as mqtt
import ssl
import time
import logging
import json
import time


logging.basicConfig(format='[{asctime},{msecs:03.0f}] {levelname} {name}.{lineno}| {message}',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG,
                    style='{')
LOGGER = logging.getLogger()

# insert here your MQTT host, the device/sensor IDs, the path to device certificate (as part of the
# IoT service key), and the password for that certificate file
#
# Mapping of entity IDs:
# IoT deviceAlternateId -> AC equipment external object ID
# IoT sensorAlternateId -> AC model template ID
# IoT capabilityAlternateId -> AC indicator group ID
host = "sample.cp.iot.sap"
deviceAlternateId = "BB61BF0AED"
sensorAlternateId = "pipe_right"
capabilityAlternateId = "strains_raw"
certfile = "PATH/TO/CERTIFICATE.pem"
# !! Do not put this password into a SCM (e.e., Git)!!
# Instead, read it from an environment variable at runtime
certfilePassword = "PASSWORD"

# Example payload - each 'measure' item has to match exactly to the capability generated in IoT!
# Note the special requirements for transferring the time stamp, with property "_time":
#  - needs not to be modeled in SAP Asset Central
#  - content is EPOCH-milliseconds
def get_payload():
    millis = int(round(time.time() * 1000))
    payload = {
        "measures": [
            {
                "_time": millis - 500,
                "strain01": 100,
                "strain02": 101,
                "strain03": 102,
                "strain04": 103
            }, {
                "_time": millis,
                "strain01": 200,
                "strain02": 201,
                "strain03": 202,
                "strain04": 203
            }
        ],
        "sensorAlternateId": sensorAlternateId,
        "capabilityAlternateId": capabilityAlternateId
    }
    return payload

###############################################################################

return_codes = {
    0: "Connection successful",
    1: "Connection refused – incorrect protocol version",
    2: "Connection refused – invalid client identifier",
    3: "Connection refused – server unavailable",
    4: "Connection refused – bad username or password",
    5: "Connection refused – not authorised",
}


def on_connect(mqttc, obj, flags, rc):
    LOGGER.info(f"==on_connect== connect return code {str(rc)}: {return_codes[rc]}")

def on_message(mqttc, obj, msg):
    LOGGER.info("==on_message== " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(mqttc, obj, mid):
    LOGGER.info("==on_publish== Message ID: " + str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    LOGGER.info("==on_subscribe== " + str(mid) + " " + str(granted_qos))


# the client ID is essential here!
mqttc = mqtt.Client(client_id=deviceAlternateId)
port = 8883
mqttc.enable_logger()

mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

keepalive = 60
topic = f"measures/{deviceAlternateId}"
qos = 2
LOGGER.debug(f"Connecting to {host} port: {str(port)}, keepalive {keepalive}")
mqttc.connect(host, port, keepalive)

protocol = ssl.PROTOCOL_TLSv1_2
ssl_context = ssl.SSLContext(protocol)
ssl_context.load_cert_chain(certfile, password=certfilePassword)
mqttc.tls_set_context(ssl_context)

LOGGER.debug("Loop starting...")
mqttc.loop_start()

for x in range(0, 10):
    message = json.dumps(get_payload())

    LOGGER.debug(f"Publishing # {x}: topic {topic}, qos {qos}, message {message}")
    # here comes now the data transfer:
    infot = mqttc.publish(topic, message, qos=qos)
    LOGGER.debug(f"Return code: {infot.rc}")

    infot.wait_for_publish()
    LOGGER.debug("Publishing DONE")

    time.sleep(1)

mqttc.loop_stop()
mqttc.disconnect()
