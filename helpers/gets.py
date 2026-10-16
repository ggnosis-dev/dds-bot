import typing

from discord import Guild, Interaction, Member
from discord.ext import commands


def get_user_server(ctx: commands.Context) -> tuple:
	player = get_user(ctx)
	server = get_server(ctx)
	return player, server


def get_user_server_ids(ctx: commands.Context | Interaction) -> tuple:
	player = get_user(ctx)
	server = get_server(ctx)
	return player.id, server.id


def get_user(ctx: commands.Context | Interaction) -> Member:
	if isinstance(ctx, commands.Context):
		author = ctx.author
	elif isinstance(ctx, Interaction):
		author = ctx.user

	return typing.cast(Member, author)


def get_server(ctx) -> Guild:
	return typing.cast(Guild, ctx.guild)


def get_server_name(ctx: commands.Context) -> str:
	server = typing.cast(Guild, ctx.guild)
	return server.name
