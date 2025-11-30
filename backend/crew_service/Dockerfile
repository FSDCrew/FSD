FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./ 
RUN pip install --no-cache-dir .

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "6011"]