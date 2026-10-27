# Ask Jev your first questions

Route a support ticket and assess its urgency in the [TypeSafe playground](https://console.typesafe.ai/playground).

1. Copy the JSON in [State](#state) into **State**.
2. Copy **Choice** under [Questions](#questions) into **Questions**. Select **Run request**.
3. Replace **Questions** with **Choice and Score**. Run again with the same state.

## State

```json
{
  "customer_support_ticket": "I was charged twice."
}
```

## Questions

### 1. Choice

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

### 2. Choice and Score

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
