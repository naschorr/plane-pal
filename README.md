<p align="center"><img src="https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/avatar.png"></p>

# Plane Pal
PUBG plane tracking bot for Discord

### Activation
- Go to [this page](https://discordapp.com/oauth2/authorize?client_id=361729535496028161&scope=bot&permissions=0) on Discord's site.
- Select the server that you want Plane Pal to be added into.
- Hit the "Authorize" button.
- Start plotting!

### Usage
`|<erangel|miramar> <X Grid Marker><Y Grid Marker>[Grid Subsection] <Plane's Heading>`

Plane Pal get activated with the pipe: `|` character by default, and it can plot out the plane's path with either the `erangel` or `e` keywords if you want to plot the path on the original PUBG map, Erangel. Alternatively, you can plot the map on the newer desert map, Miramar with the `miramar` or `m` keywords.

To get the bot to plot the plane's trajectory, it needs two pieces of information:
- The plane's current position (its grid markers)
- The plane's current heading

The grid marker comes from the letters representing the plane's X and Y location on the map. For example, grid marker `BK` has the Georgopol bridge running through the middle of it, and marker `EO` has most of the military base inside it. Just make sure that the X marker comes before the Y marker when invoking Plane Pal.

The plane's heading just comes from looking forward while the plane is flying, and seeing what the compass at the top of the screen says.

You can also more accurately position the plane with the optional `Grid Subsection` argument, which just comes from further subdividing the plane's current grid into nine equal squares, each with an imaginary number that corresponds to the squares location. The numbers are oriented in the same way as a keyboard in that square one is at the bottom left corner, and square nine is at the top right corner. If you omit this, the bot will just assume that the plane travelled through the middle of the grid.

See the examples section below.

### Examples
`|erangel ak1 90`

![erangel ak1 90](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/erangel%20ak1%2090.jpeg)


`|e al7 105`

![erangel al7 105](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/erangel%20al7%20105.jpeg)


`|erangel ep 355`

![erangel ep 355](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/erangel%20ep%20355.jpeg)


`|e gp7 330`

![erangel gp7 330](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/erangel%20gp7%20330.jpeg)


`|e hn 275`

![erangel hn 275](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/erangel%20hn%20275.jpeg)


`|miramar al 115`

![miramar al 115](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/miramar%20al%20115.jpeg)


`|m ei1 175`

![miramar ei1 175](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/miramar%20ei1%20175.jpeg)


`|miramar ho 280`

![miramar ho 280](https://raw.githubusercontent.com/naschorr/plane-pal/master/resources/examples/miramar%20ho%20280.jpeg)

### Colors
The colors seen on the maps represent common distances you can travel from the plane's path. Data was pulled from [this video](https://www.youtube.com/watch?v=worfS4pDkP4) by WackyJacky101.

- The white line shows the plane's path over the game's map.
- The orange-ish area shows the 1.4 km distance that a player can travel by gliding as far as possible from the plane before they're forced to pull their parachute.
- The yellow-ish area shows the 3 km distance that a player can travel by opening their parachute immediately and maintaining a 20 km/h vertical speed.

### Installation (Windows)
If you want to customize the bot to suit your needs, you may want to install and run it locally. If you're on Linux, then you can probably figure out how to do this on your own. To do that:

- Make sure you've got [Python 3.5](https://www.python.org/downloads/) or greater, and virtualenv installed (`pip install virtualenv`)
- `cd` into the directory that you'd like the project to go
- `git clone https://github.com/naschorr/plane-pal`
- `virtualenv plane-pal/`
- `cd plane-pal`
- Activate your newly created virtualenv with: `./Scripts/activate`
- Install the required modules with: `pip install -r requirements.txt`
- Create a [Discord app](https://discordapp.com/developers/applications/me), flag it as a bot, and put the bot token inside `plane-pal/token.json`
- Register the Bot with your server. Go to: `https://discordapp.com/oauth2/authorize?client_id=CLIENT_ID&scope=bot&permissions=0`, but make sure to replace CLIENT_ID with your bot's client id.
- Select your server, and hit "Authorize"
- Check out `config.json` for any configuration you might want to do. It's set up to work well out of the box, but you may want to change the colors, distances, or the pathing.

### Notes
Tested and running on Windows 10, and Ubuntu 16.04.
Currently hosted on my freebie EC2 instance, so I've got no idea what kind of demand that thing can handle.

If you run into issues during PyNaCl's installation on Linux when installing the requirements, you may need to run: `apt install build-essential libffi-dev python3.5-dev` to install some supplemental features for the setup process.
