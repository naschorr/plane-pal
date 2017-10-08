import re
from math import sqrt

from discord import errors
from discord.ext import commands

import utilities
import plotter
import legend

## Config
CONFIG_OPTIONS = utilities.load_config()


class GridObject:
    ## Keys
    MAX_SECTIONS_KEY = "max_sections"

    ## Defaults
    MAX_SECTIONS = CONFIG_OPTIONS.get(MAX_SECTIONS_KEY, 9)    # 3x3 subgrid in each grid on the map


    def __init__(self, x, y, section=None):
        ## Todo: more checks for data integrity
        self.x = x.lower()
        self.y = y.lower()
        self.section = int(section) if section else None

    ## Methods

    def get_true_x(self, pixels_per_km):
        ## True X calculated from the left side of the image

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
        raw = "('{}', '{}', '{}') @ '{}'"
        return raw.format(self.grid_obj.x, self.grid_obj.y, self.grid_obj.section, self.heading_obj.heading)


class PathParser:
    ## Keys
    GRID_REGEX_PATTERN_KEY = "grid_regex_pattern"
    HEADING_REGEX_PATTERN_KEY = "heading_regex_pattern"

    ## Defaults
    GRID_REGEX_PATTERN = CONFIG_OPTIONS.get(GRID_REGEX_PATTERN_KEY, r"([a-hA-H])([i-pI-P])([1-9]?)")
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
        match = self.grid_regex.search(message)
        if(match):
            message = message[match.end():]
            x = match.group(1)
            y = match.group(2)
            section = match.group(3)

            if(x and y):
                return GridObject(x, y, section), message
            elif(y and not x):
                raise RuntimeError("Invalid X grid marker '{}'".format(x))
            elif(x and not y):
                raise RuntimeError("Invalid Y grid marker '{}'".format(y))
            else:
                raise RuntimeError("Invalid X and Y grid markers '{}', '{}'".format(x, y))

        raise RuntimeError("Invalid grid marker for '{}'".format(message))


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


    async def _plot(self, ctx, message):
        """Plots your given plane's path on the game map."""

        ## Parse the user's command
        try:
            path_obj = self.path_parser.parse_message(message)
        except RuntimeError as e:
            ## Give them some feedback if the command isn't understandable
            await self.failed_command_feedback(e)
            return None

        ## Handy debug output
        print("Plotting: {} for '{}'".format(path_obj, ctx.message.author))

        ## Get the file path for the final map image, and generate a callback to delete the image
        map_path = self.plotter.plot_plane_path(path_obj)
        delete_map_callback = self.plotter.file_controller.create_delete_map_callback(map_path)

        ## Upload the file to the user's channel in Discord.
        return await self.upload_file(  map_path,
                                        ctx.message.channel,
                                        content="Here you go, <@{}>. Good luck!".format(ctx.message.author.id),
                                        callback=delete_map_callback )

    ## Commands

    @commands.command(pass_context=True, no_pm=True)
    async def plot(self, ctx, *, message):
        """Plots your given plane's path on the game map."""
        return await self._plot(ctx, message)


    @commands.command(pass_context=True, no_pm=True, hidden=True)
    async def path(self, ctx, *, message):
        """Alias for the plot command."""
        return await self._plot(ctx, message)


    @commands.command(pass_context=True, no_pm=True)
    async def p(self, ctx, *, message):
        """Alias for the plot command."""
        return await self._plot(ctx, message)
