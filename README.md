# `> DIGITAL_DEVIL_SERVER_BOT_(DDS-BOT)` <img width="39" height="42" alt="icon-loan" src="https://github.com/user-attachments/assets/5992a5d9-0d11-4cfc-bb54-30c588b9d0c8" />

[![Discord](https://img.shields.io/discord/1526401638879723550?style=for-the-badge&logo=discord&label=DDS-NET%20Discord&labelColor=FFF&color=%235965f2)]()
[![License](https://img.shields.io/github/license/ggnosis-dev/dds-bot?style=for-the-badge&labelColor=FFF)](https://github.com/ggnosis-dev/dds-bot/blob/main/LICENSE)

> [!NOTE]
> An invite link will be provided here shortly.
> Not currently looking for contributions.

A Digital Devil Collecting Discord bot game. Recruit **angels** and **demons** through negotiation, fuse them together, and work together with the rest of the server to increase its capabilities.

<img width="1569" height="902" src="https://github.com/user-attachments/assets/9193bf04-a916-47a3-a35d-83d41c462b15" />

## `> GAME_FEATURES`

Collectable Discord game bots often feel like single player experiences that just so happen to live in a shared space. That said, the main goals surrounding DDS-BOT is an attempt to answer that. 
Exactly how do we get a community to play together and feel included, even when jumping in late, while still balancing individual player progression? 

### `> ENCOUNTERS`
The first method includes **encounters** containing a **horde** of however many demons, allowing both the summoner and other players to interact simultaneously with them. 

It becomes more of a **social event**. If an encounter comes with a horde of 3, then every player has a chance of recruiting one until all three have been interacted with. Ping your friends for their own chance at a rare demon you summoned!

### `> NEGOTIATION_SYSTEM`
Each interaction involves the **negotiation system**, where you talk and respond to demons to make them eager to join you. Each interaction is logged on the main view once done, letting people know exactly who made that Chris the Car cry and drive away... 

Players who can identifying the tones and personality traits get rewarded for speed, but a system like this should help to reduce sniping which can sometimes be a major cause of frustration for casual players. 

<img width="1640" height="931" src="https://github.com/user-attachments/assets/90ff5e33-a2ea-41c4-af84-486dff7622f8" />

### `> FUSION`
Two demons can be **fused together** to bring life to a new one. Sometimes this may be the only way to get a specific one. Players can fuse **Elements** into their demons to summon another of its matching race, either a tier up or down from it.

There are also **Special Fusions**, recipes that require 3 or more demons to have been collected before they can be summoned. Sometimes, raising the **server level** will gift a **special fusion key** to the server.

<img width="1146" height="669" alt="sp_fuse" src="https://github.com/user-attachments/assets/4ff30ea2-7c66-4647-a961-113c81d74ad6" />

### `> SERVER_COMPENDIUM`
Alongside each player's own personal **party** and **compendium** (all registered demons), there is the **server compendium**. This system lets players contribute and **loan** their collection to boost server-wide capabilities. 

Its main function is to increase the **maximum rank encounter's will spawn at**, and it dictates progression. To balance this for newer or weaker players, spawning is dictated by **triangular distribution**. Spawn ranks peak near the party's average rank and taper off toward the server's maximum, so newer players will mostly see lower-ranked encounters. Knowing this, specific demons can also be **hunted** for by manipulating the party's average rank.

Weaker players are also not left out of building this compendium as more regular players will likely make party space for higher ranked contributions, leaving different, lower ranked demons available.

<img width="1147" height="931" alt="rags" src="https://github.com/user-attachments/assets/a2c691d6-27c0-4403-98f4-f0fc06a30831" />

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
- More dialogue options
- More demons and races
- Better tutorials
- Entries need filling
- Migrate DB to something with async writes (not really that important right now)
- Get the bot on servers
