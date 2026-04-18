package org.example;

import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.SerializationSchema;


public class GenericValueSerializationSchema<T> implements SerializationSchema<T> {

    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public byte[] serialize(T element) {
        try {
            return mapper.writeValueAsBytes(element);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
