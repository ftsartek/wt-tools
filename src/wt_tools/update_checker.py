from urllib.parse import urlparse

import click
import requests


@click.group()
def main():
    pass


@main.command(name="check")
def check_versions_online() -> dict:
    """check warthunder versions online"""
    tag_list = [
        "",
        "dev",
        "dev-stable",
        "production-rc",
        "test",
        "nightly",
        "tournament",
        "experimental",
        "ps4submission",
        "xbox-submission",
        "experimental2",
        "china-test",
        "china-dev",
    ]
    headers = {"User-Agent": "wt-tools"}
    versions_url = (
        "https://yupmaster.gaijinent.com/yuitem/get_version.php?proj=warthunder&tag={}"
    )

    s = requests.Session()
    s.headers.update(headers)
    tags = {}
    for tag in tag_list:
        r = s.get(versions_url.format(tag))
        # if any valid version
        if r.text != "NOITEM":
            print(tag if tag else "default", r.text)
            tags[tag if tag else "default"] = r.text
    return tags


@main.command(name="download")
@click.argument("tag")
def download_yup(tag):
    """download yup (torrent) file with given tag,  list of available tags in CHECK command"""
    headers = {"User-Agent": "wt-tools"}
    yup_url = f"https://yupmaster.gaijinent.com/yuitem/get_version_yup.php?proj=warthunder&tag={'' if tag == 'default' else tag}&torrent=1"
    r = requests.get(yup_url, headers=headers)
    for line in r.text.split():
        # get the first good link
        if line.startswith("https"):
            name = urlparse(line).path.strip("/")
            r = requests.get(line, headers=headers)
            with open("{}.{}".format(tag, name), "wb") as f:
                f.write(r.content)
            break


def download_torrent(tag):
    """download torrent file with given tag,  list of available tags in CHECK command"""
    headers = {"User-Agent": "wt-tools"}
    torrent_url = f"https://yupmaster.gaijinent.com/yuitem/current_yup.php?project=warthunder&torrent=1&tag={'' if tag == 'default' else tag}"
    r = requests.get(torrent_url, headers=headers)
    for line in r.text.split():
        # get the first good link
        if line.startswith("https"):
            name = urlparse(line).path.strip("/")
            r = requests.get(line, headers=headers)
            with open("{}.{}".format(tag, name), "wb") as f:
                f.write(r.content)
            break

if __name__ == "__main__":
    main()
