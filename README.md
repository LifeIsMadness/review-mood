```bash
pip install flask==3.0.3
python app.py
```

## Examples

### POST /reviews

```bash
curl -X POST http://127.0.0.1:5000/reviews \
  -H "Content-Type: application/json" \
  -d '{"text": "Очень хороший сервис!"}'
```

**Response:**
```json
{
  "id": 1,
  "text": "Очень хороший сервис!",
  "sentiment": "positive",
  "created_at": "2025-07-28T11:24:00.123456"
}
```

### GET /reviews?sentiment=positive

```bash
curl http://127.0.0.1:5000/reviews?sentiment=positive
```

**Response:**
```json
[
  {
  "id": 1,
  "text": "Очень хороший сервис!",
  "sentiment": "positive",
  "created_at": "2025-07-28T11:24:00.123456"
  }
]
```
