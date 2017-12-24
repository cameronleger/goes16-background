from setuptools import setup, find_packages


setup(
    name="goes16-background",
    version="1.0.0",
    url="http://github.com/cameronleger/goes16-background",
    author="Cameron Leger",
    author_email="contact@cameronleger.com",
    license="MIT",
    description="Set near-realtime Full Disk GeoColor image of Earth as your desktop background",
    long_description="goes16-background is a Python 3 script that fetches near-realtime (~15 minutes delayed) "
                     "Full Disk GeoColor image of Earth as its taken by GOES-16 "
                     "and sets it as your desktop background.",
    install_requires=["appdirs", "pillow", "python-dateutil"],
    packages=find_packages(),
    entry_points={"console_scripts": ["goes16-background=goes16background.__main__:main"]},
)
