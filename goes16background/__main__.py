#!/usr/bin/env python3

import argparse
from datetime import timedelta, datetime
import io
import itertools as it
import json
from lxml import html
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

from .utils import set_background, get_desktop_environment, is_discharging


# Semantic Versioning: Major, Minor, Patch
GOES16_BG_VERSION = (1, 0, 0)
QUERY_URL = "https://www.star.nesdis.noaa.gov/GOES/GOES16_FullDisk.php"

# The image is yuuge
warnings.simplefilter('ignore', Image.DecompressionBombWarning)


def parse_args():
    parser = argparse.ArgumentParser(description="set (near-realtime) picture of Earth as your desktop background",
                                     epilog="http://github.com/cameronleger/goes16background")

    parser.add_argument("--version", action="version", version="%(prog)s {}.{}.{}".format(*GOES16_BG_VERSION))

    group = parser.add_mutually_exclusive_group()

    parser.add_argument("-s", "--size", type=int, choices=[339, 678, 1808, 5424, 10848], dest="size", default=1808,
                        help="increases the quality (and the size) the image. possible values are 339, 678, 1808, 5424, 10848")
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

    args = parser.parse_args()

    if not args.deadline >= 0:
        sys.exit("DEADLINE has to be greater than (or equal to if you want to disable) zero!\n")

    return args


def download(url):
    exception = None

    for i in range(1, 4):  # retry max 3 times
        try:
            with urllib.request.urlopen(url) as response:
                return response.read()
        except Exception as e:
            exception = e
            print("[{}/3] Retrying to download '{}'...".format(i, url))
            time.sleep(1)
            pass

    if exception:
        raise exception
    else:
        sys.exit("Could not download '{}'!\n".format(url))


def exit_thread(message):
    print(message)
    sys.exit(message)


def thread_main(args):
    print("Updating...")
    latest_html = download(QUERY_URL)
    html_tree = html.fromstring(latest_html)

    print("//a[contains(@title, 'GeoColor') and .='{0} x {0} px']".format(args.size))
    latest_link = html_tree.xpath("//a[contains(@title, 'GeoColor') and .='{0} x {0} px']".format(args.size))[0]
    if latest_link is None:
        exit_thread("Unable to find Latest Link for GeoColor Full Disk Images")

    print(latest_link.text)

    print("Latest image: {}.".format(latest_link.get('title')))

    download_url = latest_link.get("href")
    print("Download URL: {}".format(download_url))

    if args.composite_over is not None:
        print("Opening image to composite over...")
        try:
            composite_img = Image.open(args.composite_over)
        except Exception as e:
            exit_thread("Unable to open --composite-over image!\n")

    goes16_width = args.size
    goes16_height = args.size
    print("Downloading image...")
    goes16_img = Image.open(io.BytesIO(download(download_url)))
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

    for file in iglob(path.join(args.output_dir, "goes16-latest*.png")):
        os.remove(file)

    output_file = path.join(args.output_dir, "goes16-latest.png")
    print("Saving to '%s'..." % (output_file,))
    os.makedirs(path.dirname(output_file), exist_ok=True)
    output_img.save(output_file, "PNG")

    if not set_background(output_file):
        exit_thread("Your desktop environment '{}' is not supported!\n".format(get_desktop_environment()))

def main():
    args = parse_args()

    print("goes16background {}.{}.{}".format(*GOES16_BG_VERSION))

    if args.save_battery and is_discharging():
        sys.exit("Discharging!\n")

    main_thread = threading.Thread(target=thread_main, args=(args,), name="goes16background-main-thread", daemon=True)
    main_thread.start()
    main_thread.join(args.deadline * 60 if args.deadline else None)

    if args.deadline and main_thread.is_alive():
        sys.exit("Timeout!\n")

    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
