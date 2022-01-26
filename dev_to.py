"""
This module contains functions to interact with the Dev.to REST API
"""

from urllib.parse import urljoin
from typing import Dict, Optional, Tuple

import requests

from github_access import PostDetails

# The Dev.to endpoint for creating an article.
# This endpoint is documented here: https://developers.forem.com/api/#operation/createArticle
CREATE_ARTICLE_ENDPOINT = 'https://dev.to/api/articles'

class ReadmeParseError(Exception):
    """
    An exception type for errors parsing README.ms files in the expected format
    """

def update_relative_image_urls(post_details: PostDetails, readme: str) -> str:
    """
    Markdown can contain imagues using relative URLs. This function replaces all the relative URLs in
    the README with full URLs based off the repo.

    Images are defined as ![<alt text>](<image url>)

    :param PostDetails post_details: The post page details for the article to create
    :param str readme: The contents of the README.md markdown file

    :return: The readme with full URLs
    :rtype: str
    """

    # Check for image tags - if none are present, just return the untouched readme
    if readme.find('![') < 0:
        return readme

    # Start by building a root URL that can be applied to any markdown image URLs
    root_url = urljoin('https://raw.githubusercontent.com/', post_details.repo.full_name)
    root_url = urljoin(f'{root_url}/', post_details.repo.default_branch)
    root_url = urljoin(f'{root_url}/', post_details.root_folder.path)

    # Work through the readme finding image open tags
    open_tag_position = readme.find('![')

    # Do this in a loop - at the end of the loop the next tag is found
    # by starting one past the previous tag
    # This way the position will be -1 when we have found the last one
    while open_tag_position > -1:
        # We have found the open tag, so find the separator between the alt text
        # and the image URL by finding the close square bracket from the alt text
        # and the open bracked from the url.
        # We cannot assume these are next to each other, there might be a space between
        close_square_bracket = readme.find(']', open_tag_position)
        open_bracket = readme.find('(', close_square_bracket) + 1
        close_bracket = readme.find(')', open_bracket)

        # Grab the URL from between the open and close square bracket
        url_text = readme[open_bracket:close_bracket]

        # Check if we need to make this an absolute URL
        if not url_text.lower().startswith('http'):
            absolute_url_text = urljoin(f'{root_url}/', url_text)
            start_part = readme[:open_bracket]
            end_part = readme[close_bracket:]
            readme = start_part + absolute_url_text + end_part

        # Find the next image open tag in the readme
        # Despite replacing the relative url with the absolute, we can still start at the same
        # point, it's only the text past our open tag that has changed
        open_tag_position = readme.find('![', open_tag_position + 1)

    return readme

def create_article_payload_from_readme(post_details: PostDetails, readme: str, organization_id: Optional[int]) -> Dict:
    """
    This creates a dev.to article from a README file.

    This assumes the readme starts with a top level heading (#) on the first line,
    if this is not the case then an error is raised. This heaading is used as the blog
    post title, and is not included in the actual blog markdown.

    Exception - if the README starts with an image, this is set as a page image

    :param PostPageDetails post_details: The post page details for the article to create
    :param str readme: The contents of the README.md markdown file
    :param Optional[int] organization_id: The Dev.to organization id if this article should
    be posted as part of an organization. If no organization is needed, pass None

    :return: The JSON document for the payload
    :rtype: Dict
    """
    # Look for the first H1 header
    # If this is not on the first line then fail.

    # Strip any whitespace in case the header is a few lines in
    readme = readme.strip()

    # Get the first line from the readme, and delete it from the resulting string
    readme_lines = readme.splitlines()
    first_line = readme_lines[0].strip()

    # Check the first entry to see if it is an image
    # If so this can be an article cover image and then the image is stripped
    # from the README before further processing

    # Check for H1 - this should be a # character with no # after it
    # So we check that the string starts with a #, and if we skip this,
    # The resulting string does not start with a #
    if not first_line.startswith('#') or first_line[1:].startswith('#'):
        raise ReadmeParseError('Readme file does not start with a H1 (#)')

    # Remove the # and create the title
    title = first_line.lstrip('#').strip()

    # Remove the first line from the readme
    readme = readme[len(first_line):].strip()

    # Images in the markdown can be in the local repository
    # Any that are will have a relative URL, so this needs to be updated to a full URL
    # that can be referenced from the article
    readme = update_relative_image_urls(post_details, readme)

    # Create the article
    return create_article_payload(title, readme, organization_id)

def create_article_payload(title: str, body: str, organization_id: Optional[int]) -> Dict:
    """
    Creates a JSON document in the correct format to submit a new article to Dev.to.

    :param str title: The article title
    :param str body: The article body as markdown
    :param Optional[int] organization_id: The Dev.to organization id if this article should
    be posted as part of an organization. If no organization is needed, pass None

    :return: The JSON document for the payload
    :rtype: Dict
    """
    # Build the payload. The format is defined here:
    # https://developers.forem.com/api/#operation/createArticle
    payload = {
        'article' : {
            'title': title,
            'published': False,
            'body_markdown': body,
            'tags': [
                'autogenerated'
            ]
        }
    }

    # This payload can contain an organization id if the article is designed to be posted
    # in an organization. Passing None to this function means no organization,
    # otherwise the organization ID is set on the payload
    if organization_id:
        payload['article']['organization_id'] = organization_id

    return payload

def call_create_article(api_key: str, article: Dict) -> Tuple[str, str]:
    """
    Makes a POST call to the Dev.to API to create the article for the given payload.
    The slug and article ID are returned.

    :param str api_key: The Dev.to API key
    :param Dict article: The artical as a JSON payload

    :return: A tuple containing the slug and the ID of the new article
    :rtype: Tuple[str, str]
    """
    # The API key needs to be passed as a header
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }

    # Make the post request to the Create Article endpoint, passing in our article and headers
    response = requests.post(CREATE_ARTICLE_ENDPOINT, json=article, headers=headers)

    # Check the response. Dev.to returns 201 when an article is created succesfully.
    # Any other code, raise an exception
    if response.status_code != 201:
        raise ValueError(response.text)

    # Get the response JSON
    response_body = response.json()

    # Build a tuple return value.
    # The first value in the tuple is the slug - so part of the final article URL
    #    The final URL is in the form https://dev.to/<user>/<slug>
    # The second value in the tuple is the article's unique ID
    return (response_body['slug'], response_body['id'])

def call_update_article(api_key: str, article_id: str, article: Dict) -> Tuple[str, str]:
    """
    Makes a POST call to the Dev.to API to update an article for the given payload
    and article ID

    :param str api_key: The Dev.to API key
    :param str article_id: The Dev.to article ID
    :param Dict article: The artical as a JSON payload

    :return: A tuple containing the slug and the ID of the updated article
    :rtype: Tuple[str, str]
    """
    # The API key needs to be passed as a header
    headers = {
        'Content-Type': 'application/json',
        'api-key': api_key
    }

    # Build the endpoint using the article ID - to update we make a PUT to that specific article
    # See: https://developers.forem.com/api/#operation/updateArticle
    url = f'{CREATE_ARTICLE_ENDPOINT}/{article_id}'

    # Make the put request to the Article endpoint, passing in our article and headers
    response = requests.put(url, json=article, headers=headers)

    # Check the response. Dev.to returns 2001 when an article is updated succesfully.
    # Any other code, raise an exception
    if response.status_code != 200:
        raise ValueError(response.text)

    # Get the response JSON
    response_body = response.json()

    # Build a tuple return value.
    # The first value in the tuple is the slug - so part of the final article URL
    #    The final URL is in the form https://dev.to/<user>/<slug>
    # The second value in the tuple is the article's unique ID
    return (response_body['slug'], response_body['id'])

def post_to_dev_to(post_page: PostDetails, api_key: str, organization_id: Optional[int]) -> None:
    """
    Posts a blog post to dev.to.

    This checks if the dev.to article exists. If not, it is created, otherwise it is uypdated.

    :param PostDetails post_page: The post page details for the article to create
    :param str api_key: The Dev.to API key
    :param Optional[int] organization_id: The Dev.to organization id if this article should
    be posted as part of an organization. If no organization is needed, pass None
    """
    # Build the article payload
    print('Reading from GitHub and creating the payload')
    article_payload = create_article_payload_from_readme(post_page, post_page.readme_content, organization_id)

    # Check if the article already exists on dev.to, if not we create, if so we update
    if post_page.is_existing_dev_to_article:
        # Update the article
        print('Updating article on Dev.to...')
        slug, article_id = call_update_article(api_key, post_page.dev_to_article_id, article_payload)
        print(f'Article updated: slug {slug}, id {article_id}')
    else:
        # Submit the article and get back the details
        print('Creating article on Dev.to...')
        slug, article_id = call_create_article(api_key, article_payload)
        post_page.update_for_dev_to(slug, article_id)
        print(f'Article created: slug {slug}, id {article_id}')
