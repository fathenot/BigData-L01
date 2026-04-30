-- public.mlmodel definition

-- Drop table

-- DROP TABLE public.mlmodel;

CREATE TABLE public.mlmodel ( model_version_id varchar(50) NOT NULL, algorithm_name varchar(100) NOT NULL, deployment_date timestamptz DEFAULT CURRENT_TIMESTAMP NULL, CONSTRAINT mlmodel_pkey PRIMARY KEY (model_version_id));

-- Permissions

ALTER TABLE public.mlmodel OWNER TO "admin";
GRANT ALL ON TABLE public.mlmodel TO "admin";


-- public.product definition

-- Drop table

-- DROP TABLE public.product;

CREATE TABLE public.product ( product_asin varchar(20) NOT NULL, product_name text NULL, category varchar(100) NULL, CONSTRAINT product_pkey PRIMARY KEY (product_asin));

-- Permissions

ALTER TABLE public.product OWNER TO "admin";
GRANT ALL ON TABLE public.product TO "admin";


-- public.streamtopic definition

-- Drop table

-- DROP TABLE public.streamtopic;

CREATE TABLE public.streamtopic ( topic_id uuid DEFAULT gen_random_uuid() NOT NULL, topic_name varchar(255) NOT NULL, description text NULL, CONSTRAINT streamtopic_pkey PRIMARY KEY (topic_id), CONSTRAINT streamtopic_topic_name_key UNIQUE (topic_name));

-- Permissions

ALTER TABLE public.streamtopic OWNER TO "admin";
GRANT ALL ON TABLE public.streamtopic TO "admin";


-- public.amazonreview definition

-- Drop table

-- DROP TABLE public.amazonreview;

CREATE TABLE public.amazonreview ( review_id uuid NOT NULL, topic_id uuid NOT NULL, product_asin varchar(20) NOT NULL, original_text text NOT NULL, star_rating int2 NULL, event_time timestamptz NOT NULL, CONSTRAINT amazonreview_pkey PRIMARY KEY (review_id), CONSTRAINT amazonreview_star_rating_check CHECK (((star_rating >= 1) AND (star_rating <= 5))), CONSTRAINT fk_product FOREIGN KEY (product_asin) REFERENCES public.product(product_asin), CONSTRAINT fk_topic FOREIGN KEY (topic_id) REFERENCES public.streamtopic(topic_id));
CREATE INDEX idx_review_event_time ON public.amazonreview USING btree (event_time);
CREATE INDEX idx_review_product ON public.amazonreview USING btree (product_asin);

-- Permissions

ALTER TABLE public.amazonreview OWNER TO "admin";
GRANT ALL ON TABLE public.amazonreview TO "admin";


-- public.sentimentresult definition

-- Drop table

-- DROP TABLE public.sentimentresult;

CREATE TABLE public.sentimentresult ( result_id uuid DEFAULT gen_random_uuid() NOT NULL, review_id uuid NOT NULL, model_version_id varchar(50) NOT NULL, sentiment_label varchar(20) NULL, confidence_score numeric(5, 4) NULL, processed_time timestamptz NOT NULL, CONSTRAINT sentimentresult_confidence_score_check CHECK (((confidence_score >= (0)::numeric) AND (confidence_score <= (1)::numeric))), CONSTRAINT sentimentresult_pkey PRIMARY KEY (result_id), CONSTRAINT sentimentresult_sentiment_label_check CHECK (((sentiment_label)::text = ANY ((ARRAY['positive'::character varying, 'neutral'::character varying, 'negative'::character varying])::text[]))), CONSTRAINT fk_model FOREIGN KEY (model_version_id) REFERENCES public.mlmodel(model_version_id), CONSTRAINT fk_review FOREIGN KEY (review_id) REFERENCES public.amazonreview(review_id) ON DELETE CASCADE);
CREATE INDEX idx_sentiment_processed_time ON public.sentimentresult USING btree (processed_time);

-- Permissions

ALTER TABLE public.sentimentresult OWNER TO "admin";
GRANT ALL ON TABLE public.sentimentresult TO "admin";

-- Seed: MLModel row required by SentimentResult FK constraint
INSERT INTO public.mlmodel (model_version_id, algorithm_name)
VALUES ('svm-v1.0', 'RoBERTa (cardiffnlp/twitter-roberta-base-sentiment)')
ON CONFLICT DO NOTHING;