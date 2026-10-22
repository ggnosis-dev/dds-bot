# `> DIGITAL_DEVIL_SERVER_BOT_(DDS-BOT)`

[![Discord](https://img.shields.io/discord/1526401638879723550?style=for-the-badge&logo=discord&label=DDS-NET%20Discord&labelColor=FFF&color=%235965f2)]()
[![License](https://img.shields.io/github/license/ggnosis-dev/dds-bot?style=for-the-badge&labelColor=FFF)](https://github.com/ggnosis-dev/dds-bot/blob/main/LICENSE)

> [!NOTE]
> An invite link will be provided here shortly.
> Not currently looking for contributions.
> Code is here for educational purposes.

A Digital Devil Collecting Discord bot game. Recruit **angels** and **demons** through negotiation, fuse them together, and work together with the rest of the server to increase its capabilities.

## `> GAME_FEATURES`

Collectable Discord games, to me, often felt like singular experiences that a person would have in a community that may or may not be playing with them. Many of them are regularly limited to player interaction through trading and, perhaps unintentionally, watching and sniping something when it pops up. 

How then can you encourage a community to play the same game while still balancing individual player progression? That's where the main design philosophy behind DDS-BOT was born; from that desire to see a server bot actually interact with as much of its community as possible.

### `> ENCOUNTERS`
The first method comes from each **encounter** containing a **horde** of however many demons, allowing both the summoner and other players to interact simultaneously with them. If an encounter came with a horde of 3, then every player has a chance of recruiting one until all three have been interacted with.

### `> NEGOTIATION_SYSTEM`
Each interaction involves the **negotiation system**, where you talk and respond to demons to make them eager to join you. Each interaction is logged on the main view once done, letting people know exactly who made that Poltergeist cry and run away... 

It can reward players for identifying the tones and personality traits, but a system like this should help to reduce sniping which can sometimes be a major cause of frustration for casual players. 

### `> FUSION`
Two demons can be **fused together** to summon a new one. Sometimes this may be the only way to get a specific demon. Players can fuse **Elements** into their demons to summon another of its matching race, either a tier up or down from it.

There are also **Special Fusions**, recipes that require 3 or more demons to have been collected before they can be summoned. Sometimes, raising the **server level** will gift a **special fusion key** to the server.

### `> SERVER_COMPENDIUM`
Alongside each player's own personal **party** and **compendium** (all registered demons), there is the **server compendium**. This system lets players contribute and **loan** their collection to boost server-wide capabilities. 

Its main function is to increase the **maximum rank encounter's will spawn at**, and it dictates progression. To balance this for newer or weaker players, spawning is dictated by **triangular distribution** where the weight is set by the player's average party rank. Knowing this, specific demons can also be **hunted** for by manipulating the party's average rank.

Weaker players are also not left out of building this compendium as more regular players will likely make party space for higher ranked contributions, leaving different, lower ranked demons available.

> [!IMPORTANT]
> The distribution still needs to be properly balanced with proper players.

## `> FUTURE_GOALS`
Planning to slow development for a bit while I start working on other projects but the things I'd like to add are:
- Balancing for encounters
  - Mainly to do with the spawn rank distribution
  - How many a horde should have
- Remove the gem hunted pop-up, I don't like it.
- Events
  - Kind of have these worked out already
- Better tutorials
