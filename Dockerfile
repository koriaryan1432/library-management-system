# ─────────────────────────────────────────────
# Stage: Python 3.12 slim base
# ─────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install dependencies first (layer caching — only re-runs if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project into container
COPY . .

# Expose the Flask port
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]
