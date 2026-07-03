# Safepay Payments 2.0 API

The Payments 2.0 API provides robust endpoints for querying and retrieving payment session data (trackers). It is commonly used for reconciliation, reporting, and building external data pipelines or AI embeddings of payment sessions.

## Authentication

For server-to-server communication, the Payments 2.0 API supports two primary authentication methods:

1. **Merchant Secret Key**: Pass the secret key in a custom header:
   `X-SFPY-MERCHANT-SECRET: <your_secret_key>`
2. **JWT / Time-Based Token**: Pass the token in the standard Authorization header:
   `Authorization: Bearer <your_token>`

---

## API Reference

### 1. Fetch Payment

**Path:** `/reporter/api/v2/payments/{tracker}`
**Method:** `GET`
**Description:** Retrieves the full details of a specific payment tracker session.

#### Request Body Schema
*This is a GET request; no JSON body is required.*

#### Example Request
```http
GET /reporter/api/v2/payments/track_f865abdd-3a61-4842-8000-1cffa38f1fbc HTTP/1.1
Host: sandbox.api.getsafepay.com
X-SFPY-MERCHANT-SECRET: sec_a7cc6fc1-088d-4f35-9dac-2bab2cb234a1
```

#### Example Response
```json
{
  "ok": true,
  "data": {
    "token": "track_f865abdd-3a61-4842-8000-1cffa38f1fbc",
    "environment": "sandbox",
    "state": "TRACKER_STARTED",
    "intent": "CYBERSOURCE",
    "mode": "payment",
    "entry_mode": "raw",
    "metadata": {
      "source": {
        "token": "meta_f6d863ed-9480-41cd-964f-75e73ae23d10",
        "tracker": "track_f865abdd-3a61-4842-8000-1cffa38f1fbc",
        "key": "source",
        "value": "quicklinks",
        "created_at": {
          "seconds": 1779194977
        },
        "updated_at": {
          "seconds": 1779194977
        }
      }
    }
  }
}
```

### 2. Search Payments

**Path:** `/reporter/api/v2/payments`
**Method:** `GET`
**Description:** Searches and filters payment trackers based on query parameters (e.g., states, limits, pagination, intents).

#### Request Body Schema
*This is a GET request; no JSON body is required. Filters are passed as URL query parameters.*

#### Example Request
```http
GET /reporter/api/v2/payments?limit=5&page=1&direction=DESC&states[0]=TRACKER_ENDED&modes[0]=payment HTTP/1.1
Host: sandbox.api.getsafepay.com
X-SFPY-MERCHANT-SECRET: sec_a7cc6fc1-088d-4f35-9dac-2bab2cb234a1
```

#### Example Response
```json
{
  "ok": true,
  "data": {
    "count": 798,
    "list": [
      {
        "token": "track_0b3bb4d0-2076-4300-8257-4aac58dba94f",
        "environment": "sandbox",
        "client": {
          "token": "client_31fd0356-00fd-4830-8178-8222913901e4",
          "api_key": "sec_a7cc6fc1-088d-4f35-9dac-2bab2cb234a1",
          "name": "Hassans Test Store",
          "email": "hzaidi@getsafepay.com"
        },
        "customer": {
          "token": "cus_f2cd94a0-8a9d-4fc7-876a-f07de76f2327",
          "first_name": "ALEX",
          "last_name": "GARCIA",
          "email": "aghdez@dlocal.com",
          "phone": "+924832696760",
          "type": 2
        },
        "state": "TRACKER_ENDED",
        "intent": "CYBERSOURCE",
        "mode": "payment",
        "currency": "PKR",
        "display_amount": "5.00",
        "metadata": {
          "order_id": "13825076"
        },
        "created_at": {
          "seconds": 1778858838
        },
        "charge": {
          "token": "ch_a58eae79-d506-480c-b045-66dee1cb204b",
          "is_discounted": false,
          "gross": "5.00",
          "net": "4.84",
          "is_fees_included": false
        },
        "risk": {
          "token": "risk_2a902d34-2a8a-41d1-a165-e2ff12b6a737",
          "score": "38"
        },
        "is_routed": false
      }
    ],
    "meta": {
      "limit": 5,
      "page": 1,
      "offset": 0,
      "sort_by": "created_at",
      "direction": "DESC",
      "pit_id": "zailBAEQc2FuZGJveC1wYXltZW50cxZMSThZOThIRFRlR3hCVlBUWTVvQ2tRAAEWUVhWWnVIX0ZRYTZpc1lfenVYQ2d0ZwABAAAAAABeKh4WY2kwNTJ5c0VTTzJVZEl3Ry1kUXFNdwABFkxJOFk5OEhEVGVHeEJWUFRZNW9Da1EAAA=="
    }
  }
}
```

---

## Data Schemas

### Payment Session (Tracker) Object

Defines the fields returned for a payment session.

| Field | Type | Description |
| :--- | :--- | :--- |
| `token` | `string` | The unique identifier for the payment session/tracker (starts with `track_`). |
| `environment` | `string` | The operating environment (e.g., `sandbox`, `production`). |
| `state` | `string` | The current status of the payment session (e.g., `TRACKER_STARTED`, `TRACKER_ENDED`, `TRACKER_REFUNDED`). |
| `intent` | `string` | The payment gateway intent (e.g., `CYBERSOURCE`). |
| `mode` | `string` | The checkout mode (e.g., `payment`, `subscription`, `unscheduled_cof`). |
| `currency` | `string` | The currency code for the payment (e.g., `PKR`). |
| `display_amount` | `string` | Formatted transaction amount. |
| `metadata` | `object` | Key-value pairs of custom data associated with the tracker (e.g., `order_id`, `source`). |
| `created_at` | `object` | Timestamp of creation (contains `seconds` unix timestamp). |
| `is_routed` | `boolean` | Indicates if the transaction was intelligently routed. |
| `client` | `object` | Optional nested object containing `token`, `api_key`, `name`, and `email` of the merchant. |
| `customer` | `object` | Optional nested object containing `token`, `first_name`, `last_name`, `email`, `phone`, and `type`. |
| `charge` | `object` | Optional nested object containing final billing data: `token`, `is_discounted`, `gross`, `net`, and `is_fees_included`. |
| `risk` | `object` | Optional nested object containing fraud analysis metrics (e.g., `token`, `score`). |
