from json import dumps
from kafka import KafkaProducer

TOPIC_NAME = 'mytopic'
producer = KafkaProducer(security_protocol="SASL_SSL",
                         bootstrap_servers=['b-3.msktutorialcluste.derszf.c2.kafka.ap-southeast-2.amazonaws.com:9098'
                                            ,'b-2.msktutorialcluste.derszf.c2.kafka.ap-southeast-2.amazonaws.com:9098'
                                            ,'b-1.msktutorialcluste.derszf.c2.kafka.ap-southeast-2.amazonaws.com:9098'])

def lambda_handler(event, context):
    print("event = ", event)
    producer.send(TOPIC_NAME, {'msg':'test'})
