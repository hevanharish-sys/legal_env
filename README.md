---
title: Legal Env
emoji: 🏢
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Legal Document Risk Analyzer (LegalEnv)

LegalEnv is a production-ready OpenEnv-style environment that simulates a legal AI assistant for contract review. It mirrors real legal-tech workflows by presenting contract clauses, asking an agent to identify the legal risk, and scoring the response based on classification accuracy, safer drafting quality, and legal reasoning quality.

## Real-World Use Case

Enterprise legal-tech platforms routinely screen contracts for risky liability caps, aggressive termination provisions, unfair payment terms, weak confidentiality controls, and overbroad compliance obligations. LegalEnv provides a deterministic benchmark for that workflow, making it useful for:

- Evaluating legal clause analysis agents
- Benchmarking LLM prompts for contract review
- Testing safer contract rewrite strategies
- Building legal AI demos, APIs, and internal evaluation pipelines

## Observation Space

Each environment observation is a Pydantic model with:

- `clause: str` - the contract clause to analyze
- `contract_type: str` - the agreement type
- `jurisdiction: str` - the relevant jurisdiction

Example observation:

```json
{
  "clause": "Company is not liable for any damages arising from use of the service.",
  "contract_type": "SaaS subscription agreement",
  "jurisdiction": "New York, USA"
}
```

## Action Space

Each agent action is a Pydantic model with:

- `risk_level: "low" | "medium" | "high"`
- `risk_type: "liability" | "termination" | "payment" | "confidentiality" | "compliance"`
- `rewrite: str`
- `reason: str`

Tasks use different subsets of this action space:

- `easy` requires `risk_type`
- `medium` requires `risk_type` and `risk_level`
- `hard` requires all fields

## Reward Explanation

The environment uses a dense deterministic reward, clipped to `[0.0, 1.0]`.

Base component weights:

- Risk Level Correct: `+0.4`
- Risk Type Correct: `+0.3`
- Rewrite Quality: `+0.2`
- Reason Quality: `+0.1`

Rewrite quality is scored by keyword coverage in the proposed rewrite using:

- `reasonable`
- `subject to law`
- `limitation`
- `exception`
- `applicable law`

Reason quality is scored by explanation terms such as:

- `risk`
- `liability`
- `unfair`
- `legal`

Penalties:

- Missing required field: `-0.2` per missing field
- Entire required response empty: additional `-0.3`

For `easy` and `medium`, the same reward weights are preserved and normalized over the fields required by that task so every task still returns a score between `0.0` and `1.0`.

## Task Design

The environment contains 15 realistic contract clauses:

- 5 `easy` clauses focused on primary risk-type recognition
- 5 `medium` clauses requiring both risk type and risk level
- 5 `hard` clauses requiring full legal analysis, rewrite, and reasoning

Covered risk categories:

- Liability
- Termination
- Payment
- Confidentiality
- Compliance

## Project Structure

```text
legal_env/
+-- models.py
+-- env.py
+-- grader.py
+-- baseline.py
+-- api.py
+-- openenv.yaml
+-- Dockerfile
+-- requirements.txt
+-- README.md
```

## Setup Instructions

From the `legal_env` directory:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## How to Run the Baseline

Set your OpenAI API key and execute the baseline agent:

```powershell
$env:OPENAI_API_KEY="your-api-key"
python baseline.py
```

The baseline:

- Uses `gpt-4o-mini`
- Sends the exact JSON-only prompt requested in the specification
- Evaluates `easy`, `medium`, and `hard`
- Prints task-level scores and an overall average score

Expected output format:

```text
easy_score=0.8000
medium_score=0.7200
hard_score=0.6100
average_score=0.7100
```

## How to Run the API

Start the FastAPI server:

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000
```

Available endpoints:

- `GET /reset?task=easy`
- `POST /step`
- `GET /state`

## Example API Usage

Reset the environment:

```http
GET /reset?task=hard
```

Example response:

```json
{
  "task": "hard",
  "observation": {
    "clause": "Company shall have no liability whatsoever, including for gross negligence, data loss, or indirect damages, under any circumstances.",
    "contract_type": "Cloud platform agreement",
    "jurisdiction": "California, USA"
  }
}
```

Submit an action:

```json
{
  "risk_level": "high",
  "risk_type": "liability",
  "rewrite": "Except to the extent prohibited by applicable law, liability is subject to a reasonable limitation with an exception for gross negligence and fraud.",
  "reason": "This clause creates legal risk because it removes liability too broadly and may be unfair."
}
```

Example `/step` response:

```json
{
  "observation": {
    "clause": "Fees are due upon invoice and are non-refundable even if the services are not delivered or are materially defective.",
    "contract_type": "Implementation services agreement",
    "jurisdiction": "England and Wales"
  },
  "reward": {
    "score": 1.0
  },
  "done": false,
  "info": {
    "task": "hard",
    "sample_id": "hard-1",
    "sample_index": 0,
    "total_samples": 5,
    "ground_truth": {
      "risk_level": "high",
      "risk_type": "liability",
      "rewrite": "Except to the extent prohibited by applicable law, Company will not be liable for indirect or consequential damages, and its aggregate liability will be subject to a reasonable limitation, with an exception for gross negligence, fraud, willful misconduct, and liabilities that cannot be limited by law.",
      "reason": "This clause creates significant legal risk because it tries to eliminate liability even for gross negligence, which may be unfair and unenforceable under applicable law."
    },
    "grading": {
      "score": 1.0,
      "task": "hard",
      "required_fields": [
        "risk_type",
        "risk_level",
        "rewrite",
        "reason"
      ],
      "missing_fields": [],
      "raw_positive": 1.0,
      "normalized_positive": 1.0,
      "penalty": 0.0,
      "breakdown": {
        "risk_level": 0.4,
        "risk_type": 0.3,
        "rewrite": 0.2,
        "reason": 0.1
      }
    }
  }
}
```

## Docker

Build and run:

```powershell
docker build -t legalenv .
docker run --rm -e OPENAI_API_KEY=$env:OPENAI_API_KEY legalenv
```

The container uses `python:3.10` and defaults to serving the FastAPI endpoints on port `7860`, which is the standard required for **Hugging Face Spaces**:

```text
uvicorn api:app --host 0.0.0.0 --port 7860
```
