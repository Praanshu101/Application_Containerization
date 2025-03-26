FROM docker.elastic.co/elasticsearch/elasticsearch:7.17.0

# Set environment variables for Elasticsearch
ENV discovery.type=single-node
ENV ES_JAVA_OPTS="-Xms512m -Xmx512m"

# Copy custom config (if needed)
COPY elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml

EXPOSE 92000 9300

# Only accessible inside Docker network