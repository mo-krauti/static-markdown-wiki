# static-markdown-wiki

Generates a website for your markdown notes. Features:

* `[[wikilinks]]` support
* generates page listings
* code syntax highlighting
* themeable 
* lightweight

## Setup

```bash
pip install .
```

## Running

```bash
static-markdown-wiki path_to_md_content_folder path_to_output_folder
```

## Customizing

Copy [the theme directory](./static_markdown_wiki/theme) somewhere. 
Adapt the jinja templates and the css to your liking. Run
```bash
static-markdown-wiki path_to_md_content_folder path_to_output_folder path_to_your_theme_folder
```
