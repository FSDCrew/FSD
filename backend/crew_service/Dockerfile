FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./ 
RUN pip install --no-cache-dir .

RUN playwright install chromium --with-deps

COPY . .

COPY ./scripts/start.sh .
RUN chmod +x ./scripts/start.sh

CMD ["./scripts/start.sh"]