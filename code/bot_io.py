import re
from math import sqrt

from discord import errors
from discord.ext import commands

import utilities
import plotter
import dynamo_helper

## Config
CONFIG_OPTIONS = utilities.load_config()


class GridObject:
    ## Keys
    MAX_SECTIONS_KEY = "max_sections"

    ## Defaults
    MAX_SECTIONS = CONFIG_OPTIONS.get(MAX_SECTIONS_KEY, 9)    # 3x3 subgrid in each grid on the map


    def __init__(self, x, y, section=None):
        ## Prepopulate the members
        self.valid = True
        self._x = None
        self._y = None
        self._section = None

        self.x = x
        self.y = y
        self.section = section

    ## Properties

    @property
    def x(self):
        return self._x


    @x.setter
    def x(self, value):
        x = value.lower()

        ## This lets the user enter in the X and Y grid markers in the wrong order, and still tolerate it.
        ## Obviously, it's still a good idea to enter them in correctly. See y property as well.

        ## Make sure x's ascii value is between 'a' and 'h's ascii values
        if(ord('a') <= ord(x) <= ord('h')):
            self._x = x
        ## If it's less than 'a', then theres no hope, just clamp it to 'a'
        elif(ord('a') > ord(x)):
            self._x = 'a'
        ## Otherwise see if y's setter can handle it without giving up.
        else:
            self._x = None
            self.valid = False
            self.y = x


    @property
    def y(self):
        return self._y


    @y.setter
    def y(self, value):
        y = value.lower()

        if(ord('i') <= ord(y) <= ord('p')):
            self._y = y
        elif(ord('p') < ord(y)):
            self._y = 'p'
        else:
            self._y = None
            self.valid = False
            self.x = y


    @property
    def section(self):
        return self._section


    @section.setter
    def section(self, value):
        section = int(value) if value else 0
        if(1 <= section <= self.MAX_SECTIONS):
            self._section = section
        else:        
            self._section = None

    ## Methods

    def get_true_x(self, pixels_per_km):
        ## True X calculated from the left side of the image

        ## Sanity check to prevent garbage data from being used
        if(not self.valid):
            raise RuntimeError("Can't get true X distance without valid X: ({}).".format(self.x))

        letter_index = ord(self.x) - ord('a')   ## Grid index = difference between grid marker's ascii value and a's ascii value

        ## Calculate the pixel distance from the left of the screen, for a given letter's grid marker
        grid_offset = letter_index * pixels_per_km
        if(self.section is not None):
            ## Determine the extra offset from the left if the user specified a sub section of the grid
            max_section_sqrt = sqrt(self.MAX_SECTIONS)
            section_index = self.section - 1    # 0 index the section index, it's [1-9] for users
            section_offset = ((((section_index % max_section_sqrt) / max_section_sqrt) + (1 / (max_section_sqrt * 2))) * pixels_per_km)
        else:
            ## Otherwise, just assume that the plane travelled through the center of the grid
            section_offset = pixels_per_km / 2

        ## Return an integer value to avoid any rounding issues (plus, we're dealing with whole pixels anyway)
        return int(grid_offset + section_offset)


    def get_true_y(self, pixels_per_km):
        ## True Y calculated from the top of the image. See get_true_x() above for comments

        if(not self.valid):
            raise RuntimeError("Can't get true Y distance without valid Y: ({}).".format(self.y))

        letter_index = ord(self.y) - ord('i')

        grid_offset = letter_index * pixels_per_km
        if(self.section is not None):
            max_section_sqrt = sqrt(self.MAX_SECTIONS)
            section_index = self.section - 1    # 0 index the section index, it's [1-9] for users
            section_offset = pixels_per_km - ((((section_index // max_section_sqrt) / max_section_sqrt) + (1 / (max_section_sqrt * 2))) * pixels_per_km)
        else:
            section_offset = pixels_per_km / 2

        return int(grid_offset + section_offset)


class HeadingObject:
    def __init__(self, heading):
        self.heading = int(heading)

    ## Methods

    @property
    def angle(self):
        return (450 - self.heading) % 360


class PathObject:
    def __init__(self, grid, heading):
        self.grid_obj = grid
        self.heading_obj = heading


    def __str__(self):
        raw = "{} {} {} {}"
        return raw.format(  self.grid_obj.x,
                            self.grid_obj.y,
                            self.grid_obj.section,
                            self.heading_obj.heading )


class PathParser:
    ## Keys
    GRID_REGEX_PATTERN_KEY = "grid_regex_pattern"
    HEADING_REGEX_PATTERN_KEY = "heading_regex_pattern"

    ## Defaults
    GRID_REGEX_PATTERN = CONFIG_OPTIONS.get(GRID_REGEX_PATTERN_KEY, r"([a-pA-P])([a-pA-P])([1-9]?)")
    HEADING_REGEX_PATTERN = CONFIG_OPTIONS.get(HEADING_REGEX_PATTERN_KEY, r"(\d{1,3})")


    def __init__(self, **kwargs):
        self.grid_regex = re.compile(kwargs.get(self.GRID_REGEX_PATTERN_KEY, self.GRID_REGEX_PATTERN))
        self.heading_regex = re.compile(kwargs.get(self.HEADING_REGEX_PATTERN_KEY, self.HEADING_REGEX_PATTERN))


    def parse_message(self, message):
        start_grid, message = self.parse_grid(message)
        if(not start_grid):
            raise RuntimeError("Invalid grid marker for '{}'".format(message))

        ## Todo: Specify heading or end_grid?
        heading, message = self.parse_heading(message)
        if(not heading):
            raise RuntimeError("Invalid heading designation for '{}'".format(message))

        return PathObject(start_grid, heading)


    def parse_grid(self, message):
        ## Basic regex string parsing, with errors popped on getting an unknown command
        ## Todo: implement re.IGNORECASE (not working for whatever reason?)
        match = self.grid_regex.search(message)
        #print(match, self.grid_regex.search(message))
        if(match):
            ## Assume that the user correctly entered the X and Y grid markers for now
            x = match.group(1)
            y = match.group(2)
            section = match.group(3)

            ## Todo: improve error output and handling
            if(x and y):
                grid_obj = GridObject(x, y, section)
                if(grid_obj.valid):
                    return grid_obj, message[match.end():]
            elif(y and not x):
                raise RuntimeError("Invalid X grid marker '{}'".format(x))
            elif(x and not y):
                raise RuntimeError("Invalid Y grid marker '{}'".format(y))
            else:
                raise RuntimeError("Invalid X and Y grid markers '{}', '{}'".format(x, y))

        raise RuntimeError("Invalid grid marker for '{}'".format(message[match.start():match.end()]))


    def parse_heading(self, message):
        ## Basic regex string parsing, with errors popped on getting an unknown command
        match = self.heading_regex.search(message)
        if(match):
            message = message[match.end():]
            heading = match.group(1)

            if(heading):
                return HeadingObject(heading), message
            else:
                raise RuntimeError("Invalid heading designation '{}'".format(heading))
        
        raise RuntimeError("Invalid heading designation for '{}'".format(message))


class BotIO:
    ## Keys
    PLOT_COMMAND_HELP_KEY = "plot_command_help"

    ## Defaults
    PLOT_COMMAND_HELP = CONFIG_OPTIONS.get(PLOT_COMMAND_HELP_KEY, "")


    def __init__(self, plane_pal, bot, **kwargs):
        self.plane_pal = plane_pal
        self.bot = bot

        self.plot_command_help = kwargs.get(self.PLOT_COMMAND_HELP_KEY, self.PLOT_COMMAND_HELP)

        self.path_parser = PathParser()
        self.plotter = plotter.Plotter()
        self.dynamo_db = dynamo_helper.DynamoHelper()

    ## Methods

    async def say(self, *args, **kwargs):
        await self.bot.say(*args, **kwargs)


    async def failed_command_feedback(self, message=None):
        ## Generate some feedback for the bot to give to users that mess up invocation
        output = "I couldn't understand the command"
        if(message):
            output += ", {}".format(message)
        if(self.plot_command_help):
            output += ". {}".format(self.plot_command_help)
        output += "."

        await self.bot.say(output)


    async def failed_upload_feedback(self, message=None):
        ## Generate some feedback for the bot to give to users when their map upload fails
        output = "Sorry, I couldn't upload your map"
        if(message):
            output += ", {}".format(message)
        output += "."

        await self.bot.say(output)


    async def upload_file(self, file_path, channel, content=None, callback=None):
        ## Pythonically open and upload the image to the given channel
        with open(file_path, "rb") as fd:
            try:
                await self.bot.send_file(channel, fd, content=content)
            except errors.HTTPException as e:
                utilities.debug_print("Error uploading file at: '{}'", e, debug_level=0)
                await self.failed_upload_feedback(e)
                return False

        ## Call the callback function, provided it exists
        if(callback):
            return callback()
        else:
            return True


    async def _plot(self, ctx, message, map_name):
        """Plots your given plane's path on the game map."""

        ## Parse the user's command
        try:
            path_obj = self.path_parser.parse_message(message)
        except RuntimeError as e:
            ## Give them some feedback if the command isn't understandable
            await self.failed_command_feedback(e)

            ## Put some information about the failed query into the database
            self.dynamo_db.put(dynamo_helper.DynamoItem(
                ctx.message.author.id,
                ctx.message.timestamp.timestamp(),
                ctx.message.channel.name,
                ctx.message.server.name,
                map_name,
                message,
                None
            ))
            return None
        else:
            ## Put some information about the successful query into the database
            self.dynamo_db.put(dynamo_helper.DynamoItem(
                ctx.message.author.id,
                ctx.message.timestamp.timestamp(),
                ctx.message.channel.name,
                ctx.message.server.name,
                map_name,
                message,
                str(path_obj)
            ))

        ## Get the file path for the final map image, and generate a callback to delete the image
        plotted_map = self.plotter.plot_plane_path(map_name, path_obj)
        map_path = self.plotter.file_controller.save_map(plotted_map)
        delete_map_callback = self.plotter.file_controller.create_delete_map_callback(map_path)

        ## Upload the file to the user's channel in Discord.
        return await self.upload_file(  map_path,
                                        ctx.message.channel,
                                        content="Here you go, <@{}>. Good luck!".format(ctx.message.author.id),
                                        callback=delete_map_callback )

    ## Commands

    @commands.command(pass_context=True, no_pm=True)
    async def erangel(self, ctx, *, message):
        """Plots your given plane's path on the map of Erangel."""
        return await self._plot(ctx, message, "erangel")


    @commands.command(pass_context=True, no_pm=True)
    async def miramar(self, ctx, *, message):
        """Plots your given plane's path on the map of Miramar."""
        return await self._plot(ctx, message, "miramar")


    @commands.command(pass_context=True, no_pm=True)
    async def e(self, ctx, *, message):
        """Alias for plotting on Erangel's map."""
        return await self._plot(ctx, message, "erangel")


    @commands.command(pass_context=True, no_pm=True)
    async def m(self, ctx, *, message):
        """Alias for plotting on Miramar's map."""
        return await self._plot(ctx, message, "miramar")
