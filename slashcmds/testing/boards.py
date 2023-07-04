from discord import Interaction, app_commands

from games.boards.boards import Board, CheckersBoard


@app_commands.command()
@app_commands.describe(
    width="Desired number of columns for this board.",
    height="Desired number of rows for this board.",
    checked="Whether it should be checked or not.",
)
async def board(ctx: Interaction, width: int, height: int, checked: str):
    board = Board(width, height, checked=checked.lower() == "yes")
    await ctx.response.send_message(str(board))


@app_commands.command()
async def checkers(ctx: Interaction):
    board = CheckersBoard(8, 8, checked=True)
    await ctx.response.send_message(str(board))


async def setup(bot):
    bot.tree.add_command(board)
    bot.tree.add_command(checkers)
