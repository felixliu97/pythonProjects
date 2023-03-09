import json
import time
from time import time
from confluent_kafka import Producer

KAFKA_BROKER = 'b-3.democluster1.o158i3.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-1.democluster1.o158i3.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-2.democluster1.o158i3.c2.kafka.ap-southeast-2.amazonaws.com:9098'
KAFKA_TOPIC = 'mytopic'

producer = Producer({
    'bootstrap.servers': KAFKA_BROKER,
    'socket.timeout.ms': 100,
    'api.version.request': 'false',
    'broker.version.fallback': '0.9.0',
    'message.max.bytes': 1000000000
    # 'security.protocol': 'SASL_SSL',
    # 'sasl.mechanism': 'AWS_MSK_IAM'
})


def lambda_handler(event, context):
    print("event = ",event)
    start_time = int(time() * 1000)
    #This is test data, you can get data from the event
    data = {"name": "xyz", "email": "xyz@"}

    send_msg_async(data)

    end_time = int(time() * 1000)
    time_taken = (end_time - start_time) / 1000
    print("Time taken to complete = %s seconds" % (time_taken))
    print(event)


def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(
            msg.topic(), msg.partition()))


def send_msg_async(msg):
    print("Sending message")
    try:
        msg_json_str = str({"data": json.dumps(msg)})
        producer.produce(
            KAFKA_TOPIC,
            msg_json_str,
            callback=lambda err, original_msg=msg_json_str: delivery_report(err, original_msg
                                                                            ),
        )
        producer.flush()
    except Exception as ex:
        print("Error : ", ex)