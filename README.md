# Auto blog post Poster

This code contains a Python app that can be deployed as a GitHub action to take blog post markdown files from a GitHub repo, and create blog posts from them on supported platforms.

Currently supported platforms are:

| Platform | Link |
| -------- | ---- |
| DEV | [dev.to](https://dev.to) |

## App workflow

This app will work through all the folders in the repo, looking for folders with posts in. These are the `README.md` files inside an folder that also contains a file called `post.json` in a `.blogpost` folder. This JSON file contains metadata about the file that is used to create the posts.

If this `.blogpost` folder is present, the JSON file inside is parsed and the README file is used to create the posts. If this folder is not present, the README file is ignored. This allows you to only publish the markdown files you want

The format of this JSON is:

```json
{
    "readme_sha": "",
    "dev_to": {
        "slug": "",
        "article_id": ""
    }
}
```

To create an initial blog post, this folder can contain an empty JSON file. Once the blog post is created, this file is updated.

| Field | Description |
| ----- | ----------- |
| `readme_sha` | The hash of the README.md file when the blog posts were written |
| `dev_to` | This section is details for a post to Dev.to |
| `dev_to.slug`  | The slug of the Dev.to article |
| `dev_to.article_id` | The article id of the Dev.to article |

When the app encounters a `post.json` file with details of an existing post, that post will be retrieved. If the README has been updated later than the post, the post is regenerated. This is checked by comparing the sha recorded in the JSON file with the sha of the file in GitHub - if these are different then the posts need to be updated.

## Environment variables

To run this, you need to set the following environment variables:

| Variable name | Description |
| ------------- | ----------- |
| DEV_TO_API_KEY | Your Dev.to API key
| DEV_TO_ORGANIZATION_ID | Your Dev.to organization Id. This is optional, if you don't want to post to an organization, don't set this |
| REPO | The GitHub repo to read blog posts from |
| GITHUB_ACCESS_TOKEN | Your GitHub access token |
