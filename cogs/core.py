import discord
from discord.ext import commands, tasks
import database
import logging
import random

# --- Constants ---
MESSAGE_ACTIVITY_POINTS = 1
MESSAGE_GAMBLING_POINTS = 2
VOICE_ACTIVITY_POINTS = 10
VOICE_GAMBLING_POINTS = 20

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_activity_check.start()
        self.monthly_reset_task.start()
        logging.info("Core cog loaded and tasks started.")

    def cog_unload(self):
        self.voice_activity_check.cancel()
        self.monthly_reset_task.cancel()

    # --- Event Listeners ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        database.add_points(
            message.guild.id,
            message.author.id,
            activity_points_to_add=MESSAGE_ACTIVITY_POINTS,
            gambling_points_to_add=MESSAGE_GAMBLING_POINTS
        )

    # --- Background Tasks ---
    @tasks.loop(minutes=10)
    async def voice_activity_check(self):
        logging.info("Running voice activity check...")
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                # Award points only if there are at least 2 non-muted/deafened users
                active_users = [m for m in vc.members if not m.voice.self_mute and not m.voice.self_deaf]
                if len(active_users) > 1:
                    for member in active_users:
                        if not member.bot:
                            database.add_points(
                                guild.id,
                                member.id,
                                activity_points_to_add=VOICE_ACTIVITY_POINTS,
                                gambling_points_to_add=VOICE_GAMBLING_POINTS
                            )
                            logging.info(f"Awarded points to {member.display_name} in {guild.name} for voice activity.")

    @voice_activity_check.before_loop
    async def before_voice_activity_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def monthly_reset_task(self):
        """Checks daily if it's the first of the month to reset monthly points."""
        now = datetime.utcnow()
        if now.day == 1:
            logging.info(f"It's the first day of the month. Resetting monthly points for all guilds.")
            for guild in self.bot.guilds:
                database.reset_monthly_points(guild.id)
                logging.info(f"Reset monthly points for {guild.name}.")

    @monthly_reset_task.before_loop
    async def before_monthly_reset_task(self):
        await self.bot.wait_until_ready()

    # --- Leaderboard Commands ---
    @commands.command(name='top', help='Shows the leaderboard for activity points. Use `$top monthly` for this month.')
    async def top(self, ctx, period: str = 'all'):
        if period == 'monthly':
            point_type = 'monthly_activity_points'
            title = "🏆 Top 10 Most Active Users This Month"
        else:
            point_type = 'activity_points'
            title = "🏆 Top 10 Most Active Users (All Time)"

        leaderboard_data = database.get_leaderboard(ctx.guild.id, point_type=point_type)
        embed = discord.Embed(title=title, color=discord.Color.gold())
        if not leaderboard_data:
            embed.description = "No activity points have been recorded yet."
        else:
            leaderboard_list = []
            for i, row in enumerate(leaderboard_data):
                member = ctx.guild.get_member(row['user_id'])
                display_name = member.display_name if member else f"Unknown User (ID: {row['user_id']})"
                points = row[point_type]
                leaderboard_list.append(f"**{i+1}. {display_name}**: {points} AP")
            embed.description = "\n".join(leaderboard_list)
        await ctx.send(embed=embed)

    @commands.command(name='wallet', help='Shows the leaderboard for the richest users.')
    async def wallet(self, ctx):
        leaderboard_data = database.get_leaderboard(ctx.guild.id, point_type='gambling_points')
        settings = database.get_guild_settings(ctx.guild.id)
        currency_name = settings['currency_name']
        embed = discord.Embed(title=f"💰 Top 10 Richest Users ({currency_name})", color=discord.Color.green())

        if not leaderboard_data:
            embed.description = "No one has any money yet."
        else:
            leaderboard_list = []
            for i, row in enumerate(leaderboard_data):
                member = ctx.guild.get_member(row['user_id'])
                display_name = member.display_name if member else f"Unknown User (ID: {row['user_id']})"
                leaderboard_list.append(f"**{i+1}. {display_name}**: {row['gambling_points']} {currency_name}")
            embed.description = "\n".join(leaderboard_list)
        await ctx.send(embed=embed)

    # --- Economy Commands ---
    @commands.command(name='balance', aliases=['bal'], help='Checks your gambling points balance.')
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_data = database.get_user_data(ctx.guild.id, member.id)
        settings = database.get_guild_settings(ctx.guild.id)
        currency_name = settings['currency_name']
        balance = user_data['gambling_points']
        await ctx.send(f"**{member.display_name}** has **{balance} {currency_name}**.")

    @commands.command(name='bet', help='Bets a certain amount of your currency.')
    async def bet(self, ctx, amount: int):
        if amount <= 0:
            return await ctx.send("You must bet a positive amount.")

        user_data = database.get_user_data(ctx.guild.id, ctx.author.id)
        balance = user_data['gambling_points']
        if amount > balance:
            return await ctx.send("You cannot bet more than you have.")

        settings = database.get_guild_settings(ctx.guild.id)
        win_chance = settings['bet_win_chance']

        if random.randint(1, 100) <= win_chance:
            # Win: The amount is doubled, so the net gain is the original amount.
            new_balance = database.update_gambling_points(ctx.guild.id, ctx.author.id, amount)
            await ctx.send(f"🎉 **You won!** You received **{amount}**. Your new balance is **{new_balance}**.")
        else:
            # Lose
            new_balance = database.update_gambling_points(ctx.guild.id, ctx.author.id, -amount)
            await ctx.send(f"😢 **You lost!** You lost **{amount}**. Your new balance is **{new_balance}**.")

    # --- Shop Commands ---
    @commands.command(name='shop', help='Displays the items available for purchase.')
    async def shop(self, ctx):
        items = database.get_shop_items(ctx.guild.id)
        settings = database.get_guild_settings(ctx.guild.id)
        currency_name = settings['currency_name']

        if not items:
            return await ctx.send("The shop is currently empty. An admin can add items with `$shopadmin add`.")

        embed = discord.Embed(title="Role Shop", color=discord.Color.teal())
        description = "Buy a role with the `$buy <item_id>` command.\n\n"
        for item in items:
            role = ctx.guild.get_role(item['role_id'])
            if role:
                description += f"**ID: {item['item_id']}** | **{role.name}** - `{item['price']}` {currency_name}\n"
        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name='buy', help='Buys an item (role) from the shop.')
    async def buy(self, ctx, item_id: int):
        item = database.get_shop_item(item_id)
        if not item or item['guild_id'] != ctx.guild.id:
            return await ctx.send("That item ID is not valid.")

        role = ctx.guild.get_role(item['role_id'])
        if not role:
            return await ctx.send("The role for this item no longer exists. An admin needs to remove this item.")

        user_data = database.get_user_data(ctx.guild.id, ctx.author.id)
        balance = user_data['gambling_points']

        if balance < item['price']:
            return await ctx.send(f"You don't have enough currency to buy this. You need `{item['price']}`.")

        if role in ctx.author.roles:
            return await ctx.send("You already have this role!")

        try:
            database.update_gambling_points(ctx.guild.id, ctx.author.id, -item['price'])
            await ctx.author.add_roles(role, reason="Purchased from shop")
            await ctx.send(f"You have successfully purchased the **{role.name}** role!")
        except discord.Forbidden:
            await ctx.send("I don't have the necessary permissions to assign roles.")
            database.update_gambling_points(ctx.guild.id, ctx.author.id, item['price']) # Refund
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
            database.update_gambling_points(ctx.guild.id, ctx.author.id, item['price']) # Refund

    # --- Admin Commands ---
    @commands.group(name='shopadmin', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def shopadmin(self, ctx):
        await ctx.send("Invalid subcommand. Use `$shopadmin add` or `$shopadmin remove`.")

    @shopadmin.command(name='add')
    @commands.has_permissions(administrator=True)
    async def shop_add(self, ctx, role: discord.Role, price: int):
        if price < 0:
            return await ctx.send("Price cannot be negative.")
        if database.add_shop_item(ctx.guild.id, role.id, price):
            await ctx.send(f"Added the **{role.name}** role to the shop for `{price}` currency.")
        else:
            await ctx.send("That role is already in the shop.")

    @shopadmin.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def shop_remove(self, ctx, item_id: int):
        if database.remove_shop_item(item_id):
            await ctx.send(f"Item ID `{item_id}` removed from the shop.")
        else:
            await ctx.send(f"Could not find an item with ID `{item_id}`.")

    @commands.command(name='givepoints')
    @commands.has_permissions(administrator=True)
    async def givepoints(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("Amount must be positive.")
        database.update_gambling_points(ctx.guild.id, member.id, amount)
        await ctx.send(f"Gave **{amount}** currency to **{member.display_name}**.")

    @commands.command(name='takepoints')
    @commands.has_permissions(administrator=True)
    async def takepoints(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("Amount must be positive.")
        database.update_gambling_points(ctx.guild.id, member.id, -amount)
        await ctx.send(f"Took **{amount}** currency from **{member.display_name}**.")

async def setup(bot):
    await bot.add_cog(Core(bot))
