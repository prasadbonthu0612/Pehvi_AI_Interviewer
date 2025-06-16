FROM python:3.10-slim

# Install Java, git, unzip, and gdown
RUN apt-get update && apt-get install -y default-jre git unzip curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir gdown

# Set the working directory
WORKDIR /app

# Download and extract LanguageTool
RUN mkdir -p /root/.cache/language_tool_python && \
    curl -L https://internal1.languagetool.org/snapshots/LanguageTool-latest-snapshot.zip -o /root/.cache/language_tool_python/LanguageTool-latest.zip && \
    unzip /root/.cache/language_tool_python/LanguageTool-latest.zip -d /root/.cache/language_tool_python && \
    rm /root/.cache/language_tool_python/LanguageTool-latest.zip

# Download answering_model.onnx files
RUN mkdir -p /app/models/answering_model.onnx && \
    gdown --id 1oAaYXdFit0-YnBEPKKfBGTWgKzloQxFF -O /app/models/answering_model.onnx/config.json && \
    gdown --id 1UUguJUH4WDFgrltWOR9gqp92dEI0OXgb -O /app/models/answering_model.onnx/decoder_model.onnx && \
    gdown --id 1YrxaEpcb213QmGgPBH4nWY9rOEo63rM6 -O /app/models/answering_model.onnx/encoder_model.onnx && \
    gdown --id 1E36-_FFOvlqBEalTZwLX23UNzUmRdF19 -O /app/models/answering_model.onnx/generation_config.json && \
    gdown --id 1feDY0VuW2Yt4KwfdBCm2xMq8ECwK-s7J -O /app/models/answering_model.onnx/special_tokens_map.json && \
    gdown --id 15MVna5700fJYbTnz4fkA5I0Yga53zaRs -O /app/models/answering_model.onnx/spiece.model && \
    gdown --id 1qkg8I9UHCCmWNg-ww6vaw63sEhc6HC9e -O /app/models/answering_model.onnx/tokenizer_config.json && \
    gdown --id 1FKOVYEJQfK4oGhhisI3vDRrOOSLmyrsd -O /app/models/answering_model.onnx/tokenizer.json

# Download question_model.onnx files
RUN mkdir -p /app/models/question_model.onnx && \
    gdown --id 1b1jri2YLB-d2LDEeoFbJ2wcDnu3HXO4_ -O /app/models/question_model.onnx/config.json && \
    gdown --id 1jiQctYuNofxz954R2tC6NLa2tG1hBvLE -O /app/models/question_model.onnx/decoder_model.onnx && \
    gdown --id 1h1gn51JsRieQYkvdO_cYQ3R2r1lsGsQq -O /app/models/question_model.onnx/encoder_model.onnx && \
    gdown --id 1Mn3zgnZi7C4-iFp7AzKLsus73V3nUAJd -O /app/models/question_model.onnx/generation_config.json && \
    gdown --id 1dg3mrsOW5d8Nky8w_xPQJWxUlIC2HRCx -O /app/models/question_model.onnx/special_tokens_map.json && \
    gdown --id 1HHCya4Fnl4FQw-7D0Ose0qWwEy5b97yC -O /app/models/question_model.onnx/spiece.model && \
    gdown --id 1Wcc1vtxDWKXotVcNeH0peaeAYqzDDVec -O /app/models/question_model.onnx/tokenizer_config.json && \
    gdown --id 1qHqxALGlcrPXPuK1To2D47wZ425cqcOe -O /app/models/question_model.onnx/tokenizer.json

# Download and unzip Vosk model
RUN mkdir -p /app/models/vosk && \
    gdown --id 1UZiwoEpteJ3me8tDuhkXRWudIySb56KB -O /app/models/vosk/vosk-model.zip && \
    unzip /app/models/vosk/vosk-model.zip -d /app/models/vosk && \
    rm /app/models/vosk/vosk-model.zip

# Copy app code
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Optional: silence Hugging Face warnings (if transformers is used)
RUN pip install --no-cache-dir "transformers[onnx]"

# Let Render know which port to expose
EXPOSE 10000

# Start app with dynamic port assigned by Render
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} main:app"]
