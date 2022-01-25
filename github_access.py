"""
This module defines the GitHubAccess help class that is used to read and write to
a GitHub repo.
"""

import json

from github import Github, Repository
from github.ContentFile import ContentFile

def is_series_page_folder(folder: ContentFile) -> bool:
    """
    A static method to check if a file is a valid series page folder.
    A valid series page folder has a READM.md file with the series page details,
    and a subfolder called .seriespage.

    :param ContentFile folder: The folder to check

    :return: True if the folder is a valid series page folder, otherwise false
    :rtype: bool
    """

    # Get all the items in this folder as a list so it's easier to process them
    folder_contents = list(folder)

    # Check for the README.md file. This is case insensitve - although README.md is the standard,
    # we should support all casings
    readme = next(filter(lambda x: x.path.lower().endswith('readme.md'), folder_contents), None)

    # Look for the .seriespage folder as a folder (type is dir for folders)
    series_page_folder = next(filter(lambda x: x.path.lower().endswith('.seriespage') and x.type == 'dir', folder_contents), None)

    # Return if we have found a README and a .seriespage folder
    return readme is not None and series_page_folder is not None

class SeriesPageDetails:
    """
    A class that represents a series page. This tracks the folder that the series page is in,
    the README file, and the contents of the seriespage.json file
    """
    def __init__(self, repo: Repository, series_page_root_folder: ContentFile, series_page_root_folder_contents: ContentFile) -> None:
        """
        Create the details and populates it from the series page details.

        :param Repository repo: The GitHub repository
        :param ContentFile series_page_root_folder: The root folder for the series page
        :param ContentFile series_page_folder_contents: The contents of the series page folder
        """
        self.root_folder = series_page_root_folder
        self.__repo = repo

        # Find the .seriespage folder
        series_page_folder = next(filter(lambda x: x.path.lower().endswith('.seriespage') and x.type == 'dir', series_page_root_folder_contents), None)

        # Cache the contents of the README file
        readme = next(filter(lambda x: x.path.lower().endswith('readme.md'), series_page_root_folder_contents), None)

        if readme.encoding == 'base64':
            self.readme_content = readme.decoded_content.decode('utf-8')
        else:
            self.readme_content = readme.decoded_content

        # Get the sha of the readme.md file to use to compare against
        self.current_readme_sha = readme.sha

        # Get the contents of this folder to find the seriespage.JSON file
        series_page_contents = self.__repo.get_contents(series_page_folder.path)
        self.__series_page_json_file : ContentFile= next(filter(lambda x: x.path.lower().endswith('seriespage.json'), series_page_contents), None)

        # Default everything
        self.last_post_readme_sha = ''
        self.dev_to_slug = ''
        self.dev_to_article_id = ''
        series_page_details = {}

        # If this file is not found, then we don't have any blog posts
        # Otherwise, read the contents and the file date
        if self.__series_page_json_file is not None:
            # This file could be empty, so ignore any exceptions from decoding this file
            try:
                # Load the JSON from the file contents
                if self.__series_page_json_file.encoding == 'base64':
                    json_content = self.__series_page_json_file.decoded_content.decode('utf-8')
                else:
                    json_content = self.__series_page_json_file.decoded_content

                series_page_details = json.loads(json_content)
            except json.decoder.JSONDecodeError:
                series_page_details = {}
        else:
            # If the file doesn't exist, create it as an empty JSON object
            self.__series_page_json_file. _ = repo.create_file(f'{series_page_folder.path}/seriespage.json', 'Creating seriespage.json file', '{}')

        # Read the values from this JSON if they are there
        if 'readme_sha' in series_page_details:
            self.last_post_readme_sha = series_page_details['readme_sha']

        if 'dev_to' in series_page_details:
            # If we have a dev_to section, read the slug and article id
            dev_to_section = series_page_details['dev_to']
            if 'slug' in dev_to_section and 'article_id' in dev_to_section:
                self.dev_to_slug = dev_to_section['slug']
                self.dev_to_article_id = dev_to_section['article_id']

    @property
    def is_outdated(self) -> bool:
        """
        Gets if the blog post is outdated.
        A blog post is outdated if the sha of the readme is different to the one recorded
        in the seriespage.json file.

        :return: True if the sha of the readme is different to the one saved in the seriespage.json file,
        otherwise false
        :rtype: bool
        """
        return self.last_post_readme_sha != self.current_readme_sha

    @property
    def is_existing_dev_to_article(self) -> bool:
        """
        Gets if this blog post already exists on dev.to, that is we have a slug and article ID

        :return: True if the article ID and slug are set otherwise false
        :rtype: bool
        """
        return self.dev_to_slug and self.dev_to_article_id

    def update_for_dev_to(self, slug: str, article_id: str) -> None:
        """
        Updates the seriespage JSON to reflect an updated blog post on dev.to

        :param str slug: The slug of the dev.to article
        :param str srticle_id: The article Id of the dev.to post
        """

        self.dev_to_slug = slug
        self.dev_to_article_id = article_id

    def commit_changes(self) -> None:
        """
        Writes updates to the series page JSON file
        """
        self.last_post_readme_sha = self.current_readme_sha

        series_page_json = {
            'readme_sha': self.last_post_readme_sha,
            'dev_to': {
                'slug': self.dev_to_slug,
                'article_id': self.dev_to_article_id,
            }
        }

        self.__repo.update_file(self.__series_page_json_file.path,
            'Updating series page JSON after writing blog posts',
            json.dumps(series_page_json, indent=2),
            self.__series_page_json_file.sha)

    def __str__(self) -> str:
        """
        The string representation of the series page.
        This includes the GitHub series page path, and details on any
        blog posts that have been created from this page

        :return: The string representation of the series page
        :rtype: str
        """
        dev_to_section = ''
        if self.dev_to_article_id == '':
            dev_to_section = 'none'
        else:
            dev_to_section = f'{self.dev_to_slug}({self.dev_to_article_id})'

        return f'{self.root_folder.path} (sha: {self.current_readme_sha}): dev.to: {dev_to_section}. Last sha: {self.last_post_readme_sha}'

class GitHubAccess:
    """
    A class that access a GitHub repo and has methods to find and update series pages
    """
    class GitHubSeriesFolderIterator:
        """
        An iterator that loops though all the folders in a repo that have a .seriespage folder
        """
        def __init__(self, repo: Repository) -> None:
            """
            Create the iterator.

            :param Repository repo: The GitHub repository
            """
            self.__repo = repo

            # This iterator starts in the root folder
            self.__contents = repo.get_contents('')

        def __iter__(self):
            # Nothing to do to initialize this iterator
            return self

        def __next__(self):
            # Walk through the contents whilst we still have some unprocessed items
            while self.__contents:
                # Get the next item from the contents
                file_content = self.__contents.pop(0)

                # Check to see if it a folder, for folders we need to extract
                # the contents, then check to see if the folder is a series page
                if file_content.type == 'dir':
                    # Extract the contents of the folder
                    dir_contents = self.__repo.get_contents(file_content.path)
                    # Check the contents of the folder to see if it matches what we expect for a series page
                    if is_series_page_folder(dir_contents):
                        # If we are a series page, create a wrapper for the details and return that
                        return SeriesPageDetails(self.__repo, file_content, dir_contents)
                    # If we are not a series page folder, add all the items from this folder to
                    # the end of our contents list to process. This way we process nested folders
                    self.__contents.extend(dir_contents)

            # Once we reach the end of the contents list, stop the iterator
            if not self.__contents:
                raise StopIteration

    def __init__(self, repo: str, access_token: str) -> None:
        """
        Creates the GitHubAccess object.

        :param str repo: The GitHub repo to scan for series pages
        :param str access_token: A GitHub access token
        """
        self.__g = Github(access_token)

        # If the repo name starts with github.com, strip this off
        if repo.lower().startswith('https://github.com/'):
            repo = repo[19:]

        # Create the repo connection
        self.__repo = self.__g.get_repo(repo)

    def get_series_folders(self) -> GitHubSeriesFolderIterator:
        """
        Gets an iterator to walk through all series page folders in the repo

        :return: The iterator
        :rtype: GitHubSeriesFolderIterator
        """
        return GitHubAccess.GitHubSeriesFolderIterator(self.__repo)
