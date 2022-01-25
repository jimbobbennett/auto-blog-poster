# Auto blog post series page Poster

This code contains a Python app that can be deployed as a GitHub action to take series page markdown files from the [Microsoft Reactor GitHub repo](https://github.com/microsoft/Reactors) and create blog posts from them on platforms such as [Dev.to](https://dev.to).

## App workflow

This app will work through all the folders in the repo, looking for series pages. These are the `README.md` files inside an folder that also contains a file called `seriespage.json` in the `.seriespage` folder. This JSON file contains metadata about the series page that is used to create the posts.

If this `.seriespage` folder is present, the JSON file inside is parsed and the README file is used to create the posts. If this folder is not present, the README file is ignored.

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

When the app encounters a `seriespage.json` file with details of an existing post, that post will be retrieved. If the README has been updated later than the post, the post is regenerated. This is checked by comparing the sha recorded in the JSON file with the sha of the file in GitHub - if these are different then the posts need to be updated.
