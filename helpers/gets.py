import typing

from discord import Guild, Member
from discord.ext import commands


def get_player_server(ctx: commands.Context) -> tuple:
	player = get_player(ctx)
	server = get_server(ctx)
	return player, server


def get_player_server_ids(ctx: commands.Context) -> tuple:
	player = get_player(ctx)
	server = get_server(ctx)
	return player.id, server.id


def get_player(ctx) -> Member:
	return typing.cast(Member, ctx.author)


def get_server(ctx) -> Guild:
	return typing.cast(Guild, ctx.guild)


def get_server_name(ctx: commands.Context) -> str:
	server = typing.cast(Guild, ctx.guild)
	return server.name
