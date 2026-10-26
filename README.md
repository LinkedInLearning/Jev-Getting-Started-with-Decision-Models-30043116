# RoleMatch

Review resume evidence against a job description.

Select or edit a role, upload applications, and compare the evidence for each requirement.
Answers include source references, request cost, and timing.

## Install

Install [Git](https://git-scm.com/downloads) and [uv](https://docs.astral.sh/uv/getting-started/installation/).
The project uses Python 3.12.

```bash
git clone --branch 02_01b https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116.git
cd Jev-Getting-Started-with-Decision-Models-30043116
uv sync --locked
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env` for the last command.
Keep an existing `.env` when returning to the project.

## Configure an engine

The app currently uses an LLM with structured outputs.
For OpenRouter, add your key to `.env`:

```dotenv
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4.1-mini
OPENROUTER_API_KEY=your-own-key
```

For OpenAI directly, set `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4.1-mini`, and `OPENAI_API_KEY`.
Keys stay in the local environment file.

### Optional Jev integration

Open this repository in Codex and choose one prompt:

| Setup | Required keys | Prompt |
| --- | --- | --- |
| Replace the LLM with Jev | TypeSafe only | [Connect Jev](prompts/jev-only.md) |
| Compare LLM and Jev results | OpenRouter or OpenAI, plus TypeSafe | [Compare engines](prompts/compare-engines.md) |

Both prompts link to the Jev documentation and implementation requirements.
Jev support becomes available after the selected integration is implemented.
Set `TYPESAFE_API_KEY` in `.env` and follow the updated setup instructions.

You can install and open the app without an LLM key.
Analysis requires a configured engine.
The Jev-only option removes the LLM dependency and its key requirement.

## Run

```bash
uv run streamlit run app.py
```

Open [localhost:8501](http://localhost:8501).
Keep the terminal running.
Restart the app after changing environment settings or dependencies.

## Review applications

1. Select **Python Backend Engineer** on the left.
2. Edit the job description and matching criteria if needed.
3. Upload the five PDFs from [output/pdf/resumes](output/pdf/resumes/).
4. Select **Analyze applications**.
5. Select an applicant to read the answers.
6. Expand **Analysis details** for evidence, cost, timing, and exports.

The [resume bundle](output/pdf/applicant-resumes.zip) contains five fictional applications.
Two other job descriptions are also built in.

Evidence match counts criteria with direct supporting evidence.
It is not a probability of job fit or a hiring recommendation.

See [application details](GETTING_STARTED.md) for scoring, measurements, file limits, and checks.
