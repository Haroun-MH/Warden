# Warden Project

This project, inspired by Mr. Chaouki Bayoudhi, is designed for log anomaly detection using Django and GraphQL.

## Requirements
- Python 3.13.1
- Django 5.2
- Other dependencies listed in `requirements.txt`

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone https://github.com/Haroun-MH/Warden.git
   cd Warden
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Apply Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Run the Development Server**
   ```bash
   python manage.py runserver
   ```

5. **Start Celery Worker and Beat**
   ```bash
   celery -A warden worker --loglevel=info
   celery -A warden beat --loglevel=info
   ```

## API Endpoints
- **Log Entries**
  - `GET /api/logs/`: List all log entries.
  - `POST /api/logs/`: Create a new log entry (requires HMAC signature).
  - `GET /api/logs/<id>/`: Retrieve a specific log entry.

## GraphQL Queries
- **All Log Entries**
  ```graphql
  query {
    allLogEntries {
      id
      message
      timestamp
    }
  }
  ```
- **All Anomaly Reports**
  ```graphql
  query {
    allAnomalyReports {
      id
      reason
      bertScore
    }
  }
  ```
- **Log Entries by Anomaly Score**
  ```graphql
  query {
    logEntriesByAnomalyScore(minScore: 0.5, maxScore: 1.0) {
      id
      message
    }
  }
  ```

## Generating X-Signature
To make API requests that require an HMAC signature, compute the signature using the request body and a shared secret key:
```python
import hmac
import hashlib

secret_key = 'your-super-secret-hmac-key-here'
body = b'{"key": "value"}'  # Example request body
signature = hmac.new(secret_key.encode(), body, hashlib.sha256).hexdigest()
```
Include this signature in the `X-Signature` header of your request.

## Project Idea
This project is based on the idea of Mr. Chaouki Bayoudhi, focusing on detecting anomalies in log data using advanced techniques.