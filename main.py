import json
import re
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

import requests

MANGADEX_USER_ID = "d2ae45e0-b5e2-4e7f-a688-17925c2d7d6b"
SEASONAL_LIST_NAME_PATTERN = re.compile(
    r"(?P<season>winter|spring|summer|fall)\s+(?P<year>\d+)$", re.IGNORECASE
)

build_path = Path().cwd().joinpath("build")
build_path.mkdir(exist_ok=True)


class Season(IntEnum):
    WINTER = 0
    SPRING = 1
    SUMMER = 2
    FALL = 3


@dataclass(frozen=True, order=True)
class SeasonalList:
    id: str = field(compare=False)
    manga_ids: list[str] = field(compare=False)

    year: int
    season: Season

    @property
    def name(self) -> str:
        return f"{self.season.name.capitalize()} {self.year}"

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "manga_ids": self.manga_ids,
        }


if __name__ == "__main__":
    seasonal_lists = []
    offset = 0

    while True:
        custom_list_res = requests.get(
            "https://api.mangadex.org/user/{}/list?limit=50&offset={}".format(
                MANGADEX_USER_ID, offset
            )
        ).json()
        for custom_list in custom_list_res["data"]:
            name_regex = SEASONAL_LIST_NAME_PATTERN.search(
                custom_list["attributes"]["name"]
            )

            if not name_regex:
                continue

            seasonal_lists.append(
                SeasonalList(
                    id=custom_list["id"],
                    season=Season[name_regex.group("season").upper()],
                    year=name_regex.group("year"),
                    manga_ids=sorted(
                        [
                            i["id"]
                            for i in custom_list["relationships"]
                            if i["type"] == "manga"
                        ]
                    ),
                )
            )

        meta_limit = int(custom_list_res["limit"])
        meta_offset = int(custom_list_res["offset"])
        meta_total = int(custom_list_res["total"])
        next_offset = meta_offset + meta_limit
        if next_offset < meta_total:
            offset = next_offset
        else:
            break

    latest_seasonal_list = sorted(seasonal_lists, reverse=True)[0]

    for minified in [True, False]:
        file_path = build_path.joinpath(
            f"seasonal-list{'.min' if minified else ''}.json"
        )
        with open(file_path, "w+") as file:
            json_str = json.dumps(
                latest_seasonal_list.as_dict(),
                indent=None if minified else 2,
                separators=(",", ":") if minified else None,
            )
            file.write(json_str + "\n")
