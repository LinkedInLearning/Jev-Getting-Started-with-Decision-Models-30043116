# Questions

## 1. Choice

Paste this entire block into **Questions**.

```json
{
  "triage": {
    "type": "choice",
    "instructions": "Which team should handle this request?",
    "criteria": {
      "Billing": "Billing department",
      "Technical": "Engineering department",
      "Logistics": "Logistics department"
    }
  }
}
```

## 2. Choice and Score

Replace **Questions** with this entire block. Keep the same state.

```json
{
  "triage": {
    "type": "choice",
    "instructions": "Which team should handle this request?",
    "criteria": {
      "Billing": "Billing department",
      "Technical": "Engineering department",
      "Logistics": "Logistics department"
    }
  },
  "urgency": {
    "type": "score",
    "instructions": "How urgent is this support ticket?",
    "criteria": [
      "Not very urgent",
      "Moderately urgent",
      "Severe"
    ]
  }
}
```
