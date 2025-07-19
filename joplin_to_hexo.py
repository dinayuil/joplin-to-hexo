import os
import re
import json
import shutil
import argparse
from datetime import datetime
from joppy.client_api import ClientApi
from joppy.data_types import NoteData, NotebookData
from typing import List, Dict, Optional

# --- CONFIGURATION ---
# 1. Get your Joplin API Token:
#    - In Joplin, go to: Tools > Options > Web Clipper
#    - Enable the Web Clipper Service.
#    - Under "Advanced Options", you will find the authorization token.
TOKEN_FILE = "joplin_token.txt"

# 4. Define the standard Hexo directory names.
POSTS_DIR_NAME = "source/_posts"
RESOURCES_DIR_NAME = "source/resources" 


# --- SCRIPT ---

def get_joplin_token() -> str:
    """
    Gets the Joplin API token.
    First, it tries to read the token from TOKEN_FILE.
    If the file doesn't exist, it prompts the user to enter the token
    and saves it to the file for future use.
    """
    if os.path.exists(TOKEN_FILE):
        print(f"Reading Joplin token from {TOKEN_FILE}...")
        with open(TOKEN_FILE, 'r') as f:
            token = f.read().strip()
        if token:
            return token
        else:
            print(f"Warning: {TOKEN_FILE} is empty.")

    print("\n--- Joplin API Token Setup ---")
    print("Your Joplin API token is required to connect to the Joplin application.")
    print("You can find it in Joplin under: Tools > Options > Web Clipper.")
    print("Ensure the Web Clipper Service is ENABLED.")
    
    token = ""
    while not token:
        token = input("Please paste your Joplin API token here and press Enter: ").strip()
        if not token:
            print("Token cannot be empty. Please try again.")

    try:
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        print(f"Token saved to {TOKEN_FILE} for future use.")
    except IOError as e:
        print(f"Warning: Could not save token to file. Reason: {e}")
    
    return token


def clean_output_directories(posts_dir: str, resources_dir: str):
    """
    Deletes and recreates the Hexo posts and resources directories for a clean build.
    """
    print("\n--- Cleaning Output Directories ---")
    for dir_path in [posts_dir, resources_dir]:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"Successfully deleted directory: {dir_path}")
            except OSError as e:
                print(f"Error deleting directory {dir_path}: {e}")
                return False
    
    print("Recreating directories...")
    os.makedirs(posts_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)
    print("Directories are clean and ready.")
    return True


def sanitize_filename(name: str) -> str:
    """
    Removes invalid characters from a string so it can be used as a filename,
    while preserving Unicode characters like Chinese.
    """
    # Replace spaces with hyphens for URL-friendliness
    name = name.replace(" ", "-")
    # Remove characters that are invalid in filenames on most OSes.
    # This includes: / \ : * ? " < > |
    sanitized_name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Also remove control characters
    sanitized_name = re.sub(r'[\x00-\x1f\x7f]', '', sanitized_name)
    # Filenames cannot end with a space or a dot on Windows.
    sanitized_name = sanitized_name.strip(' .')
    # If the name is empty after sanitization (unlikely), provide a fallback.
    if not sanitized_name:
        return "untitled-note"
    return sanitized_name

def get_category_hierarchy(start_notebook_id: str, notebooks_map: Dict[str, NotebookData]) -> List[str]:
    """
    Traverses the notebook hierarchy upwards to build a list of categories.
    """
    categories = []
    current_id = start_notebook_id
    while current_id and current_id in notebooks_map:
        notebook = notebooks_map[current_id]
        # Prepend title to get the correct order [Parent, Child]
        categories.insert(0, notebook.title)
        current_id = notebook.parent_id
    return categories


def remove_outer_braces(text):
  """
  Removes surrounding curly braces {} from a string in a safe way.
  """
  # Remove leading/trailing whitespace first
  stripped_text = text.strip()

  # Check if the string starts with '{' and ends with '}'
  if stripped_text.startswith('{') and stripped_text.endswith('}'):
    # If it does, return the content inside the braces
    return stripped_text[1:-1]
  
  # Otherwise, return the original (stripped) text
  return stripped_text


def process_note(api: ClientApi, note: NoteData, posts_dir: str, resources_dir: str, notebooks_map: Dict[str, NotebookData]):
    """
    Processes a single note: creates front-matter, downloads resources,
    updates markdown links, and saves the complete Hexo post.
    """
    if not note.title or not note.body:
        print(f"Skipping note with ID {note.id} because it has no title or body.")
        return

    print(f"Processing note: '{note.title}'")

    # --- Process Note Body and Resources ---
    new_body = note.body
    resource_links = re.findall(r'!\[.*?\]\(:\/([a-f0-9]{32})\)', note.body)

    if resource_links:
        print(f"  Found {len(resource_links)} image(s) in this note.")

    for resource_id in resource_links:
        try:
            resource_meta = api.get_resource(resource_id, fields="id,title,filename,mime")
            original_filename = resource_meta.filename or resource_meta.title or ""
            _, extension = os.path.splitext(original_filename)
            if not extension:
                extension = ".png"

            new_resource_filename = f"{resource_id}{extension}"
            local_image_path = os.path.join(resources_dir, new_resource_filename)

            if not os.path.exists(local_image_path):
                print(f"  Downloading resource: {new_resource_filename}...")
                resource_file_content = api.get_resource_file(resource_id)
                with open(local_image_path, 'wb') as f:
                    f.write(resource_file_content)
            
            new_image_path_in_md = f"/resources/{new_resource_filename}"
            old_link = f"(:/{resource_id})"
            new_link = f"({new_image_path_in_md})"
            new_body = new_body.replace(old_link, new_link)
        except Exception as e:
            print(f"  ERROR: Could not process resource {resource_id}. Reason: {e}")

    # --- Create Front-matter in JSON format ---
    if note.user_created_time:
        date_str = note.user_created_time.strftime('%Y-%m-%d %H:%M:%S') 
    elif note.created_time:
        date_str = note.created_time.strftime('%Y-%m-%d %H:%M:%S') 
    else:
        print(f"  WARNING: No creation time found for note id {note.id}, title {note.title}. Using current time.")
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    updated_str = note.updated_time.strftime('%Y-%m-%d %H:%M:%S') if note.updated_time else date_str

    front_matter_dict = {
        "title": note.title,
        "date": date_str,
        "updated": updated_str,
    }

    if note.parent_id:
        categories = get_category_hierarchy(note.parent_id, notebooks_map)
        if categories:
            front_matter_dict["categories"] = categories

    # Use json.dumps for robust handling of special characters.
    # `indent=2` makes it readable, `ensure_ascii=False` preserves Unicode chars.
    json_str = json.dumps(front_matter_dict, indent=2, ensure_ascii=False)
    json_str = remove_outer_braces(json_str)
    front_matter_str = f";;;{json_str}\n;;;\n\n"

    # --- Combine and Save ---
    final_content = front_matter_str + new_body
    # Use the unique note ID as the filename to avoid conflicts with duplicate titles.
    # The note title is still used in the front-matter for the post's display title.
    post_slug = note.id 
    markdown_filename = f"{post_slug}.md"
    markdown_filepath = os.path.join(posts_dir, markdown_filename)
    
    with open(markdown_filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"  Successfully saved markdown to: {markdown_filepath}\n")

def main():
    """
    Main function to run the Joplin to Hexo export process.
    """
    parser = argparse.ArgumentParser(description="Export notes from Joplin to Hexo posts.")
    parser.add_argument(
        "-t", "--tag",
        default="blog",
        help="The tag name of notes to export. Use 'ALL' to export all notes. Default: 'blog'."
    )
    parser.add_argument(
        "-o", "--output",
        default="hexo_source",
        help="The base directory for your Hexo source files. Default: 'hexo_source'."
    )
    args = parser.parse_args()
    
    target_tag_name: Optional[str] = None if args.tag.upper() == 'ALL' else args.tag
    output_dir = args.output

    joplin_token = get_joplin_token()
    if not joplin_token:
        print("Could not obtain Joplin API token. Exiting.")
        return

    print("\n--- Starting Joplin to Hexo Export ---")
    
    try:
        api = ClientApi(token=joplin_token)
        api.ping()
        print("Successfully connected to Joplin API.")
    except Exception as e:
        print(f"Error connecting to Joplin API: {e}")
        print("Please ensure Joplin is running and the Web Clipper service is enabled.")
        return

    # --- Fetch Notes ---
    note_fields = "id,title,body,parent_id,user_created_time,updated_time"
    notes_to_process = []
    
    if target_tag_name:
        try:
            print(f"Looking for tag: '{target_tag_name}'...")
            tags = api.get_all_tags(fields="id,title")
            target_tag = next((tag for tag in tags if tag.title == target_tag_name), None)
            if not target_tag:
                print(f"Error: Tag '{target_tag_name}' not found.")
                return
            print("Found tag. Fetching associated notes...")
            notes_to_process = api.get_all_notes(tag_id=target_tag.id, fields=note_fields)
        except Exception as e:
            print(f"An error occurred while fetching notes for tag '{target_tag_name}': {e}")
            return
    else:
        print("No target tag specified. Fetching all notes...")
        try:
            notes_to_process = api.get_all_notes(fields=note_fields)
        except Exception as e:
            print(f"An error occurred while fetching all notes: {e}")
            return

    if not notes_to_process:
        print("No notes found in Joplin with the specified criteria. Nothing to do.")
        return
    
    print(f"\nFound {len(notes_to_process)} notes in Joplin to process.")

    # --- Fetch Notebooks for Category Mapping ---
    print("Fetching all notebooks for category lookup...")
    all_notebooks = api.get_all_notebooks(fields="id,title,parent_id")
    notebooks_map = {nb.id: nb for nb in all_notebooks if nb.id}

    # --- Clean and Create Directories ---
    posts_dir = os.path.join(output_dir, POSTS_DIR_NAME)
    resources_dir = os.path.join(output_dir, RESOURCES_DIR_NAME)
    if not clean_output_directories(posts_dir, resources_dir):
        print("Failed to clean directories. Aborting.")
        return
    
    # --- Process Notes ---
    print(f"\nStarting processing of {len(notes_to_process)} notes...")
    print(f"Posts will be saved to: {posts_dir}")
    print(f"Images will be saved to: {resources_dir}\n")
    
    for note in notes_to_process:
        process_note(api, note, posts_dir, resources_dir, notebooks_map)

    print("\n--- Export finished! ---")


if __name__ == "__main__":
    main()
