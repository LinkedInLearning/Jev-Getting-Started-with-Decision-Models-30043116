# Run the ATS application

Start here for Video 4. Branch `02_01b` contains the LLM starter. You can use Codex to add Jev with a comparison, or replace the LLM entirely.

## 1. Clone and select the branch

Install [Git](https://git-scm.com/downloads), Python 3.12, and [uv](https://docs.astral.sh/uv/getting-started/installation/) first.

```bash
git clone https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116.git
cd Jev-Getting-Started-with-Decision-Models-30043116
git switch 02_01b
uv sync --locked
```

Already cloned the repository? Open its folder, fetch the latest branches with `git fetch origin`, then switch to `02_01b`.

## 2. Choose your setup

| What you want | Keys needed | Prompt to use in Codex |
| --- | --- | --- |
| Connect Jev without an LLM | TypeSafe key only | [Jev-only prompt](prompts/video-04-jev-only-prompt.md) |
| Compare the LLM and Jev | OpenRouter or OpenAI key, plus a TypeSafe key | [Comparison prompt](prompts/video-04-codex-prompt.md) |

You do not need an OpenAI or OpenRouter key to clone the repo or open the interface. Analysis needs a configured engine. Jev support is added by the chosen prompt during the lesson.

For the first setup, copy the example file:

```bash
cp .env.example .env
```

In Windows PowerShell, use `Copy-Item .env.example .env`. Keep an existing `.env` when returning to the project.

### Jev only

1. Open the repository folder in Codex.
2. Copy the [Jev-only prompt](prompts/video-04-jev-only-prompt.md) into Codex.
3. Let Codex replace the LLM integration and update the setup instructions.
4. Add your [TypeSafe key](https://console.typesafe.ai) to `.env`:

```dotenv
TYPESAFE_API_KEY=your-own-jev-key
```

Leave the OpenAI and OpenRouter keys blank. Follow the generated instructions, then start the converted app. This path does not require an LLM baseline or show a comparison.

### Compare both engines

First add an [OpenRouter key](https://openrouter.ai/settings/keys) to `.env`:

```dotenv
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4.1-mini
OPENROUTER_API_KEY=your-own-key
```

Run the LLM starter and export a baseline. Then paste the [comparison prompt](prompts/video-04-codex-prompt.md) into Codex.

After the integration is added, set `TYPESAFE_API_KEY` in `.env`. Follow the generated setup instructions and restart Streamlit. Use **Compare both** to inspect paired answers, costs, time, and disagreements for the unchanged job and PDFs.

The comparison menu becomes available after that integration is implemented. It is not included in this starter.

## 3. Start the app

```bash
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501). Keep the terminal running. Restart Streamlit after Codex changes the integration or dependencies.

If that port is busy, use `uv run streamlit run app.py --server.port 8502`, then open [http://localhost:8502](http://localhost:8502).

## 4. Analyze applications

1. Select **Python Backend Engineer** on the left.
2. Upload all five PDFs from `output/pdf/resumes/` on the right.
3. Select **Analyze applications** after your chosen engine is configured.
4. Select an applicant to read the answers.
5. Expand **Analysis details** for evidence, cost, and time.
6. Select **Export analysis** to save the run.

The PDFs are fictional course applications. Evidence match counts criteria with direct supporting evidence. It is not a probability of job fit.

For details, see [GETTING_STARTED.md](GETTING_STARTED.md). The [video guide](lessons/04-working-application/script.html) contains the recording flow and both prompt options.
