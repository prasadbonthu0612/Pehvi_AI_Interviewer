FROM python:3.10-slim

# Install Java, wget, and git
RUN apt-get update && apt-get install -y default-jre wget git && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Download answering_model.onnx and its files
RUN mkdir -p /app/models/answering_model.onnx && \
    wget -O /app/models/answering_model.onnx/config.json "https://drive.google.com/uc?export=download&id=1oAaYXdFit0-YnBEPKKfBGTWgKzloQxFF" && \
    wget -O /app/models/answering_model.onnx/decoder_model.onnx "https://drive.google.com/uc?export=download&id=1UUguJUH4WDFgrltWOR9gqp92dEI0OXgb" && \
    wget -O /app/models/answering_model.onnx/encoder_model.onnx "https://drive.google.com/uc?export=download&id=1YrxaEpcb213QmGgPBH4nWY9rOEo63rM6" && \
    wget -O /app/models/answering_model.onnx/generation_config.json "https://drive.google.com/uc?export=download&id=1E36-_FFOvlqBEalTZwLX23UNzUmRdF19" && \
    wget -O /app/models/answering_model.onnx/special_tokens_map.json "https://drive.google.com/uc?export=download&id=1feDY0VuW2Yt4KwfdBCm2xMq8ECwK-s7J" && \
    wget -O /app/models/answering_model.onnx/spiece.model "https://drive.google.com/uc?export=download&id=15MVna5700fJYbTnz4fkA5I0Yga53zaRs" && \
    wget -O /app/models/answering_model.onnx/tokenizer_config.json "https://drive.google.com/uc?export=download&id=1qkg8I9UHCCmWNg-ww6vaw63sEhc6HC9e" && \
    wget -O /app/models/answering_model.onnx/tokenizer.json "https://drive.google.com/uc?export=download&id=1FKOVYEJQfK4oGhhisI3vDRrOOSLmyrsd"

# Download question_model.onnx and its files
RUN mkdir -p /app/models/question_model.onnx && \
    wget -O /app/models/question_model.onnx/config.json "https://drive.google.com/uc?export=download&id=1Qw8Qw8Qw8Qw8Qw8Qw8Qw8Qw8Qw8Qw8Q" && \
    wget -O /app/models/question_model.onnx/decoder_model.onnx "https://drive.google.com/uc?export=download&id=1UUguJUH4WDFgrltWOR9gqp92dEI0OXgb" && \
    wget -O /app/models/question_model.onnx/encoder_model.onnx "https://drive.google.com/uc?export=download&id=1YrxaEpcb213QmGgPBH4nWY9rOEo63rM6" && \
    wget -O /app/models/question_model.onnx/generation_config.json "https://drive.google.com/uc?export=download&id=1E36-_FFOvlqBEalTZwLX23UNzUmRdF19" && \
    wget -O /app/models/question_model.onnx/special_tokens_map.json "https://drive.google.com/uc?export=download&id=1feDY0VuW2Yt4KwfdBCm2xMq8ECwK-s7J" && \
    wget -O /app/models/question_model.onnx/spiece.model "https://drive.google.com/uc?export=download&id=15MVna5700fJYbTnz4fkA5I0Yga53zaRs" && \
    wget -O /app/models/question_model.onnx/tokenizer_config.json "https://drive.google.com/uc?export=download&id=1qkg8I9UHCCmWNg-ww6vaw63sEhc6HC9e" && \
    wget -O /app/models/question_model.onnx/tokenizer.json "https://drive.google.com/uc?export=download&id=1FKOVYEJQfK4oGhhisI3vDRrOOSLmyrsd"

# Download vosk model (example: download and unzip)
RUN mkdir -p /app/models/vosk && \
    wget -O /app/models/vosk/vosk-model.zip "https://drive.google.com/file/d/1UZiwoEpteJ3me8tDuhkXRWudIySb56KB" && \
    apt-get update && apt-get install -y unzip && \
    unzip /app/models/vosk/vosk-model.zip -d /app/models/vosk && \
    rm /app/models/vosk/vosk-model.zip

# Continue with the rest of your Dockerfile...
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 10000
CMD gunicorn --bind 0.0.0.0:${PORT:-10000} main:app
