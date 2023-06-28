import random
import discord
from math import floor
from game_base import GameBase
from typing import Tuple

# from games.uno.game import UNOGame

######## EMBEDS ##########

GAME_START_EMBED = discord.Embed().set_author(name="<< UNO GAME NOT STARTED >>")
GAME_STATUS_EMBED = discord.Embed().set_author(name="<< UNO GAME STATE MESSAGE>>").add_field(name="Orientation", value="⤵ DOWN").add_field(name="Stack", value="0")
GAME_END_EMBED = discord.Embed().set_author(name="<< UNO GAME ENDED >>")
GAME_CANCELED_EMBED = discord.Embed().set_author(name="<< UNO GAME CANCELLED >>")

##########################

class WildColorSelector(discord.ui.View):
    foo: bool = False

    def __init__(self, *, timeout: float | None = 60, card):
        super().__init__(timeout=timeout)
        self.card = card

    @discord.ui.button(emoji="🔴")
    async def red_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.foo = True
        self.card.color = "R"
        self.stop()

    @discord.ui.button(emoji="🟢")
    async def green_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.foo = True
        self.card.color = "G"
        self.stop()

    @discord.ui.button(emoji="🔵")
    async def blue_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.foo = True
        self.card.color = "B"
        self.stop()

    @discord.ui.button(emoji="🟡")
    async def yellow_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.foo = True
        self.card.color = "Y"
        self.stop()


class DrawOrThrowView(discord.ui.View):
    foo: bool = False

    @discord.ui.button(label="Throw")
    async def throw_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.foo = True
        self.stop()

    @discord.ui.button(label="Keep")
    async def keep_button(self, interaction: discord.Interaction, button):
        await interaction.response.defer()
        self.stop()
    

class CardSelector(discord.ui.Select):

    async def callback(self, interaction: discord.Interaction):
        card_id = interaction.data.get('values')[0]
        card = self.view.game.current_player.hand.get_card_by_id(card_id)
        player = self.view.game.get_player_by_id(interaction.user.id)
        # check if card is wild and wait for selection
        if card.is_wild:
            colors = ["R", "Y", "G", "B"] # select a random color if the player doesn't select
            self.view.second_action = True
            self.view.children_view = WildColorSelector(card=card)
            await interaction.response.send_message(content="Select a color for your WILD, you have 60 seconds.", view=self.view.children_view,ephemeral=True)
            await self.view.children_view.wait()

            # if not self.view.children_view.foo: card.color = random.choice(colors) # if player didn't select a color...

            self.view.second_action = False
            self.view.children_view = None

        # play card
        await self.view.game.play_card(player, card_id)

        # close turn options view
        if not self.view.foo:
            await self.view.close_view()

class DrawButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        # if custom id stack resolve, resolve stack...
        if interaction.data.get('custom_id') == "stack_resolve":
            self.view.game.last_action = f"{self.view.game.current_player.name} draw {self.view.game.stack} cards, last card is: "
            await self.view.game.stack_resolve(force_skip=False)
        else:
            # grab a card
            card = self.view.game.draw_card(self.view.game.current_player)
            if card.validate(self.view.game.last_card) and not card.is_wild:
            # if can be played make second action true, and wait
                self.view.second_action = True
                self.children_view = DrawOrThrowView(timeout=None)
                await interaction.response.send_message(content=f"Do you want to keep `[{card.name}]` {card.emoji} or play it?", ephemeral=True, view= self.children_view)
                await self.children_view.wait()
                
                if self.children_view.foo:
                    await self.view.game.play_card(self.view.game.current_player, card.id, False)
                    self.view.game.last_action = f"{self.view.game.current_player.name} draw a card an played it: "

                self.view.second_action = False
                self.view.children_view = None

            self.view.game.last_action = f"{self.view.game.current_player.name} draw a card, the last card is: "
        # if not just pass and close the view
        if not self.view.foo: 
            self.view.game.skip_turn()
            await self.view.close_view()

class TurnOptionsView(discord.ui.View):
    foo: bool = False # tells me if the view is being closed, avoiding trying to close it again

    def __init__(self, *, timeout: float | None = None, game: GameBase, mother_view, hand_user_id:int):
        super().__init__(timeout=timeout)
        self.game = game
        self.ephemeral_message: discord.WebhookMessage = None
        self.second_action : bool = False
        self.mother_view: discord.ui.View = mother_view
        self.children_view: discord.ui.View | None = None
        self.hand_user_id: int = None

    # concludes the turn and send a new turn message
    async def close_view(self):
        # player = self.game.get_player_by_id(self.hand_user_id)
        await self.ephemeral_message.edit(view=None)
        if self.ephemeral_message is not None: self.ephemeral_message = None # deletes the hand message webhook
        if self.children_view is not None: self.children_view.stop()
        self.mother_view.opened = False

        if self.game.status.name == "PLAYING":
            color = discord.ButtonStyle.blurple if self.game.stack == 0 else discord.ButtonStyle.danger
            new_view = await self.game.message_handler.create_new_menu(HandButton(label="Hand", custom_id="hand_button", style=color))
            await self.game.message_handler.send_status_message(view=new_view)
            self.mother_view.stop()
        elif self.game.status.name == "CANCELLED" or self.game.status.name == "FINISHED":
            await self.game.message_handler.send_results()
            self.mother_view.stop()
        self.stop()
    
    def build_turn_menu(self):
        valid_hand = []
        # check if player has valid hand and then add card select menu
        # delete wild options in card selector if is the last card or there's a stack
        if self.game.stack > 0 and self.game.data.stackable:
            valid_hand = self.game.current_player.hand.generate_plus_hand()
        else:
            valid_hand = self.game.current_player.hand.generate_valid_hand(self.game.last_card)

        # if valid hand has items, make the select menu and append
        if len(valid_hand) > 0:
            card_selector: CardSelector = CardSelector(custom_id="send_card", options=[])
            for card in valid_hand:
                    card_selector.append_option(discord.SelectOption(label=card.name, emoji=card.color_emoji, value=card.id))
            self.add_item(card_selector)

        # check if there's an stack
        # with this make the draw button differente (draw x cards and red)
        if self.game.stack > 0 and self.game.data.stackable:
            self.add_item(DrawButton(label=f"Draw {self.game.stack} cards", style=discord.ButtonStyle.danger, custom_id="stack_resolve"))
        else:
            # add draw button
            self.add_item(DrawButton(label="Draw"))
        return self

########################################################################################################
class HandButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        # print("This is the hand button")
        self.game = self.view.game
        player = self.game.get_player_by_id(interaction.user.id) # the player who touched the button
        player_emoji_hand = player.hand.emoji_hand(self.view.game.emoji_collection)

        # checks if it's not player's turn:
        if self.game.current_player.id != interaction.user.id:
            await interaction.response.send_message(content=player_emoji_hand, ephemeral=True)

        # is the player turn
        else:
            # checks if hand has been opened before:
            if self.view.opened:
                # edit the last hand message
                await self.view.last_hand_msg.edit(content=player_emoji_hand, view=None)

            if self.view.TURN_VIEW is not None:
                if self.view.TURN_VIEW.second_action: return await interaction.response.send_message("You've already make your choice...", ephemeral=True)

            # remember the hand button:
            await interaction.response.defer(ephemeral=True)
            self.view.TURN_VIEW = TurnOptionsView(timeout=None, game=self.game, mother_view=self.view, hand_user_id=interaction.user.id).build_turn_menu()
            self.view.opened = True
            self.view.last_hand_msg = await interaction.followup.send(content=player_emoji_hand, ephemeral=True, view=self.view.TURN_VIEW)
            self.view.TURN_VIEW.ephemeral_message = self.view.last_hand_msg

class PlayerTurnView(discord.ui.View):
    # Si el turno del jugador termina...
    async def on_timeout(self):
        if self.game is not None: 
            if self.game.status.name == "PLAYING":
                print("Timeout turn")
                if self.TURN_VIEW is not None: 
                    self.TURN_VIEW.foo = True
                    self.TURN_VIEW.stop()
                    if self.TURN_VIEW.children_view is not None: self.TURN_VIEW.children_view.stop()
                await self.game.punish_user()

    def __init__(self, *, timeout: float | None = 180, game: GameBase):
        super().__init__(timeout=timeout)
        self.game = game
        self.opened: bool = False # this will remember if the player used the button inside the view.
        self.last_hand_msg : discord.WebhookMessage | None = None
        self.TURN_VIEW = None

    async def interaction_check(self, interaction: discord.Interaction):
        # Revisar si el usuario se encuentra en el juego
        player = self.game.get_player_by_id(interaction.user.id)
        if player not in self.game.players:
            await interaction.response.send_message("> You are not even playing, are you dumb?", ephemeral=True)
            return False
        else: return True
        

class GameDiscordInterface:
    def __init__(self, game: GameBase) -> None:
        self.game = game
        self.thread : discord.Thread = game.thread # change to discord.Thread
        self.last_view: discord.ui.View | None = None # this is for closing the game at the end
    
    async def send_status_message(self, view: discord.ui.View | None = None):
        GAME_STATUS_EMBED.description = (
            f"{self.game.last_action} `[{self.game.last_card.name}]`\n"
            f"```md\n{self.game.player_list}```"
        )
        GAME_STATUS_EMBED.color = self.game.last_card.color_code
        GAME_STATUS_EMBED.set_thumbnail(url=self.game.last_card.image_url)
        GAME_STATUS_EMBED.set_footer(text=f"You have {floor(self.game.data.turn_time / 60)} minutes to play.")
        GAME_STATUS_EMBED.set_field_at(index=0,name="Orientation: ", value=f"{'⏬ DOWN' if self.game.is_clockwise else '⏫ UP'}")
        GAME_STATUS_EMBED.set_field_at(index=1,name="Stack: ", value=self.game.stack)
        self.last_view = view # save the last view used.
        await self.thread.send(content=f"It's <@{self.game.current_player.id}>'s turn.",embed=GAME_STATUS_EMBED, view=view)


    async def create_new_menu(self, *buttons: Tuple[discord.ui.Button, ...]) -> PlayerTurnView:
        player_turn_menu = PlayerTurnView(timeout=self.game.data.turn_time, game=self.game)
        for button in buttons:
            player_turn_menu.add_item(button)
        return player_turn_menu

    async def send_results(self):
        self.last_view.stop()
        if self.game.status.name == "CANCELLED":
            await self.thread.parent.send(embed=GAME_CANCELED_EMBED)
        if self.game.status.name == "FINISHED":
            for player in self.game.players:
                await self.game.data.client.db.add_uno_game(user_id=player.id)

            await self.game.data.client.db.add_uno_win(user_id=self.game.winner.id) # ADD UNO WIN POINT TO THE WINNER

            DB_USER = await self.game.data.client.db.user(user_id=self.game.winner.id)
            
            GAME_END_EMBED.description = (
                f"Game ended, the winner is {self.game.winner.name}\n"
                f"## Win number {DB_USER['wins']}, Game number {DB_USER['games']}\n ### Win rate: {(DB_USER['wins']/DB_USER['games']) * 100}%"
            )
            GAME_END_EMBED.color = self.game.last_card.color_code
            GAME_END_EMBED.set_thumbnail(url=self.game.last_card.image_url)
            GAME_END_EMBED.set_footer(text=f"Duration: {round(self.game.calculate_duration())} minutes.")
            await self.thread.starter_message.delete()
            await self.thread.parent.send(embed=GAME_END_EMBED)
        del self.game.data.client.games[self.game.thread.guild.id]
        await self.thread.delete()
