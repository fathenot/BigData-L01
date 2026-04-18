package org.example;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.connector.kafka.sink.KafkaRecordSerializationSchema;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.kafka.clients.admin.*;

import java.util.Arrays;
import java.util.Properties;

public class Main {

    public static String keyExtractor(SocialMediaComment comment) {
        return comment.topic;
    }

    public static void CleanComment(SocialMediaComment comment) {
        if (comment == null || comment.textComment == null) return;

        comment.textComment = comment.textComment
                .replaceAll("(https?://\\S+|www\\.\\S+)", "")
                .replaceAll("@\\w+", "")
                .replaceAll("#\\w+", "")
                .replaceAll("\\s+", " ")
                .trim()
                .toLowerCase();
    }
    public static void main(String[] args) throws Exception {

        // ========================
        // 1. Tạo Kafka topics
        // ========================
        Properties props = new Properties();
        props.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:29092");

        try (AdminClient admin = AdminClient.create(props)) {

            NewTopic topic1 = new NewTopic("social_media_stream", 3, (short) 1);
            NewTopic topic2 = new NewTopic("processed_comments", 3, (short) 1);
            NewTopic topic3 = new NewTopic("sentiment-input", 3, (short) 1);

            admin.createTopics(Arrays.asList(topic1, topic2, topic3)).all().get();

            System.out.println("Topics created successfully (or already exist).");

        } catch (Exception e) {
            System.out.println("Topic creation may have failed or already exists.");
            e.printStackTrace();
        }

        // ========================
        // 2. Flink environment
        // ========================
        StreamExecutionEnvironment env =
                StreamExecutionEnvironment.getExecutionEnvironment();

        env.setParallelism(1);

        // ========================
        // 3. Kafka Source
        // ========================
        KafkaSource<String> source =
                KafkaSource.<String>builder()
                        .setBootstrapServers("kafka:9092")
                        .setTopics("social_media_stream")
                        .setGroupId("flink-group")
                        .setValueOnlyDeserializer(
                                new SimpleStringSchema()
                        )
                        .build();
        DataStream<String> rawStream = env.fromSource(
                source,
                WatermarkStrategy.noWatermarks(),
                "Kafka Source"
        );

        DataStream<SocialMediaComment> parsed = rawStream
                .map(json -> {
                    try {

                        SocialMediaComment comment =
                                new ObjectMapper().readValue(json, SocialMediaComment.class);

                        CleanComment(comment);
                        return comment;

                    } catch (Exception e) {
                        // tránh crash pipeline
                        System.out.println("Invalid JSON: " + json);
                        return null;
                    }
                })
                .filter(comment -> comment != null);

        KafkaSink<SocialMediaComment> sink =
                KafkaSink.<SocialMediaComment>builder()
                        .setBootstrapServers("kafka:9092")
                        .setRecordSerializer(
                                KafkaRecordSerializationSchema.builder()
                                        .setTopic("processed_comments")
                                        .setValueSerializationSchema(
                                                new GenericValueSerializationSchema<SocialMediaComment>()
                                        )
                                        .build()
                        )
                        .build();

        parsed.sinkTo(sink);
        env.execute("Kafka → Flink Demo");
    }
}