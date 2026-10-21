from typing import Any, cast

from discord import Guild, Interaction, Member
from discord.ext import commands


def get_user_server(ctx: commands.Context) -> tuple:
	user = get_user(ctx)
	server = get_server(ctx)
	return user, server


def get_player_id(ctx: commands.Context) -> int:
	"""Added to context during the @checks.has_profile() check."""
	return ctx.player_id  # pyright: ignore[reportAttributeAccessIssue]


def get_server_id(ctx: commands.Context) -> int:
	server = get_server(ctx)
	return server.id


def get_user_id(ctx: commands.Context) -> int:
	if isinstance(ctx, commands.Context):
		author = ctx.author
	elif isinstance(ctx, Interaction):
		author = ctx.user

	return cast(int, author.id)


def get_user_server_ids(ctx: commands.Context | Interaction) -> tuple:
	player = get_user(ctx)
	server = get_server(ctx)
	return player.id, server.id


def get_user(ctx: commands.Context | Interaction) -> Member:
	if isinstance(ctx, commands.Context):
		author = ctx.author
	elif isinstance(ctx, Interaction):
		author = ctx.user

	return cast(Member, author)


def get_server(ctx: commands.Context | Interaction) -> Guild:
	return cast(Guild, ctx.guild)


def get_server_field(ctx: commands.Context, field: str) -> Any:
	server = get_server(ctx)
	return getattr(server, field)
