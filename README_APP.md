# Run the ATS application

Start here for Video 4. Branch `02_01b` contains the working **LLM-only** application.

## 1. Clone and select the branch

Install [Git](https://git-scm.com/downloads), Python 3.12, and [uv](https://docs.astral.sh/uv/getting-started/installation/) first.

```bash
git clone https://github.com/LinkedInLearning/Jev-Getting-Started-with-Decision-Models-30043116.git
cd Jev-Getting-Started-with-Decision-Models-30043116
git switch 02_01b
uv sync --locked
```

Already cloned the repository? Open its folder, fetch the latest branches with `git fetch origin`, then switch to `02_01b`.

## 2. Configure the LLM

For the first setup, copy the example file:

```bash
cp .env.example .env
```

In Windows PowerShell, use `Copy-Item .env.example .env`.

Open `.env` in your editor. Add your [OpenRouter API key](https://openrouter.ai/settings/keys):

```dotenv
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4.1-mini
OPENROUTER_API_KEY=your-own-key
```

Keep an existing `.env` when returning to the project. Do not copy the example over your keys.

## 3. Start the app

```bash
uv run streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501). Keep the terminal running.

If that port is busy, use `uv run streamlit run app.py --server.port 8502`, then open [http://localhost:8502](http://localhost:8502).

## 4. Run your first analysis

1. Select **Python Backend Engineer** on the left.
2. Upload all five PDFs from `output/pdf/resumes/` on the right.
3. Select **Analyze applications**.
4. Select an applicant to read the answers.
5. Expand **Analysis details** to inspect evidence, cost, and time.
6. Select **Export analysis** to save the LLM baseline.

The PDFs are fictional course applications. Evidence match counts criteria with direct supporting evidence. It is not a probability of job fit.

## 5. Add Jev during the lesson

Open this repository folder in Codex. Use the [short recording prompt](prompts/video-04-codex-prompt.md).

The prompt asks Codex to read the [official Jev documentation](https://docs.typesafe.ai/llms.txt), add a second matching engine, and build a side-by-side comparison.

After Codex adds the integration, set `TYPESAFE_API_KEY` in `.env` using a key from the [TypeSafe console](https://console.typesafe.ai). Follow the generated setup instructions, then restart Streamlit.

The requested engine menu is **LLM structured output**, **Jev**, and **Compare both**. These options become available after the integration is implemented. They are not included in this starter.

Use **Compare both** on the unchanged job and PDFs. Inspect answers, cost, time, and disagreements together.

For details, see [GETTING_STARTED.md](GETTING_STARTED.md). The [video guide](lessons/04-working-application/script.html) contains the recording flow.
