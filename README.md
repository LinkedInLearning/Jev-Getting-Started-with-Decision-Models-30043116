# Jev: Getting Started with Decision Models
This is the repository for the LinkedIn Learning course `Jev: Getting Started with Decision Models`. The full course is available from [LinkedIn Learning][lil-course-url].

The `02_01b` branch contains **RoleMatch**, a working LLM starter for matching resume evidence against a job description. Start with [README_APP.md](README_APP.md) for the quick setup. Jev is added during the lesson using the [Codex prompt](prompts/video-04-codex-prompt.md). Detailed application notes are in [GETTING_STARTED.md](GETTING_STARTED.md).

No OpenAI or OpenRouter key? Choose the [Jev-only prompt](prompts/video-04-jev-only-prompt.md). It replaces the LLM integration and requires only a TypeSafe key.

![lil-thumbnail-url]

## Course Description

_See the readme file in the main branch for updated instructions and information._
## Instructions
This repository has branches for each of the videos in the course. You can use the branch pop up menu in github to switch to a specific branch and take a look at the course at that stage, or you can add `/tree/BRANCH_NAME` to the URL to go to the branch you want to access.

## Branches
The branches are structured to correspond to the videos in the course. The naming convention is `CHAPTER#_MOVIE#`. As an example, the branch named `02_03` corresponds to the second chapter and the third video in that chapter. 
Some branches will have a beginning and an end state. These are marked with the letters `b` for "beginning" and `e` for "end". The `b` branch contains the code as it is at the beginning of the movie. The `e` branch contains the code as it is at the end of the movie. The `main` branch holds the final state of the code when in the course.

When switching from one exercise files branch to the next after making changes to the files, you may get a message like this:

    error: Your local changes to the following files would be overwritten by checkout:        [files]
    Please commit your changes or stash them before you switch branches.
    Aborting

To resolve this issue:
	
    Add changes to git using this command: git add .
	Commit changes using this command: git commit -m "some message"

## Installing
1. Install Python 3.12 and [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone branch `02_01b`, then run `uv sync --locked`.
3. Copy `.env.example` to `.env`. Choose [Jev only or comparison](README_APP.md#2-choose-your-setup) for the required keys and Codex prompt.
4. Run `uv run streamlit run app.py` and open [localhost:8501](http://localhost:8501).

The app includes three editable job descriptions, five fictional PDF resumes, and a live LLM matching workflow. Upload the PDFs from `output/pdf/resumes/` to see evidence scores and applicant answers. Supporting analysis stays collapsed below the answers. See [GETTING_STARTED.md](GETTING_STARTED.md) for the recording workflow and later Jev integration.

## Instructor

Instructor name

Instructor description

                            

Check out my other courses on [LinkedIn Learning](https://www.linkedin.com/learning/instructors/).


[0]: # (Replace these placeholder URLs with actual course URLs)

[lil-course-url]: https://www.linkedin.com/learning/
[lil-thumbnail-url]: https://media.licdn.com/dms/image/v2/D4E0DAQG0eDHsyOSqTA/learning-public-crop_675_1200/B4EZVdqqdwHUAY-/0/1741033220778?e=2147483647&v=beta&t=FxUDo6FA8W8CiFROwqfZKL_mzQhYx9loYLfjN-LNjgA

