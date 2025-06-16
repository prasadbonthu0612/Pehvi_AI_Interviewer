FROM python:3.10-slim

# Install Java, git, unzip, and gdown
RUN apt-get update && apt-get install -y default-jre git unzip && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir gdown

# Set the working directory
WORKDIR /app

# Download answering_model.onnx and its files using gdown
RUN mkdir -p /app/models/answering_model.onnx && \
    gdown --id 1oAaYXdFit0-YnBEPKKfBGTWgKzloQxFF -O /app/models/answering_model.onnx/config.json && \
    gdown --id 1UUguJUH4WDFgrltWOR9gqp92dEI0OXgb -O /app/models/answering_model.onnx/decoder_model.onnx && \
    gdown --id 1YrxaEpcb213QmGgPBH4nWY9rOEo63rM6 -O /app/models/answering_model.onnx/encoder_model.onnx && \
    gdown --id 1E36-_FFOvlqBEalTZwLX23UNzUmRdF19 -O /app/models/answering_model.onnx/generation_config.json && \
    gdown --id 1feDY0VuW2Yt4KwfdBCm2xMq8ECwK-s7J -O /app/models/answering_model.onnx/special_tokens_map.json && \
    gdown --id 15MVna5700fJYbTnz4fkA5I0Yga53zaRs -O /app/models/answering_model.onnx/spiece.model && \
    gdown --id 1qkg8I9UHCCmWNg-ww6vaw63sEhc6HC9e -O /app/models/answering_model.onnx/tokenizer_config.json && \
    gdown --id 1FKOVYEJQfK4oGhhisI3vDRrOOSLmyrsd -O /app/models/answering_model.onnx/tokenizer.json

# Download question_model.onnx and its files using gdown
RUN mkdir -p /app/models/question_model.onnx && \
    gdown --id 1Qw8Qw8Qw8Qw8Qw8Qw8Qw8Qw8Qw8Qw8Q -O /app/models/question_model.onnx/config.json && \
    gdown --id 1UUguJUH4WDFgrltWOR9gqp92dEI0OXgb -O /app/models/question_model.onnx/decoder_model.onnx && \
    gdown --id 1YrxaEpcb213QmGgPBH4nWY9rOEo63rM6 -O /app/models/question_model.onnx/encoder_model.onnx && \
    gdown --id 1E36-_FFOvlqBEalTZwLX23UNzUmRdF19 -O /app/models/question_model.onnx/generation_config.json && \
    gdown --id 1feDY0VuW2Yt4KwfdBCm2xMq8ECwK-s7J -O /app/models/question_model.onnx/special_tokens_map.json && \
    gdown --id 15MVna5700fJYbTnz4fkA5I0Yga53zaRs -O /app/models/question_model.onnx/spiece.model && \
    gdown --id 1qkg8I9UHCCmWNg-ww6vaw63sEhc6HC9e -O /app/models/question_model.onnx/tokenizer_config.json && \
    gdown --id 1FKOVYEJQfK4oGhhisI3vDRrOOSLmyrsd -O /app/models/question_model.onnx/tokenizer.json

# Download vosk model (zip) and unzip
RUN mkdir -p /app/models/vosk && \
    gdown --id 1UZiwoEpteJ3me8tDuhkXRWudIySb56KB -O /app/models/vosk/vosk-model.zip && \
    unzip /app/models/vosk/vosk-model.zip -d /app/models/vosk && \
    rm /app/models/vosk/vosk-model.zip

# Copy the rest of the application code
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 10000
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} main:app 
