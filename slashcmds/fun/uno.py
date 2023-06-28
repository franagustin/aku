import discord
import settings
from games.uno.game import GameManager, UnoGameConfig
from discord import app_commands
logger = settings.logging.getLogger("game")

boolean_options = [
    app_commands.Choice(name="True", value=1),
    app_commands.Choice(name="False", value=0)
]

@app_commands.command()
@app_commands.guild_only()
@app_commands.describe(randomize="Randomize player list at start?", stackable="Do you want to allow stack +2?",turn_time="How long is each turn? (in seconds)")
@app_commands.choices(randomize=boolean_options, stackable=boolean_options)
@app_commands.checks.bot_has_permissions(manage_threads=True, send_messages_in_threads=True)
async def uno(ctx: discord.Interaction, randomize: int = 0, stackable: int= 1, turn_time: int = 180):
    """Lose all your friends."""
    try:
        configuration = UnoGameConfig(client=ctx.client, turn_time=180)

        await ctx.response.defer()
        if randomize == 1: configuration.randomize_players = True
        if stackable == 0: configuration.stackable = False
        configuration.turn_time = turn_time

        game_manager = GameManager(ctx=ctx, config=configuration)
        await game_manager.start_game()
    except:
        print("An error occurred")
    finally:
        print("UNO command ended")
        # if start_menu.foo == None: print("Timedout")
        # if start_menu.foo == True: 
            # Comenzar el juego

async def setup(bot):
    bot.tree.add_command(uno)