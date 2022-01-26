"""
This app contains code to take a GitHub markdown file and convert it to a blog posts
on platforms such as dev.to
"""
import os

from dev_to import post_to_dev_to, ReadmeParseError
from github_access import GitHubAccess

# Get the DEV.to API key
# This can be created from your Dev.to settings by following these instructions:
# https://developers.forem.com/api/#section/Authentication
DEV_TO_API_KEY = os.environ['DEV_TO_API_KEY']

# Get the DEV.to Organization if needed
# This is used to post under different organizations
# If this is not set, the article is posted to the user only
DEV_TO_ORGANIZATION_ID = os.getenv('DEV_TO_ORGANIZATION_ID', None)

# Get the GitHub API key
# This is a personal access token with access to the Reactor repo
GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']

# Get the repo location
REPO = os.environ['REPO']

# Connect to GitHub
gh = GitHubAccess(REPO, GITHUB_ACCESS_TOKEN)
post_folders = gh.get_post_folders()

print(f'Processing post pages from {REPO}')

# Iterate through all the post pages in the repo
for post_page in post_folders:
    # Check if the page is outdated. If so, build a post.
    if post_page.is_outdated:
        try:
            print(f'Processing {post_page}')

            post_to_dev_to(post_page, DEV_TO_API_KEY, DEV_TO_ORGANIZATION_ID)

            # Update the details in the post folder
            print('Updating the post page in GitHub...')
            post_page.commit_changes()

        except ReadmeParseError as ex:
            # If this fails then maybe the README isn't correctly formed.
            # Report and re-raise the error
            error_message = f'Failed to parse the README file {post_page.root_folder.path} to create a Dev.to blog post\nException: {ex}'
            print(error_message)
            raise ReadmeParseError(error_message) from ex
    else:
        print(f'{post_page} - no changes')
