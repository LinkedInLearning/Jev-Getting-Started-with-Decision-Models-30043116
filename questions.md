# Questions

## 1. Choice

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

## 2. Choice and Noul

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

## 3. Choice, Noul, and Score

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
