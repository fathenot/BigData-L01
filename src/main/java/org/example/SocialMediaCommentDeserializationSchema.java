package org.example;

import  java.io.IOException;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.DeserializationFeature;
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.databind.ObjectMapper;

public class SocialMediaCommentDeserializationSchema implements DeserializationSchema<SocialMediaComment> {
    private static final long serialVersionUID = 1L;

    private static final ObjectMapper objectMapper = new ObjectMapper().findAndRegisterModules()
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);;

    @Override
    public SocialMediaComment deserialize(byte[] message) throws IOException {
        return objectMapper.readValue(message, SocialMediaComment.class);
    }

    @Override
    public boolean isEndOfStream(SocialMediaComment endOfStream) {
        return false;
    }

    @Override
    public TypeInformation<SocialMediaComment> getProducedType() {
        return TypeInformation.of(SocialMediaComment.class);
    }

}
