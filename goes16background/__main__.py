#!/usr/bin/env python3

import argparse
from datetime import timedelta, datetime
import io
import itertools as it
import json
from lxml import html
import math
import multiprocessing as mp
import multiprocessing.dummy as mp_dummy
import os
import os.path as path
import sys
from time import strptime, strftime, mktime
import urllib.request
from glob import iglob, glob
import threading
import time
from logging import warnings

import appdirs
from PIL import Image, ImageDraw, ImageFilter
from dateutil.tz import tzlocal

from .utils import set_background, get_desktop_environment, is_discharging, download


# Semantic Versioning: Major, Minor, Patch
GOES16_BG_VERSION = (1, 2, 0)
counter = None
TILE_SIZE = 678
BASE_URL = "http://rammb-slider.cira.colostate.edu/data"

# The image is yuuge
warnings.simplefilter('ignore', Image.DecompressionBombWarning)


def parse_args():
    parser = argparse.ArgumentParser(description="set (near-realtime) picture of Earth as your desktop background",
                                     epilog="http://github.com/cameronleger/goes16-background")

    parser.add_argument("--version", action="version", version="%(prog)s {}.{}.{}".format(*GOES16_BG_VERSION))

    parser.add_argument("-s", "--size", type=int, choices=[678, 1356, 2712, 5424, 10848], dest="size", default=1356,
                        help="increases the quality (and the size) the image. possible values are 678, 1356, 2712, 5424, 10848")
    parser.add_argument("-d", "--deadline", type=int, dest="deadline", default=6,
                        help="deadline in minutes to download the image, set 0 to cancel")
    parser.add_argument("--save-battery", action="store_true", dest="save_battery", default=False,
                        help="stop refreshing on battery")
    parser.add_argument("--output-dir", type=str, dest="output_dir",
                        help="directory to save the temporary background image",
                        default=appdirs.user_cache_dir(appname="goes16background", appauthor=False))
    parser.add_argument("--composite-over", type=str, dest="composite_over",
                        help="image to composite the background image over",
                        default=None)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    if not args.deadline >= 0:
        sys.exit("DEADLINE has to be greater than (or equal to if you want to disable) zero!\n")

    return args


def download_chunk(args):
    global counter

    base_url, latest, x, y, level, tile_count = args
    url_format = base_url + "/imagery/{}/goes-16---full_disk/natural_color/{}/0{}/00{}_00{}.png"
    url = url_format.format(strftime("%Y%m%d", latest), strftime("%Y%m%d%H%M%S", latest), level, y, x)

    tiledata = download(url)

    with counter.get_lock():
        counter.value += 1
        if counter.value == tile_count * tile_count:
            print("Downloading tiles: completed.")
        else:
            print("Downloading tiles: {}/{} completed...".format(counter.value, tile_count * tile_count))
    return x, y, tiledata


def exit_thread(message):
    print(message)
    sys.exit(message)


def thread_main(args):
    global counter
    counter = mp.Value("i", 0)

    tile_count = int(args.size / TILE_SIZE)
    level = int(math.log(tile_count, 2))

    print("Updating...")
    latest_json = download("{}/json/goes-16/full_disk/natural_color/latest_times.json".format(BASE_URL))
    latest = strptime(str(json.loads(latest_json.decode("utf-8"))["timestamps_int"][0]), "%Y%m%d%H%M%S")

    print("Latest version: {} UTC.".format(strftime("%Y/%m/%d %H:%M:%S", latest)))

    if args.composite_over is not None:
        print("Opening image to composite over...")
        try:
            composite_img = Image.open(args.composite_over)
        except Exception as e:
            exit_thread("Unable to open --composite-over image!\n")

    goes16_width = TILE_SIZE * tile_count
    goes16_height = TILE_SIZE * tile_count
    goes16_img = Image.new("RGB", (goes16_width, goes16_height))

    p = mp_dummy.Pool(tile_count * tile_count)
    print("Downloading tiles...")
    res = p.map(download_chunk, it.product((BASE_URL,), (latest,), range(tile_count), range(tile_count), (level,), (tile_count,)))

    for (x, y, tiledata) in res:
        tile = Image.open(io.BytesIO(tiledata))
        goes16_img.paste(tile, (TILE_SIZE * x, TILE_SIZE * y, TILE_SIZE * (x + 1), TILE_SIZE * (y + 1)))

    output_img = goes16_img

    if args.composite_over is not None:
        print("Compositing over input image")
        composite_width, composite_height = composite_img.size
        resize_ratio = min(composite_width / goes16_width, composite_height / goes16_height)

        goes16_img = goes16_img.resize((round(goes16_width * resize_ratio), round(goes16_height * resize_ratio)),
            Image.ANTIALIAS)

        radius_img = min(goes16_width, goes16_height) * resize_ratio / 2
        goes16_center_img = Image.new("RGB", (composite_width, composite_height), "black")
        goes16_center_img.paste(goes16_img, (round(composite_width / 2 - radius_img), round(composite_height / 2 - radius_img)))

        radius = min(goes16_width, goes16_height) * resize_ratio * 0.995 / 2
        left = round(composite_width / 2 - radius)
        right = round(composite_width / 2 + radius)
        top = round(composite_height / 2 - radius)
        bottom = round(composite_height / 2 + radius)

        mask_img = Image.new("L", (composite_width, composite_height), "black")
        draw = ImageDraw.Draw(mask_img)
        draw.ellipse((left, top, right, bottom), fill='white')
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=2))

        composite_img.paste(goes16_center_img, (0, 0), mask_img)

        output_img = composite_img

    for file in iglob(path.join(args.output_dir, "goes16-*.png")):
        os.remove(file)

    output_file = path.join(args.output_dir, strftime("goes16-%Y%m%dT%H%M%S.png", latest))
    print("Saving to '%s'..." % (output_file,))
    os.makedirs(path.dirname(output_file), exist_ok=True)
    output_img.save(output_file, "PNG")

    if not set_background(output_file):
        exit_thread("Your desktop environment '{}' is not supported!\n".format(get_desktop_environment()))

def main():
    args = parse_args()

    print("goes16-background {}.{}.{}".format(*GOES16_BG_VERSION))

    if args.save_battery and is_discharging():
        sys.exit("Discharging!\n")

    main_thread = threading.Thread(target=thread_main, args=(args,), name="goes16-background-main-thread", daemon=True)
    main_thread.start()
    main_thread.join(args.deadline * 60 if args.deadline else None)

    if args.deadline and main_thread.is_alive():
        sys.exit("Timeout!\n")

    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
