FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Le token vient d'une variable d'environnement, jamais du code.
CMD ["python", "bot.py"]
