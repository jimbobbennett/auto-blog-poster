"""
This app contains code to take a GitHub markdown file and convert it to a Dev.to post
"""
import os

from dotenv import load_dotenv

from dev_to import post_to_dev_to, ReadmeParseError
from github_access import GitHubAccess

# Load environment variables - this includes GitHub API kets and dev.to API keys
load_dotenv()

# Get the DEV.to API key
# This can be created from your Dev.to settings by following these instructions:
# https://developers.forem.com/api/#section/Authentication
DEV_TO_API_KEY = os.environ['DEV_TO_API_KEY']

# Get the DEV.to Organization if needed
# This is used to post under different organizations
DEV_TO_ORGANIZATION_ID = os.environ['DEV_TO_ORGANIZATION_ID']

# Get the GitHub API key
# This is a personal access token with access to the Reactor repo
GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

# Get the repo location
REPO = os.environ['REPO']

# Connect to GitHub
gh = GitHubAccess(REPO, GITHUB_ACCESS_TOKEN)
series_folders = gh.get_series_folders()

print(f'Processing series pages from {REPO}')

# Iterate through all the series pages in the repo
for series_page in series_folders:
    # Check if the page is outdated. If so, build a post.
    if series_page.is_outdated:
        try:
            print(f'Processing {series_page}')

            post_to_dev_to(series_page, DEV_TO_API_KEY, DEV_TO_ORGANIZATION_ID) 

            # Update the details in the series folder
            print('Updating the series page in GitHub...')
            series_page.commit_changes()

        except ReadmeParseError as ex:
            # If this fails then maybe the README isn't correctly formed.
            # Report and re-raise the error
            error_message = f'Failed to parse the README file {series_page.root_folder.path} to create a Dev.to blog post\nException: {ex}'
            print(error_message)
            raise ReadmeParseError(error_message) from ex
    else:
        print(f'{series_page} - no changes')
