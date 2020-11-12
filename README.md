# i3FancySwitcher
When run displays an overview of open workspaces and applications in i3. You
can then select a workspace to switch to by clicking on it. Intended to be a
fancy drop in addition to i3.

![Current State](example.gif)

Colors are read from .Xresources by [tcolors](https://github.com/mkoskar/tcolors)

### Usage
```
Usage: python3 i3FancySwitcher -b [BACKGROUND_IMAGE] -f [FONT.TTF] [OPTIONAL_ARGS]
	-b/--background: Path to the background image to use
	-f/--font: Path to the .ttf file to use for the text
	-l/--location: Location of the bar, options of 'vl', 'vr', 'ht', 'hb' (vertical left/right, horizontal top/bottom). If not given defaults to the center of the screen.
	-g/--glyphs: no argument, specifies whether to describe workspace windows using icons or just text. Defaults to text
	-s/--scale: Percentage of screen real estate to take up, defaults to 20%
	-h/--help: Prints the usage
```

### TODO
- [ ] Actually nice command line argument structure
- [ ] Fix scaling issues on buttons
- [ ] SPEEEEEEEEED
