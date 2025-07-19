# Joplin to Hexo Exporter

A Python script to export notes from the Joplin note-taking application and format them as blog posts for the Hexo static site generator.

This script handles note content, front-matter generation (for title, dates, and categories), and linked resources like images, ensuring a smooth workflow from your notes to your blog.

## Features

- **Command-Line Options**: Configure the export tag and output directory directly from the command line.
- **Tag-Based Export**: Filters and exports only the Joplin notes that have a specific tag (e.g., "blog"). Can also be configured to export all notes.
- **Clean Build Process**: Wipes the output directories before each run to ensure the Hexo posts are always a perfect mirror of the source Joplin notes.
- **Stable Filenames**: Uses the unique Joplin note ID as the filename for each post, preventing issues with duplicate note titles.
- **Resource Handling**: Finds all linked images within a note, downloads them, saves them to a `resources` directory, and updates the links in the markdown file to point to the local copies.
- **Category Generation**: Automatically creates a `categories` list in the front-matter based on the note's parent notebook hierarchy in Joplin (e.g., `[Parent Notebook, Child Notebook]`).


## Current Limitations
- **Images Only**: The script currently only processes and downloads linked images (`![](:/resource_id)`). Other attached files (like PDFs or text files) will not be processed.

## Prerequisites

- **Python 3**
- **Joplin Desktop Application**: The script communicates with Joplin via its Web Clipper API.
- **An existing Hexo project**: You should have a Hexo site set up.

## Installation & Setup

1.  **Clone or Download**:
    Get the script (`joplin_to_hexo.py`) and `requirements.txt` file, and place them in a directory of your choice.

2.  **Set up a Python Virtual Environment** (Recommended):
    ```bash
    # Create a virtual environment
    python -m venv venv

    # Activate it
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    The required Python packages are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Enable Joplin Web Clipper API**:
    - In the Joplin desktop app, go to **Tools > Options > Web Clipper**.
    - Click **"Enable the Web Clipper Service"**. The API server will start.
    - Under "Advanced Options", you will see your **Authorization Token**. You will need this for the first run.

## Usage

1.  **Run the script** from your terminal. You can use command-line options to customize the run.

    **Basic usage (uses default values):**
    ```bash
    python joplin_to_hexo.py
    ```

    **With options:**
    ```bash
    # Export notes tagged with "tech-review" to a directory named "my-blog"
    python joplin_to_hexo.py --tag "tech-review" --output "my-blog"

    # Export all notes
    python joplin_to_hexo.py --tag "ALL"
    ```

    **Command-Line Arguments:**
    - `-t`, `--tag`: The tag name to filter by. Defaults to `"blog"`. Use `"ALL"` to export all notes.
    - `-o`, `--output`: The directory where the Hexo `source` folder will be generated. Defaults to `"hexo_source"`.

2.  **First-Time Setup (Token)**:
    - If this is your first time running the script, it will not find a `joplin_token.txt` file.
    - It will prompt you to paste your Joplin API token into the terminal.
    - Once you provide the token, the script will save it to `joplin_token.txt` so you don't have to enter it again.
    - **Important**: Add `joplin_token.txt` to your `.gitignore` file to prevent accidentally committing your secret token to version control.

## Recommended Workflow

For maximum safety and control, it is recommended to use this script in a separate folder, not directly inside your Hexo project's root directory.

1.  Run the script in its own folder. It will generate an output directory (e.g., `hexo_source`).
2.  **Always back up** your existing Hexo `source/_posts` and `source/resources` folders before copying new files.
3.  Manually inspect the generated files in the script's output directory to ensure they are correct.
4.  Copy the generated posts and resources into your actual Hexo project's `source/_posts` and `source/resources` directories, overwriting the old content.
5.  Run your standard Hexo commands (`hexo generate`, `hexo server`, etc.) to build and preview your site.

## TODO
[] Support links to Joplin notes in a Joplin note


## Acknowledgements

-   This script relies heavily on the excellent [**Joppy**](https://github.com/marph91/joppy) library for all its interactions with the Joplin API. Many thanks to the creators of Joppy for their great work.
-   Inspiration was also drawn from [**mark-magic**](https://github.com/mark-magic/mark-magic), a more versatile and powerful NodeJS-based tool. This Python version was created to provide an alternative with a different set of default behaviors and to be more accessible for those more familiar with the Python ecosystem.
