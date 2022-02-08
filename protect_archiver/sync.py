import json
import logging

import click

from datetime import datetime
from os import path

import dateutil.parser

from .client import ProtectClient
from .downloader import Downloader
from .utils import calculate_intervals
from .utils import json_encode
from .utils import print_download_stats


def sync(
    dest,
    address,
    port,
    not_unifi_os,
    username,
    password,
    verify_ssl,
    statefile,
    ignore_state,
    ignore_failed_downloads,
    cameras,
    only_events,
):
    # normalize path to destination directory and check if it exists
    dest = path.abspath(dest)
    if not path.isdir(dest):
        click.echo(f"Video file destination directory '{dest} is invalid or does not exist!")
        exit(1)

    client = ProtectClient(
        address=address,
        port=port,
        not_unifi_os=not_unifi_os,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        destination_path=dest,
        ignore_failed_downloads=ignore_failed_downloads,
        use_subfolders=True,
    )

    # get camera list
    print("Getting camera list")
    camera_list = client.get_camera_list()

    if cameras != "all":
        camera_ids = set(cameras.split(","))
        camera_list = [c for c in camera_list if c.id in camera_ids]

    process = ProtectSync(
        client=client, destination_path=dest, statefile=statefile, only_events=only_events
    )
    process.run(camera_list, ignore_state=ignore_state)

    print_download_stats(client)


class ProtectSync:
    def __init__(
        self, client: ProtectClient, destination_path: str, statefile: str, only_events: bool
    ):
        self.client = client
        self.statefile = path.abspath(path.join(destination_path, statefile))
        self.only_events = only_events

    def readstate(self) -> dict:
        if path.isfile(self.statefile):
            with open(self.statefile) as fp:
                state = json.load(fp)
        else:
            state = {"cameras": {}}

        return state

    def writestate(self, state: dict):
        with open(self.statefile, "w") as fp:
            json.dump(state, fp, default=json_encode)

    def run(self, camera_list: list, ignore_state: bool = False):
        # noinspection PyUnboundLocalVariable
        logging.info(
            f"Synchronizing video files from 'https://{self.client.address}:{self.client.port}"
        )

        if not ignore_state:
            state = self.readstate()
        else:
            state = {"cameras": {}}
        for camera in camera_list:
            try:
                camera_state = state["cameras"].setdefault(camera.id, {})
                start = (
                    dateutil.parser.parse(camera_state["last"]).replace(
                        minute=0, second=0, microsecond=0
                    )
                    if "last" in camera_state
                    else camera.recording_start.replace(minute=0, second=0, microsecond=0)
                )
                end = datetime.now().replace(minute=0, second=0, microsecond=0)
                for interval_start, interval_end in calculate_intervals(start, end):
                    Downloader.download_footage(self.client, interval_start, interval_end, camera)
                    state["cameras"][camera.id] = {
                        "last": interval_end,
                        "name": camera.name,
                    }
            except Exception:
                logging.exception(
                    f"Failed to sync camera {camera.name} - continuing to next device"
                )
            finally:
                self.writestate(state)
