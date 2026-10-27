# Choose the right question type

Choose the first tool for an API-pricing research request in the [TypeSafe playground](https://console.typesafe.ai/playground).

1. Copy the JSON in [State](#state) into **State**.
2. Copy **Choice** under [Questions](#questions) into **Questions**. Select **Run request**.
3. Replace **Questions** with **Choice and Noul**. Run again.
4. Replace **Questions** with **Choice, Noul, and Score**. Run again.

Keep the same state for all three runs.

## State

```json
{
  "prompt": "Find the latest API pricing for three AI providers and compare their costs."
}
```

## Questions

### 1. Choice

Paste this entire block into **Questions**.

```json
{
  "tool use": {
    "type": "choice",
    "instructions": "Which tool should the agent use first?",
    "criteria": {
      "Web Search": "Find the current public information.",
      "Calculator": "Perform calculations",
      "File Search": "Search uploaded documents"
    }
  }
}
```

### 2. Choice and Noul

Replace **Questions** with this entire block. Keep the same state.

```json
{
  "tool use": {
    "type": "choice",
    "instructions": "Which tool should the agent use first?",
    "criteria": {
      "Web Search": "Find the current public information.",
      "Calculator": "Perform calculations",
      "File Search": "Search uploaded documents"
    }
  },
  "external source requirement": {
    "type": "noul",
    "instructions": "Does this request require current information from external sources?",
    "criteria": {
      "true": "",
      "false": ""
    }
  }
}
```

### 3. Choice, Noul, and Score

Replace **Questions** with this entire block. Keep the same state.

```json
{
  "tool use": {
    "type": "choice",
    "instructions": "Which tool should the agent use first?",
    "criteria": {
      "Web Search": "Find the current public information.",
      "Calculator": "Perform calculations",
      "File Search": "Search uploaded documents"
    }
  },
  "external source requirement": {
    "type": "noul",
    "instructions": "Does this request require current information from external sources?",
    "criteria": {
      "true": "",
      "false": ""
    }
  },
  "workload": {
    "type": "score",
    "instructions": "How much work does this request require?",
    "criteria": [
      "One lookup",
      "Multiple lookup",
      "Multiple lookup + calculation + comparison"
    ]
  }
}
```
