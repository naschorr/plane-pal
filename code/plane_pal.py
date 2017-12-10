import importlib
import sys
import os
import asyncio
import time
from collections import OrderedDict

import discord
from discord.ext import commands

import utilities
import bot_io
import plotter
import admin

## Config
CONFIG_OPTIONS = utilities.load_config()


## Todo: Genericize this module manager out into its own module and put on PyPI
class ModuleEntry:
    def __init__(self, cls, *init_args, **init_kwargs):
        self.module = sys.modules[cls.__module__]
        self.cls = cls
        self.name = cls.__name__
        self.args = init_args
        self.kwargs = init_kwargs

    ## Methods

    ## Returns an invokable object to instantiate the class defined in self.cls
    def get_class_callable(self):
        return getattr(self.module, self.name)


class ModuleManager:
    def __init__(self, plane_pal, bot):
        self.plane_pal = plane_pal
        self.bot = bot
        self.modules = OrderedDict()

    ## Methods

    ## Registers a module, class, and args necessary to instantiate the class
    def register(self, cls, *init_args, **init_kwargs):
        module_entry = ModuleEntry(cls, *init_args, **init_kwargs)

        self.modules[module_entry.name] = module_entry

        ## Add the module to the bot, provided it hasn't already been added.
        if(not self.bot.get_cog(module_entry.name)):
            cog_cls = module_entry.get_class_callable()
            self.bot.add_cog(cog_cls(*module_entry.args, **module_entry.kwargs))


    ## Reimport a single module
    def _reload_module(self, module):
        try:
            importlib.reload(module)
        except Exception as e:
            print("Error: ({}) reloading module: {}".format(e, module))
            return False
        else:
            return True


    ## Reload a cog attached to the bot
    def _reload_cog(self, cog_name):
        module_entry = self.modules.get(cog_name)
        assert module_entry is not None

        self.bot.remove_cog(cog_name)
        self._reload_module(module_entry.module)
        cog_cls = module_entry.get_class_callable()
        self.bot.add_cog(cog_cls(*module_entry.args, **module_entry.kwargs))


    ## Reload all of the registered modules
    def reload_all(self):
        counter = 0
        for module_name in self.modules:
            try:
                self._reload_cog(module_name)
            except Exception as e:
                print("Error: {} when reloading cog: {}".format(e, module_name))
            else:
                counter += 1

        print("Loaded {}/{} cogs.".format(counter, len(self.modules)))
        return counter


class PlanePal:
    ## Keys and Defaults
    ## Basically, any given class can be configured by changing the respective value for the
    ## desired key in config.json (see the Keys section at the top of each class for a list of
    ## keys). However, if you want to use Hawking as a part of something else, you may want to
    ## dynamically configure objects as necessary. Thus, you can also instantiate classes with
    ## keyworded arguments, which will then override any existing defaults, or config.json data.
    ## The existing defaults in each class are sort of like a fallback, in case the config.json is
    ## broken in some way.

    ## Keys
    ACTIVATION_STR_KEY = "activation_str"
    DESCRIPTION_KEY = "description"
    TOKEN_KEY = "token"
    TOKEN_FILE_KEY = "token_file"
    TOKEN_FILE_PATH_KEY = "token_file_path"

    ## Defaults
    ACTIVATION_STR = CONFIG_OPTIONS.get(ACTIVATION_STR_KEY, "|")
    DESCRIPTION = CONFIG_OPTIONS.get(DESCRIPTION_KEY, "Plane Pal for Discord")
    TOKEN_FILE = CONFIG_OPTIONS.get(TOKEN_FILE_KEY, "token.json")
    TOKEN_FILE_PATH = CONFIG_OPTIONS.get(TOKEN_FILE_PATH_KEY, os.sep.join([utilities.get_root_path(), TOKEN_FILE]))

    ## Init the bot, and attach base cogs
    def __init__(self, **kwargs):
        self.activation_str = kwargs.get(self.ACTIVATION_STR_KEY, self.ACTIVATION_STR)
        self.description = kwargs.get(self.DESCRIPTION_KEY, self.DESCRIPTION)
        self.token_file_path = kwargs.get(self.TOKEN_FILE_PATH_KEY, self.TOKEN_FILE_PATH)

        ## Init bot and module manager
        self.bot = commands.Bot(
            command_prefix=commands.when_mentioned_or(self.activation_str),
            description=self.description
        )
        self.module_manager = ModuleManager(self, self.bot)

        ## Register the modules (Order of registration is important, make sure dependancies are loaded first)
        self.module_manager.register(plotter.Plotter)
        self.module_manager.register(bot_io.BotIO, self, self.bot)
        self.module_manager.register(admin.Admin, self)

        ## Let us know when the bot is ready to go
        @self.bot.event
        async def on_ready():
            print("Logged in as '{}' (id:{})".format(self.bot.user.name, self.bot.user.id))

    ## Methods

    def get_cog(self, cls_name):
        return self.bot.get_cog(cls_name)


    def get_bot_io_cog(self):
        return self.bot.get_cog("BotIO")


    def run(self):
        ## Keep bot going despite any misc service errors
        try:
            self.bot.run(utilities.load_json(self.token_file_path)[self.TOKEN_KEY])
        except Exception as e:
            utilities.debug_print("Critical exception when running bot", e, debug_level=0)
            time.sleep(1)
            self.run()


## Main
if(__name__ == "__main__"):
    PlanePal().run()
