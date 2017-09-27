import utilities
from discord.ext import commands

## Config
CONFIG_OPTIONS = utilities.load_config()


class Admin:
    ## Keys
    ADMINS_KEY = "admins"

    def __init__(self, plane_pal, bot_io=None):
        self.plane_pal = plane_pal
        self.bot_io = bot_io if bot_io else self.plane_pal.get_bot_io_cog()
        self.admins = CONFIG_OPTIONS.get(self.ADMINS_KEY, [])

    ## Methods

    ## Checks if a user is a valid admin
    def is_admin(self, name):
        return (str(name) in self.admins)

    ## Commands

    ## Root command for other admin-only commands
    @commands.group(pass_context=True, no_pm=True, hidden=True)
    async def admin(self, ctx):
        """Root command for the admin-only commands"""
    
        if(ctx.invoked_subcommand is None):
            if(self.is_admin(ctx.message.author)):
                await self.bot_io.say("Missing subcommand.".format(ctx.message.author.id))
                return True
            else:
                await self.bot_io.say("<@{}> isn't allowed to do that.".format(ctx.message.author.id))
                return False

        return False


    ## Tries to reload the preset phrases (admin only)
    @admin.command(pass_context=True, no_pm=True)
    async def reload_cogs(self, ctx):
        """Reloads the bot's cogs."""

        if(not self.is_admin(ctx.message.author)):
            await self.bot_io.say("<@{}> isn't allowed to do that.".format(ctx.message.author.id))
            return False

        count = self.plane_pal.module_manager.reload_all()
        total = len(self.plane_pal.module_manager.modules)

        loaded_cogs_string = "Loaded {} of {} cogs.".format(count, total)
        await self.bot_io.say(loaded_cogs_string)

        return (count >= 0)