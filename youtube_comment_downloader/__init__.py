import io
import json
import os
import sys
import time
from typing import Optional, Union

import click

from .downloader import SortBy, YoutubeCommentDownloader


def to_json(comment: dict, indent: Optional[int] = None) -> Union[str, bytes]:
    comment_str = json.dumps(comment, ensure_ascii=False, indent=indent)
    if indent is None:
        return comment_str
    padding = " " * (2 * indent) if indent else ""
    return "".join(padding + line for line in comment_str.splitlines(True))


@click.command()
@click.option(
    "--youtubeid", "-y", help="ID of Youtube video for which to download the comments"
)
@click.option("--url", "-u", help="Youtube URL for which to download the comments")
@click.option(
    "--output",
    "-o",
    required=True,
    help="Output filename (output format is line delimited JSON)",
)
@click.option(
    "--pretty/--no-pretty",
    "-p",
    default=False,
    help="Change the output format to indented JSON",
)
@click.option("--limit", "-l", type=int, help="Limit the number of comments")
@click.option(
    "--language",
    "-a",
    type=str,
    default=None,
    help="Language for Youtube generated text (e.g. en)",
)
@click.option(
    "--sort",
    "-s",
    type=int,
    default=SortBy.RECENT,
    help="Whether to download popular (0) or recent comments (1). Defaults to 1",
)
def main(
    youtubeid: Optional[str],
    url: Optional[str],
    output: str,
    pretty: bool,
    limit: Optional[int],
    language: Optional[str],
    sort: int,
) -> None:
    """Download Youtube comments without using the Youtube API"""
    if (not youtubeid and not url) or not output:
        raise ValueError("you need to specify a Youtube ID/URL and an output filename")

    if os.path.sep in output:
        outdir = os.path.dirname(output)
        os.makedirs(outdir, exist_ok=True)

    print("Downloading Youtube comments for", youtubeid or url)
    downloader = YoutubeCommentDownloader()
    generator = (
        downloader.get_comments(youtubeid, sort, language)
        if youtubeid
        else downloader.get_comments_from_url(url, sort, language)
    )

    count = 1
    with io.open(output, "w", encoding="utf8") as fp:
        start_time = time.time()

        if pretty:
            fp.write("{\n" + " " * 4 + '"comments": [\n')

        comment = next(generator, None)
        while comment:
            comment_str = to_json(comment, indent=4 if pretty else None)
            comment = (
                None if limit and count >= limit else next(generator, None)
            )  # Note that this is the next comment
            comment_str = (
                comment_str + "," if pretty and comment is not None else comment_str
            )
            print(
                comment_str.decode("utf-8")
                if isinstance(comment_str, bytes)
                else comment_str,
                file=fp,
                end="",
            )
            sys.stdout.write(f"\rDownloaded {count} comment(s)")
            sys.stdout.flush()
            count += 1

        if pretty:
            fp.write("\n" + " " * 4 + "]\n}")
    print(f"\n[{time.time() - start_time:.2f} seconds] Done!")


if __name__ == "__main__":
    main()
