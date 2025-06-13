FROM python:3.10-slim
WORKDIR /src
COPY . .
RUN pip install python-telegram-bot huggingface_hub
CMD ["python", "bot.py"]
