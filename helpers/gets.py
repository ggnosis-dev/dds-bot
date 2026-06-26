import typing

from discord import Guild
from discord.ext import commands


def get_player_server(ctx: commands.Context) -> tuple:
	player = ctx.author
	server = typing.cast(Guild, ctx.guild)
	return player, server


def get_player_server_ids(ctx: commands.Context) -> tuple:
	player = ctx.author
	server = typing.cast(Guild, ctx.guild)
	return player.id, server.id
