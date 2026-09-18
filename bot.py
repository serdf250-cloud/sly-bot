import os
import discord
from discord import app_commands
from discord.ext import commands

# ============ НАСТРОЙКИ ============
# Токен берётся из переменных окружения Wispbyte (там настроишь DISCORD_TOKEN)
TOKEN = os.getenv("DISCORD_TOKEN")

# ЗАМЕНИ на свои ID (без кавычек)
GUILD_ID = 1550148492910010381                  # ID сервера SLY
APPLY_CHANNEL_ID = 1550173159158841385          # ID канала #apply
APPLICATION_CHANNEL_ID = 1550174780580298752    # ID канала #applications
ANNOUNCE_CHANNEL_ID = 1550172640860446740       # ID канала #announcements
LEADER_ID = 1438028252114583725                 # Твой Discord ID

ROLE_HATCHLING = "Hatchling"
ROLE_RECRUIT = "Recruit"

# ============ БОТ ============
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ============ ФОРМА ЗАЯВКИ ============
class ApplicationModal(discord.ui.Modal, title="Заявка в клан SLY"):
    nickname = discord.ui.TextInput(
        label="Ник",
        placeholder="Твой ник в игре",
        required=True,
        max_length=50
    )
    hours = discord.ui.TextInput(
        label="Часов в игре",
        placeholder="Например: 500",
        required=True,
        max_length=10
    )
    experience = discord.ui.TextInput(
        label="Опыт (рейды, PvP, фарм)",
        placeholder="Расскажи, что умеешь",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=300
    )
    reason = discord.ui.TextInput(
        label="Почему именно SLY?",
        placeholder="Чем мы тебе интересены",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=300
    )
    online = discord.ui.TextInput(
        label="Онлайн (часов в день)",
        placeholder="Например: 3-4 часа",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🐍 Новая заявка в SLY",
            color=0x6A0DAD
        )
        embed.add_field(name="Ник", value=self.nickname.value, inline=False)
        embed.add_field(name="Часы", value=self.hours.value, inline=True)
        embed.add_field(name="Онлайн", value=self.online.value, inline=True)
        embed.add_field(name="Опыт", value=self.experience.value, inline=False)
        embed.add_field(name="Почему SLY", value=self.reason.value, inline=False)
        embed.add_field(
            name="Кандидат",
            value=f"{interaction.user.mention} (`{interaction.user.id}`)",
            inline=False
        )
        embed.set_footer(text="In tenebris. Vos non vidistis.")

        view = ApplicationReviewView(interaction.user.id, self.nickname.value)

        channel = bot.get_channel(APPLICATION_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed, view=view)

        try:
            leader = await bot.fetch_user(LEADER_ID)
            await leader.send(embed=embed, view=view)
        except Exception:
            pass

        await interaction.response.send_message(
            "🐍 In tenebris. Твоя заявка отправлена. Жди ответа.",
            ephemeral=True
        )


# ============ КНОПКИ ОДОБРЕНИЯ/ОТКЛОНЕНИЯ ============
class ApplicationReviewView(discord.ui.View):
    def __init__(self, user_id: int, nickname: str):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.nickname = nickname

    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)

        if not member:
            await interaction.response.send_message("❌ Участник не найден.", ephemeral=True)
            return

        role = discord.utils.get(guild.roles, name=ROLE_HATCHLING)
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                await interaction.response.send_message(f"❌ Не смог выдать роль: {e}", ephemeral=True)
                return

        recruit = discord.utils.get(guild.roles, name=ROLE_RECRUIT)
        if recruit and recruit in member.roles:
            try:
                await member.remove_roles(recruit)
            except Exception:
                pass

        announce = bot.get_channel(ANNOUNCE_CHANNEL_ID)
        if announce:
            await announce.send(
                f"🐍 **In tenebris.** Новый Hatchling: {member.mention}\n"
                f"Испытательный срок — 3-7 дней."
            )

        try:
            await member.send(
                "🐍 **In tenebris. Ты принят.**\n\n"
                "Добро пожаловать в SLY. Испытательный срок — 3-7 дней.\n"
                "Дальше — либо Fang, либо кик. Покажи себя."
            )
        except Exception:
            pass

        embed = interaction.message.embeds[0]
        embed.color = 0x1B4D2E
        embed.set_footer(text=f"✅ Принят ({interaction.user.name})")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.user_id)

        if member:
            try:
                await member.send(
                    "🐍 **In tenebris.**\n\n"
                    "К сожалению, ты нам не подходишь. Попробуй позже."
                )
            except Exception:
                pass

        embed = interaction.message.embeds[0]
        embed.color = 0x8B0000
        embed.set_footer(text=f"❌ Отклонён ({interaction.user.name})")
        await interaction.response.edit_message(embed=embed, view=None)


# ============ КНОПКА "ПОДАТЬ ЗАЯВКУ" ============
class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Подать заявку",
        style=discord.ButtonStyle.primary,
        emoji="🐍",
        custom_id="apply_button"
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


# ============ СОБЫТИЯ ============
@bot.event
async def on_ready():
    print(f"🐍 Бот {bot.user} онлайн.")
    print("In tenebris.")

    channel = bot.get_channel(APPLY_CHANNEL_ID)
    if channel:
        async for msg in channel.history(limit=10):
            if msg.author == bot.user and msg.components:
                return

        embed = discord.Embed(
            title="🐍 Хочешь вступить в SLY?",
            description=(
                "**In tenebris.** — «Во тьме.»\n\n"
                "Мы не берём всех. Только тех, кто понимает:\n"
                "Мы не оставляем следов.\n"
                "вы не видели нас.\n\n"
                "**Нажми кнопку ниже**, чтобы подать заявку."
            ),
            color=0x6A0DAD
        )
        embed.set_footer(text="Не спамь. Только серьёзные.")
        await channel.send(embed=embed, view=ApplyView())


@bot.event
async def on_member_join(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name=ROLE_RECRUIT)
    if role:
        try:
            await member.add_roles(role)
        except Exception as e:
            print(f"Не смог выдать Recruit: {e}")


# ============ ЗАПУСК ============
bot.run(TOKEN)
