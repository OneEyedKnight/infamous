import discord
from PIL import ImageDraw


async def lvl(ctx, mon, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    lvl_ = await ctx.bot.db.fetchrow(
        "SELECT * FROM rpg_profile WHERE id=$1", user)

    if lvl_['xp'] > lvl_['lvl'] * 100:
        await ctx.send(
            msg1
        )
        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET lvl = $1 WHERE id=$2",
            lvl_['lvl'] + 1, user
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET xp = 0 WHERE id=$1",
            user
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET bal = bal + $1 WHERE id=$2",
            mon, user
        )
    else:
        await ctx.send(msg2)


async def mastery_lvl(ctx, mon, msg1, msg2, user=None):
    if not user:
        user = ctx.author.id

    lvl_ = await ctx.bot.db.fetchrow(
        "SELECT * FROM rpg_profile WHERE id=$1", user)

    if lvl_['xp'] > lvl_['lvl'] * 100:
        await ctx.send(
            msg1
        )
        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET lvl = $1 WHERE id=$2",
            lvl_['lvl'] + 1, user
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET xp = 0 WHERE id=$1",
            user
        )

        await ctx.bot.db.execute(
            "UPDATE rpg_profile SET bal = bal + $1 WHERE id=$2",
            mon, user
        )
    else:
        await ctx.send(msg2)


async def add_xp(ctx, xp, user=None):
    if not user:
        user = ctx.author.id
        
    await ctx.bot.db.execute(
        "UPDATE rpg_profile SET xp = xp + $1 WHERE id = $2",
        xp, user
    )


async def add_mastery_xp(ctx, xp, user=None):
    if not user:
        user = ctx.author.id

    await ctx.bot.db.execute(
        "UPDATE rpg_mastery SET xp = xp + $1 WHERE id = $2",
        xp, user
    )


async def add_money(ctx, mon, user=None):
    if not user:
        user = ctx.author

    await ctx.bot.db.execute(
        "UPDATE rpg_profile SET bal = bal + $1 WHERE id = $2",
        mon, user.id
    )


async def fetch_user(ctx, user=None):
    if not user:
        user = ctx.author.id

    p = await ctx.bot.db.fetchrow("SELECT * FROM rpg_profile WHERE id=$1",
                                  user)
    return p


async def fetch_mastery(ctx, user=None):
    if not user:
        user = ctx.author.id

    p = await ctx.bot.db.fetchrow("SELECT * FROM rpg_mastery WHERE id=$1",
                                  user)

    return p


async def item_class(class_):
    if class_ == "knight":
        return "Sword"

    if class_ == "hunter":
        return "Bow"

    if class_ == "sorcerer":
        return "Staff"

    if class_ == "sentinel":
        return "Crossbow"


def drawtext(x, y, text, font, image):
    draw = ImageDraw.Draw(image)
    draw.text((x + 2, y), text, fill='black', font=font)
    draw.text((x - 2, y), text, fill='black', font=font)
    draw.text((x, y + 2), text, fill='black', font=font)
    draw.text((x, y - 2), text, fill='black', font=font)
    draw.text((x, y), text, fill='white', font=font)
    return draw


def item_embed(item, thumbnail):
    embed = discord.Embed(color=0xba1c1c)
    embed.set_author(name=item[0])
    embed.description = item[7]
    embed.add_field(name="Type", value=item[1])
    embed.add_field(name="Price", value=item[2])
    embed.add_field(name="Damage", value=item[3])
    embed.add_field(name="Defense", value=item[4])
    embed.add_field(name="Class", value=item[5])
    embed.add_field(name="Mastery Level", value=item[6])
    embed.set_thumbnail(url=thumbnail)

    return embed


async def lb_embed(ctx, pfp):
    mast = await ctx.bot.db.fetchrow("SELECT * FROM rpg_mastery WHERE id=$1",
                                     pfp[0])
    embed = discord.Embed(color=0xba1c1c)
    member = ctx.guild.get_member(pfp[0])
    embed.set_author(name=member.name)
    embed.description = f"**Level:** {pfp[2]} \n" \
                        f"**Class:** {pfp[1]} \n" \
                        f"**Mastery Level:** {mast[1]}"

    embed.set_thumbnail(url=member.avatar_url)
    return embed


async def fetch_item(ctx, name, class_, user=None, inv=None):
    if not inv:
        inv = "rpg_inventory"

    if not user:
        user = ctx.author.id

    if inv == "rpg_shop":
        item = await ctx.bot.db.fetchrow("SELECT * FROM rpg_shop WHERE name=$1 AND class=$2", name, class_)
    else:
        item = await ctx.bot.db.fetchrow("SELECT * FROM rpg_inventory WHERE name=$1 AND owner=$2", name, user)

    return item
