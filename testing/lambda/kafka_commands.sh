# install Java
sudo yum -y install java-11

# download kafka
wget https://archive.apache.org/dist/kafka/2.8.1/kafka_2.12-2.8.1.tgz

# tar file
tar -xzf kafka_2.12-2.8.1.tgz

# cd
cd kafka_2.12-2.8.1/libs

# download jar file
wget https://github.com/aws/aws-msk-iam-auth/releases/download/v1.1.1/aws-msk-iam-auth-1.1.1-all.jar

# cd
cd ../bin

# create file
touch client.properties

# see client.properties file

# create topic
/home/ec2-user/kafka_2.12-2.8.1/bin/kafka-topics.sh --create --bootstrap-server b-1.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098 --command-config client.properties --replication-factor 3 --partitions 1 --topic mytopic

# producer
/home/ec2-user/kafka_2.12-2.8.1/bin/kafka-console-producer.sh --broker-list b-3.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-1.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-2.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098 --producer.config client.properties --topic mytopic

# consumer
/home/ec2-user/kafka_2.12-2.8.1/bin/kafka-console-consumer.sh --bootstrap-server b-3.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-1.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-2.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098 --consumer.config client.properties --topic mytopic --from-beginning

# b-3.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-1.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098,b-2.democluster1.17jbh5.c2.kafka.ap-southeast-2.amazonaws.com:9098