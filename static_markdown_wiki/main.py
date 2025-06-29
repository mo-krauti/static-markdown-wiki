import pathlib
import shutil
import sys
from dataclasses import dataclass

import jinja2
import markdown
import markupsafe
from markdown.extensions.wikilinks import WikiLinkExtension
from pymdownx.highlight import HighlightExtension
from pymdownx.magiclink import MagiclinkExtension
from pymdownx.superfences import SuperFencesCodeExtension


@dataclass
class StaticMarkdownWikiContext:
    content_folder_path: pathlib.Path
    out_folder_path: pathlib.Path
    jinja_env: jinja2.Environment


def build_url(label: str, base: str, end: str) -> str:
    for page in pages.values():
        if page.title == label:
            return page.url
    print(f"Warning: no page found for label {label}")
    return "/404.html"


class Page:
    def __init__(self, context: StaticMarkdownWikiContext, url: str, is_folder: bool):
        self.context = context
        self.url = url
        self.url_split = self.url.split("/")[1:]
        self.is_folder = is_folder
        self.breadcrumb_html = self.generate_breadcrumb_html()

    def generate_content_html(self) -> str:
        return ""

    def render(self):
        return self.context.jinja_env.get_template("base.html").render(
            title=self.title,
            breadcrumb=markupsafe.Markup(self.breadcrumb_html),
            content=markupsafe.Markup(self.generate_content_html()),
        )

    def write_html(self):
        if self.is_folder:
            html_relative_path_text = f"{self.url}index.html".removeprefix("/")
        else:
            html_relative_path_text = self.url.removeprefix("/")
        html_relative_path = pathlib.Path(html_relative_path_text)
        html_path = self.context.out_folder_path.joinpath(html_relative_path)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(self.render())

    @property
    def title(self) -> str:
        if self.url == "/":
            return "Home"
        if self.is_folder:
            return self.url_split[-2]
        else:
            return self.url_split[-1].removesuffix(".html")

    def generate_breadcrumb_html(self) -> str:
        self.parent_folder_urls = []
        breadcrumb_html = "<a href='/'>Home</a>"
        if self.is_folder:
            breadcrumb_end = 2
        else:
            breadcrumb_end = 1
        for i in range(len(self.url_split) - breadcrumb_end):
            if i < 0:
                continue
            url_path = "/" + "/".join(self.url_split[: i + 1])
            if len(url_path) > 1:
                url_path += "/"
            self.parent_folder_urls.append(url_path)
            breadcrumb_html += f" > <a href='{url_path}'>{self.url_split[i]}</a>"
        return breadcrumb_html


class MarkdownPage(Page):
    def __init__(self, context: StaticMarkdownWikiContext, markdown_path: pathlib.Path):
        self.markdown_path = markdown_path
        self.markdown_relative_path = self.markdown_path.relative_to(
            context.content_folder_path
        )
        self.markdown_relative_path_without_suffix = str(
            self.markdown_relative_path.with_suffix("")
        )
        is_folder = self.markdown_relative_path_without_suffix.endswith("index")
        if is_folder:
            url = f"/{self.markdown_relative_path_without_suffix.removesuffix("index")}"
        else:
            url = f"/{self.markdown_relative_path_without_suffix}.html"
        super().__init__(context, url, is_folder)

    def generate_content_html(self):
        return markdown.markdown(
            self.markdown_path.read_text(),
            extensions=[
                WikiLinkExtension(build_url=build_url),
                HighlightExtension(),
                MagiclinkExtension(),
                SuperFencesCodeExtension(),
            ],
        )


class GeneratedFolderPage(Page):
    def __init__(self, context: StaticMarkdownWikiContext, folder_url: str):
        super().__init__(context, folder_url, True)

    def generate_content_html(self) -> str:
        links = []
        for page_url in pages:
            if page_url.startswith(self.url):
                remaining_url_parts = (
                    page_url.removeprefix(self.url).removesuffix("/").split("/")
                )
                if len(remaining_url_parts) == 1 and remaining_url_parts[0] != "":
                    links.append((page_url, pages[page_url].title))
        return self.context.jinja_env.get_template("folder_listing.html").render(
            links=sorted(links, key=lambda link: link[1]),
        )


pages: dict[str, Page] = {}


def main():
    if len(sys.argv) == 4:
        theme_folder_path = pathlib.Path(sys.argv[3]).resolve()
    else:
        theme_folder_path = pathlib.Path(__file__).parent.resolve() / "theme"
    context = StaticMarkdownWikiContext(
        pathlib.Path(sys.argv[1]).resolve(),
        pathlib.Path(sys.argv[2]).resolve(),
        jinja2.Environment(
            loader=jinja2.FileSystemLoader(theme_folder_path),
            autoescape=jinja2.select_autoescape(),
        ),
    )

    for markdown_path in context.content_folder_path.rglob("*.md"):
        page = MarkdownPage(context, markdown_path)
        pages[page.url] = page

    folder_urls = set()
    for page in pages.values():
        for parent_url in page.parent_folder_urls:
            folder_urls.add(parent_url)
    for folder_url in folder_urls:
        if folder_url not in pages:
            pages[folder_url] = GeneratedFolderPage(context, folder_url)

    for page in pages.values():
        page.write_html()

    print(f"Wrote {len(pages)} pages")

    for css_path in theme_folder_path.glob("*.css"):
        css_relative_path = css_path.relative_to(theme_folder_path)
        css_out_path = context.out_folder_path.joinpath(css_relative_path)
        shutil.copy(css_path, css_out_path)

    number_files = 0
    for file_path in context.content_folder_path.rglob("*.*"):
        if file_path.is_file() and file_path.suffix != ".md":
            file_relative_path = file_path.relative_to(context.content_folder_path)
            file_out_path = context.out_folder_path.joinpath(file_relative_path)
            if file_out_path.parent.exists():
                shutil.copy(file_path, file_out_path)
                number_files += 1
    print(f"Copied {number_files} files")


if __name__ == "__main__":
    main()
