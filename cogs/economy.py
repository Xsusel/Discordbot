import discord
from discord.ext import commands, tasks
import database
from datetime import datetime, timedelta

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_payout = datetime.utcnow()
        self.award_currency_task.start()
        print("Economy cog loaded and earning task started.")

    def cog_unload(self):
        self.award_currency_task.cancel()

    @tasks.loop(minutes=10)
    async def award_currency_task(self):
        """Periodically awards currency to users based on their activity."""
        print(f"Running activity payout task... Last payout was at {self.last_payout.strftime('%Y-%m-%d %H:%M:%S')}")

        # We need to iterate over all guilds the bot is in
        for guild in self.bot.guilds:
            # Get activity scores for all users since the last payout
            activity_scores = database.get_activity_scores_since(guild.id, self.last_payout)

            if not activity_scores:
                continue

            print(f"Found {len(activity_scores)} active user(s) in {guild.name} to reward.")
            for user_activity in activity_scores:
                user_id = user_activity['user_id']
                # Award currency based on activity score. Let's say 1 activity point = 10 currency.
                # This can be made configurable later if needed.
                amount_to_award = int(user_activity['activity_score'] * 10)

                if amount_to_award > 0:
                    database.update_wallet_balance(guild.id, user_id, amount_to_award)
                    print(f"Awarded {amount_to_award} currency to user {user_id} in guild {guild.id}.")

        # Update the last payout time for the next run
        self.last_payout = datetime.utcnow()

    @award_currency_task.before_loop
    async def before_award_currency_task(self):
        await self.bot.wait_until_ready()

    # --- User-Facing Economy Commands ---
    @commands.command(name='balance', aliases=['bal'])
    async def balance(self, ctx, member: discord.Member = None):
        """Checks your or another user's currency balance."""
        member = member or ctx.author
        balance = database.get_wallet_balance(ctx.guild.id, member.id)
        settings = database.get_economy_settings(ctx.guild.id)
        currency_name = settings['currency_name']
        await ctx.send(f"**{member.display_name}** has **{balance} {currency_name}**.")

    @commands.command(name='top', aliases=['leaderboard'])
    async def top(self, ctx):
        """Displays the leaderboard of the richest users."""
        top_users = database.get_top_balances(ctx.guild.id, 10)
        settings = database.get_economy_settings(ctx.guild.id)
        currency_name = settings['currency_name']

        if not top_users:
            await ctx.send("There's no one on the leaderboard yet!")
            return

        embed = discord.Embed(title=f"Top 10 Richest Users", color=discord.Color.gold())
        description = []
        for i, user_row in enumerate(top_users):
            user = self.bot.get_user(user_row['user_id']) or f"User ID: {user_row['user_id']}"
            display_name = user.display_name if isinstance(user, discord.User) else str(user)
            description.append(f"**{i+1}. {display_name}**: {user_row['balance']} {currency_name}")

        embed.description = "\n".join(description)
        await ctx.send(embed=embed)

    @commands.command(name='shop')
    async def shop(self, ctx):
        """Displays the items available for purchase."""
        items = database.get_shop_items(ctx.guild.id)
        settings = database.get_economy_settings(ctx.guild.id)
        currency_name = settings['currency_name']

        if not items:
            await ctx.send("The shop is currently empty. An admin can add items with `$shop add`.")
            return

        embed = discord.Embed(title="Role Shop", color=discord.Color.teal())
        description = "Buy a role with the `$buy <item_id>` command.\n\n"
        for item in items:
            role = ctx.guild.get_role(item['role_id'])
            if role:
                description += f"**ID: {item['item_id']}** | **{role.name}** - `{item['price']}` {currency_name}\n"

        embed.description = description
        await ctx.send(embed=embed)

    @commands.command(name='buy')
    async def buy(self, ctx, item_id: int):
        """Buys an item (role) from the shop."""
        item = database.get_shop_item(item_id)
        if not item or item['guild_id'] != ctx.guild.id:
            await ctx.send("❌ That item ID is not valid.")
            return

        role = ctx.guild.get_role(item['role_id'])
        if not role:
            await ctx.send("❌ The role for this item no longer exists. An admin needs to remove this item.")
            return

        balance = database.get_wallet_balance(ctx.guild.id, ctx.author.id)
        if balance < item['price']:
            await ctx.send(f"❌ You don't have enough currency to buy this. You need `{item['price']}`.")
            return

        if role in ctx.author.roles:
            await ctx.send("⚠️ You already have this role!")
            return

        try:
            database.update_wallet_balance(ctx.guild.id, ctx.author.id, -item['price'])
            await ctx.author.add_roles(role, reason="Purchased from shop")
            await ctx.send(f"✅ You have successfully purchased the **{role.name}** role!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have the necessary permissions to assign roles. Please check my role hierarchy.")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {e}")
            # Refund the user if something went wrong
            database.update_wallet_balance(ctx.guild.id, ctx.author.id, item['price'])

    @commands.command(name='bet')
    async def bet(self, ctx, amount: int):
        """Bets a certain amount of your currency."""
        if amount <= 0:
            await ctx.send("❌ You must bet a positive amount.")
            return

        balance = database.get_wallet_balance(ctx.guild.id, ctx.author.id)
        if amount > balance:
            await ctx.send("❌ You cannot bet more than you have.")
            return

        settings = database.get_economy_settings(ctx.guild.id)
        win_chance = settings['bet_win_chance']

        import random
        if random.randint(1, 100) <= win_chance:
            # Win
            new_balance = database.update_wallet_balance(ctx.guild.id, ctx.author.id, amount)
            await ctx.send(f"🎉 **You won!** You doubled your bet and received **{amount}**. Your new balance is **{new_balance}**.")
        else:
            # Lose
            new_balance = database.update_wallet_balance(ctx.guild.id, ctx.author.id, -amount)
            await ctx.send(f"😢 **You lost!** You lost **{amount}**. Your new balance is **{new_balance}**.")

    # --- Administrator Commands ---
    @commands.group(name='shopadmin', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def shopadmin(self, ctx):
        """Manages the role shop. Use `$shopadmin add` or `$shopadmin remove`."""
        await ctx.send("Invalid subcommand. Use `$shopadmin add` or `$shopadmin remove`.")

    @shopadmin.command(name='add')
    @commands.has_permissions(administrator=True)
    async def shop_add(self, ctx, role: discord.Role, price: int):
        """Adds a role to the shop."""
        if price < 0:
            await ctx.send("❌ Price cannot be negative.")
            return

        if database.add_shop_item(ctx.guild.id, role.id, price):
            await ctx.send(f"✅ Added the **{role.name}** role to the shop for `{price}` currency.")
        else:
            await ctx.send("⚠️ That role is already in the shop.")

    @shopadmin.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def shop_remove(self, ctx, item_id: int):
        """Removes an item from the shop by its ID."""
        if database.remove_shop_item(item_id):
            await ctx.send(f"✅ Item ID `{item_id}` removed from the shop.")
        else:
            await ctx.send(f"❌ Could not find an item with ID `{item_id}`.")

    @commands.command(name='give')
    @commands.has_permissions(administrator=True)
    async def give(self, ctx, member: discord.Member, amount: int):
        """Gives a specified amount of currency to a user."""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.")
            return
        database.update_wallet_balance(ctx.guild.id, member.id, amount)
        await ctx.send(f"✅ Gave **{amount}** currency to **{member.display_name}**.")

    @commands.command(name='take')
    @commands.has_permissions(administrator=True)
    async def take(self, ctx, member: discord.Member, amount: int):
        """Takes a specified amount of currency from a user."""
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.")
            return
        database.update_wallet_balance(ctx.guild.id, member.id, -amount)
        await ctx.send(f"✅ Took **{amount}** currency from **{member.display_name}**.")

    @commands.group(name='betconfig', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def betconfig(self, ctx):
        """Configures the betting game."""
        await ctx.send("Invalid subcommand. Use `$betconfig chance`.")

    @betconfig.command(name='chance')
    @commands.has_permissions(administrator=True)
    async def betconfig_chance(self, ctx, percentage: int):
        """Sets the win chance for the betting game (1-99)."""
        if not 1 <= percentage <= 99:
            await ctx.send("❌ Win chance must be between 1 and 99.")
            return
        database.set_bet_win_chance(ctx.guild.id, percentage)
        await ctx.send(f"✅ Betting win chance set to **{percentage}%**.")


async def setup(bot):
    await bot.add_cog(Economy(bot))