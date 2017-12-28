# goes16-background
*Put near-realtime picture of Earth as your desktop background*

goes16-background is a Python 3 script that fetches near-realtime (~15 minutes delayed)
Full Disk Natural Color image of Earth as its taken by
[GOES-16](https://en.wikipedia.org/wiki/GOES-16) and sets it
as your desktop background.

![Example](/example.png?raw=true "Example")

Set a cronjob (or systemd service) that runs in every 15 minutes to automatically get the
near-realtime picture of Earth.

## Supported Desktop Environments
### Tested
* Unity 7
* Mate 1.8.1
* Pantheon
* LXDE
* OS X
* GNOME 3
* Cinnamon 2.8.8
* KDE

### Not Supported
* any other desktop environments that are not mentioned above.

## Configuration
```
usage: goes16-background [-h] [--version] [-s {678,1356,2712,5424,10848}]
                         [-d DEADLINE] [--save-battery]
                         [--output-dir OUTPUT_DIR]
                         [--composite-over COMPOSITE_OVER]

set (near-realtime) picture of Earth as your desktop background

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -s {678,1356,2712,5424,10848}, --size {678,1356,2712,5424,10848}
                        increases the quality (and the size) the image.
                        possible values are 678, 1356, 2712, 5424, 10848
  -d DEADLINE, --deadline DEADLINE
                        deadline in minutes to download the image, set 0 to
                        cancel
  --save-battery        stop refreshing on battery
  --output-dir OUTPUT_DIR
                        directory to save the temporary background image
  --composite-over COMPOSITE_OVER
                        image to composite the background image over
```

Increasing the size will increase the quality of the image, the time taken to download and the
memory consumption.

You should set a deadline compatible with your cronjob (or timer) settings to assure that script will terminate in X
minutes before it is started again.

You might use `--save-battery` to disable refreshing while running on battery power.

If you pass an image path with `--composite-over`, the image from goes16-background will be scaled to fit inside, centered, and pasted over it to be used as the background instead. This works great with, for example, [an image of the Milky Way](https://wallpaperscraft.com/image/milky_way_stars_space_nebula_68885_3840x2160.jpg).

### Nitrogen
If you use nitrogen for setting your wallpaper, you have to enter this in your
`~/.config/nitrogen/bg-saved.cfg`.

```
[:0.0]
file=/home/USERNAME/.goes16-background/goes16-latest.png
mode=4
bgcolor=#000000
```

## Installation
* You need a valid python3 installation including the python3-setuptools package
```
cd ~
git clone https://github.com/cameronleger/goes16-background.git

# install
sudo python3 setup.py install

# test whether it's working
goes16-background

# Get the installation path of goes16-background by running the command
which -- goes16-background

# Set goes16-background to be called periodically

    ## Either set up a cronjob
        crontab -e

        ### Add the line:
        */10 * * * * <INSTALLATION_PATH> # command line arguments here

    ## OR, alternatively use the provided systemd timer

        ### Configure
        vi systemd/goes16-background.service
        # Replace "<INSTALLATION_PATH>" with the output of the aforementioned command and command line arguments

        ### Copy systemd configuration
        cp systemd/goes16-background.{service,timer} ~/.config/systemd/user/

        ### Enable and start the timer
        systemctl --user enable --now goes16-background.timer
```

### For KDE Users
#### KDE 5.7+
To change the wallpaper in KDE 5.7+, desktop widgets must be unlocked. If you don't want to leave them unlocked,
the pre-KDE 5.7 method can still be used.

To unlock desktop widgets ([from the KDE userbase](https://userbase.kde.org/Plasma#Widgets)):
> Open the Desktop Toolbox or the Panel Toolbox or right click on the Desktop - if you see an item labeled Unlock
> Widgets then select that, and then proceed to add widgets to your Desktop or your Panel. 

#### Before KDE 5.7
> So the issue here is that KDE does not support changing the desktop wallpaper
> from the commandline, but it does support polling a directory for file changes
> through the "Slideshow" desktop background option, whereby you can point KDE
> to a folder and have it load a new picture at a certain interval.
>
> The idea here is to:
>
> * Set the cron for some interval (say 9 minutes)
> * Open Desktop Settings -> Wallpaper -> Wallpaper Type -> Slideshow
> * Add the `~/.goes16-background` dir to the slideshow list
> * Set the interval check to 10 minutes (one minute after the cron, also
>   depending on your download speed)

Many thanks to [xenithorb](https://github.com/xenithorb) [for the solution](https://github.com/xenithorb/himawaripy/commit/01d7c681ae7ce47f639672733d0f734574662833)!


### For Mac OSX Users

OSX has deprecated crontab, and replaced it with `launchd`. To set up a launch agent, copy the provided sample `plist`
file in `osx/org.cameronleger.goes16-background.plist` to `~/Library/LaunchAgents`, and edit the following entries if required

```
mkdir -p ~/Library/LaunchAgents/
cp osx/org.cameronleger.goes16-background.plist ~/Library/LaunchAgents/
```

* `ProgrammingArguments` needs to be the path to goes16-background installation. This *should* be `/usr/local/bin/goes16-background`
by default, but goes16-background may be installed elsewhere.

* `StartInterval` controls the interval between successive runs, set to 15 minutes (900 seconds) by default,
edit as desired.

Finally, to launch it, enter this into the console:
```
launchctl load ~/Library/LaunchAgents/org.cameronleger.goes16-background.plist
```

## Uninstallation
```
# Remove the cronjob
crontab -e
# Remove the line
*/15 * * * * <INSTALLATION_PATH>

# OR if you used the systemd timer
systemctl --user disable --now goes16-background.timer
rm $HOME/.config/systemd/user/goes16-background.{timer,service}

# Uninstall the package
sudo pip3 uninstall goes16-background
```

If you would like to share why, you can contact me on github or
[send an e-mail](mailto:contact@cameronleger.com).

## Attributions
Thanks to *[Bora M. Alper](https://github.com/boramalper/)* for the [base Himawari-8 background version](https://github.com/boramalper/himawaripy), which was a huge starting point for this version.

Obviously, thanks to the National Oceanic and Atmospheric Administration for opening these pictures to public.
