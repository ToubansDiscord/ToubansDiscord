"""
Toubans Discord version

Toubans! Discord version is licensed under MIT License.
Copyright (C) 2018 西村惟, apple502j, kenny2github
Using discord.py (rewrite), dateutil and emoji library

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import re
import math
import datetime
import calendar
import time as timetime
import locale
import json
import asyncio as ai # Below are foreign
import dateutil
from dateutil.relativedelta import relativedelta
import discord as d # Rewrite needed!
from discord.ext.commands import Bot
from discord.ext.commands import bot_has_permissions
from discord.ext.commands import has_permissions
from discord.ext import commands as c
from emoji import emojize

# Buggy, don't enable this!
#locale.setlocale(locale.LC_TIME, 'ja-JP')

TOUBANS_ADMIN = "Toubans 管理"
TOUBANS_ROLE = "Toubans 通知受け取り"

JSON = "toubans.json"

asyncio = ai # compatibility

class InfiniteLoop(RecursionError):
    def __init__(self):
        super().__init__()
        print("InfiniteLoop detected!")

bot = Bot(command_prefix="当番係、",
activity=d.Activity(type=d.ActivityType.watching, name="ヘルプ"))

split=lambda l:[l[p] for p in range(len(l))]

global infLoopCount
infLoopCount=0

def infloop():
    global infLoopCount
    infLoopCount+=1
    if infLoopCount>=200:
        raise InfiniteLoop

def _rjson():
    try:
        with open(JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _wjson(dic):
    if True: #try:
        with open(JSON, "w", encoding="utf-8") as f:
            json.dump(dic, f)
    if False: #except:
        pass

async def wait_until(tm):
    """ Wait for tm seconds. """
    while 1:
        now = timetime.time()
        remaining = tm - now
        if remaining < 86400:
            break
        await asyncio.sleep(86400) #asyncio.sleep doesn't like times more than a day
        print(remaining)
    await asyncio.sleep(remaining)

def strptime(time):
    time=time.lower().strip()
    for pattern in ("am%H:%M", "pm%H:%M", "午前%H:%M", "午後%H:%M", "%H:%M",
                    "am%H時%M分", "pm%H時%M分", "午前%H時%M分", "午後%H時%M分", "%H時%M分"):
        try:
            timeobj = datetime.datetime.strptime(time, pattern)
            hour = timeobj.hour
            minute = timeobj.minute
            if re.search("^(?:pm|午後)", pattern) and hour<12:
                hour += 12
            return hour, minute
        except:
            continue
    raise ValueError("不正な時刻です。")

def m2m(guild, mention):
    if not re.match(r"^<@\d*>$", mention):
        raise ValueError("Not a valid mention")
    uid = int(mention.replace("<@","").replace(">",""))
    return guild.get_member(uid)

def get_available_ch(guild):
    def channel_write(channel):
        if not channel:
            return False
        perm = guild.me.permissions_in(channel)
        return (
            perm.read_messages and
            perm.send_messages and
            perm.manage_messages and
            perm.embed_links and
            perm.read_message_history and
            perm.mention_everyone and
            perm.add_reactions
        )
    if channel_write(guild.get_channel(_rjson().get(str(guild.id),{"channel":0}).get("channel",0))):
        return guild.get_channel(int(_rjson()[guild.id]["channel"]))
    elif channel_write(guild.system_channel):
        return guild.system_channel
    else:
        for channel in guild.text_channels:
            if channel_write(channel):
                return channel
    return None

async def config_info(channel):
    # called by functions
    status = "設定はすべて完了しました。"
    config = _rjson().get(str(channel.guild.id),{})
    if (config=={} or config.get("toubans",{})=={}):
        status="""まず、当番メンバーを追加しましょう。「当番係、当番追加して 当番名 名前」
名前をメンションにすれば当番通知がDMで送られます。(後で実装)"""
    elif config.get("cycle", "none") == "none":
        status="""周期を「毎日1回」「毎週1回」「毎月1回」から選んで、「当番係、周期は 毎日1回」のように
設定してください。毎週1回の設定では「曜日」、毎月1回は「日」を後で設定します。"""
    elif config.get("time", "none") == "none":
        status="""通知時刻を設定します。「当番係、通知時刻は 7時15分」のように設定できます。
時刻フォーマットでは「XX:YY」または「XX時YY分」が使えます。"""
    elif (config["cycle"] in ["毎週1回"] and config.get("day","none")=="none"):
        status="""通知する曜日を「当番係、通知曜日は 月」のように設定してください。
毎月1回の通知を行いたい場合は、周期設定をやり直してください。"""
    elif (config["cycle"] == "毎月1回" and config.get("date","none")=="none"):
        status="""通知する日を「当番係、通知する日は 1日」のように設定してください。
毎週1回・毎日1回の通知を行いたいときは、周期設定をやり直してください。"""
    await channel.send(status)

def config_ended(guild):
    # called by functions
    config = _rjson().get(str(guild.id),{})
    if (config=={} or config.get("toubans",{})=={}):
        return False
    elif config.get("cycle", "none") == "none":
        return False
    elif config.get("time", "none") == "none":
        return False
    elif (config["cycle"] in ["毎週1回"] and config.get("day","none")=="none"):
        return False
    elif (config["cycle"] == "毎月1回" and config.get("date","none")=="none"):
        return False
    return True

def valid_user(guild, user):
    return d.utils.get(guild.roles, name=TOUBANS_ADMIN) in user.roles

@bot.command(name="次の設定は何")
async def next_config(ctx):
    await config_info(ctx.message.channel)

async def setup_guild(guild):
    channel = get_available_ch(guild)
    roles = []
    for role in guild.roles:
        roles.append(role.name)
    await channel.send("当番係 Version 0.01\nヘルプ: 「当番係、使い方教えて」")
    await channel.send(emojize("""Toubans! Discord version is licensed under MIT License.
Copyright :copyright: 2018 西村惟, apple502j, kenny2github
Using discord.py (rewrite), dateutil and emoji library"""))
    if TOUBANS_ROLE not in roles:
        toubanRole = await guild.create_role(
            name=TOUBANS_ROLE
        )
        await guild.owner.add_roles(toubanRole)
        await channel.send("{} 当番通知の役職を作成し、サーバー所有者に設定しました。".format(guild.owner.mention))
    if TOUBANS_ADMIN not in roles:
        toubanAdminRole = await guild.create_role(
            name=TOUBANS_ADMIN,
            color=d.Colour.green(),
            mentionable=True
        )
        await guild.owner.add_roles(toubanAdminRole)
        await channel.send("""{} 当番管理者の役職を作成し、サーバー所有者に設定しました。
なお、役職管理権限のあるユーザーが勝手に管理者になる場合があります。気を付けてください。
サーバー所有者が当番管理者にならない場合では、「先に他の人を役職管理者にしてから」自分で役職を削除してください。""".format(guild.owner.mention))
    else:
        members = guild.members
        toubanAdminRole = d.utils.get(guild.roles, name=TOUBANS_ADMIN)
        for member in members:
            if toubanAdminRole in member.roles:
                break
        else:
            # for-else means no member is admin!
            await guild.owner.add_roles(toubanAdminRole)
            await channel.send("""{} 当番管理者が一人もいないため、サーバー所有者に設定しました。
サーバー所有者が当番管理者にならない場合では、「先に他の人を役職管理者にしてから」自分で役職を削除してください。""".format(guild.owner.mention))
    # 設定Check
    config = _rjson().get(str(guild.id), {})
    if (config=={} or config.get("toubans",{})=={} or
        config.get("cycle", "none") == "none" or
        config.get("time", "none") == "none" or
        (config.get("day","none")=="none" and config.get("date",0)==0) or
        (config["cycle"] in ["毎週1回"] and config.get("day","none")=="none") or
        (config["cycle"]=="毎月1回" and config.get("date",0)==0)
        ):
        await channel.send("""{} 設定が終わっていません。以下の手順で行ってください。
""".format(toubanAdminRole.mention))
        await config_info(channel)

@bot.command(name="終了")
@c.is_owner()
async def stop(ctx):
    """ ボットを終了/再起動します。 """
    exit()

@bot.command('実行')
@c.is_owner()
async def eval_(ctx, *, arg):
	""" Pythonコードを実行します。 """
	try:
		await eval(arg, globals(), locals())
	except BaseException as e:
		await ctx.send(e)

############################################# SETTINGS PART BEGINS FROM HERE!

@bot.command(name="当番追加して")
async def add_touban(ctx, touban_type, name):
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    if not config[str(guild.id)].get("toubans", False):
        config[str(guild.id)]["toubans"]=[]
    config[str(guild.id)]["toubans"].append([touban_type, name])
    _wjson(config)
    try:
        answer = "ユーザー「{}」".format(m2m(guild, name.strip()).display_name)
    except ValueError:
        answer = name
    await ctx.send("{1}を{0}にしました。".format(touban_type, answer))

@bot.command(name="周期は")
async def set_cycle(ctx, cycle):
    valid=["毎月1回", "毎週1回", "毎日1回"]
    if cycle not in valid:
        await ctx.send("周期は{}から設定してください。".format("、".join(valid)))
        return
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    config[str(guild.id)]["cycle"]=cycle
    _wjson(config)
    await ctx.send("周期を{0}にしました。".format(cycle))

@bot.command(name="通知の始めは")
async def set_start(ctx, sentence):
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    config[str(guild.id)]["start_sentence"]=sentence
    _wjson(config)
    await ctx.send("通知の始めの文を設定しました。")

@bot.command(name="通知の終わりは")
async def set_end(ctx, sentence):
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    config[str(guild.id)]["end_sentence"]=sentence
    _wjson(config)
    await ctx.send("通知の終わりの文を設定しました。")

@bot.command(name="通知時刻は")
async def set_time(ctx, time):
    try:
        hour, minute=strptime(time)
    except ValueError:
        await ctx.send("時刻は「何時何分」と設定してください。")
        return
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    config[str(guild.id)]["time"]=[hour, minute]
    _wjson(config)
    await ctx.send("通知時刻を{0}時{1}分にしました。".format(hour, minute))

@bot.command(name="通知曜日は")
async def set_dow(ctx, dow):
    if re.match("^[^日月火水木金土]$", dow):
        await ctx.send("曜日じゃないものが混じっているようです...")
        return
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    elif config[str(guild.id)].get("cycle","none")!="毎週1回":
        await ctx.send("曜日指定で通知する場合は、周期を「毎週1回」にしてください。")
        return
    config[str(guild.id)]["day"]=split(dow)
    _wjson(config)
    await ctx.send("通知する曜日を{0}にしました。".format("、".join(dow)))

@bot.command(name="通知する日は")
async def set_date(ctx, date):
    """ 通知日を指定します。"""
    new_dates = []

    if re.match(r"^([1-9]|[12][0-9]|3[01])日?$", date):
        new_dates.append(date.replace("日",""))
    else:
        await ctx.send("日付でないものが混じっているようです。")
        return
    if any(map(lambda x:int(x)>28, new_dates)):
        await ctx.send("""注意: もしその日が存在しない月の場合は、月の最後の日として解釈されます。
たとえば、31日配信に設定した場合、4月は30日に配信されます。""")
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    elif config[str(guild.id)].get("cycle","毎月1回")!="毎月1回":
        await ctx.send("日付指定で通知する場合は、周期を「毎月1回」にしてください。")
        return
    config[str(guild.id)]["date"]=sorted(new_dates)
    _wjson(config)
    await ctx.send("通知する曜日を{0}日にしました。".format("日、".join(new_dates)))

@bot.command(name="次の送信止めて")
async def stop_send_today(ctx):
    """ 送信を止めます。 """
    guild=ctx.message.channel.guild
    if not valid_user(guild, ctx.message.author):
        await ctx.send("権限がありません。")
        return
    config=_rjson()
    if not config.get(str(guild.id), False):
        config[str(guild.id)]={}
    config[str(guild.id)]["stopnext"]=True
    _wjson(config)

########################################### NOTIFICATION PART BEGINS FROM HERE!

NOTIFICATION = emojize("""Toubans! 通知 :mega:
{start_sentence}
{notif_list}
{end_sentence}
""")

bot.remove_command('help')
@bot.command(name='使い方教えて')
async def send_help(ctx):
    """ ヘルプ """
    embed=d.Embed(title="ヘルプ", description="当番係に御用ですか?こちらを参考にしてください!", color=0x4eb6a0)
    embed.set_thumbnail(url="https://raw.githubusercontent.com/ToubansDiscord/ToubansDiscord/master/Toubans_rg.png")
    embed.add_field(name="当番係、次の設定は何", value="次になにをすればいいかわからないときはこれ!", inline=False)
    embed.add_field(name="当番係、当番追加して <当番名> <名前>", value="""当番を追加できるよ!
当番名は「掃除当番」「ボット管理当番」などなんでもOK! スペース含む場合は""おねがい。
名前は個人メンションでもOK! (通知が嫌な人にはやらないでね)""", inline=False)
    embed.add_field(name="当番係、周期は <周期>", value="""周期を設定できるよ! 周期は「毎週1回」がメジャーだけど、
毎月1回、毎日1回でもおっけー。毎週2回は無理です...""", inline=False)
    embed.add_field(name="当番係、通知の始めは <ことば>", value="通知の始めの文を設定できるよ! \"\"で囲むことを推奨するよ。", inline=False)
    embed.add_field(name="当番係、通知の終わりは <ことば>", value="通知の終わりの文を設定できるよ! \"\"で囲むことを推奨するよ。", inline=False)
    embed.add_field(name="当番係、通知時刻は <何時何分>", value=emojize("通知時刻は何時何分か、教えてね。:alarm_clock: "), inline=False)
    embed.add_field(name="当番係、通知曜日は <曜日>", value="(周期が毎週1回なら)通知曜日を「日月火水木金土」から1つ選んでね。", inline=False)
    embed.add_field(name="当番係、通知する日は <日>", value=emojize("(周期が毎月1回なら)通知するのは何日?1日-31日から1つ選んでね。:calendar_spiral: "), inline=False)
    embed.add_field(name="当番係、次の送信止めて", value=emojize("あ、今日は当番ないよ! :anger: 止めて! というときに。"), inline=False)
    embed.add_field(name="当番係、通知テストお願い", value=emojize("通知をテストします。名前設定のメンションも届くから気を付けて!:no_bell:"), inline=False)
    embed.add_field(name="当番係、使い方教えて", value=emojize("また読みたいときに使ってください。:grinning:"), inline=False)
    embed.set_footer(text="では、楽しい当番ライフを!")
    await ctx.send(embed=embed)

def turn_touban_list(guild):
    """ 当番表を回そう """
    config = _rjson()
    tlist = config[str(guild.id)]["toubans"]
    tbans = [x[0] for x in tlist]
    tpeople = [x[1] for x in tlist]
    tbans.append(tbans.pop()) # What a hacky way! But this works.
    new_tlist=[]
    for i in range(len(tlist)):
        new_tlist.append([tbans[i], tpeople[i]])
    config[str(guild.id)]["toubans"]=new_tlist
    _wjson(config)

async def notify(guild, do_turn=True):
    """ 通知文を作成、送信する """
    channel = get_available_ch(guild)
    config=_rjson()
    config = config[str(guild.id)]
    cycle=config["cycle"].replace("毎","").replace("1回","")
    start_sentence=config.get("start_sentence", f"今{cycle}の当番です。")
    end_sentence=config.get("end_sentence", "よろしくおねがいします。")
    tbans=config["toubans"]
    notif_list=[]
    for tban in tbans:
        notif_list.append(f"{tban[1]}: {tban[0]}")
    await channel.send(NOTIFICATION.format(
                                        start_sentence=start_sentence,
                                        end_sentence=end_sentence,
                                        notif_list="\n".join(notif_list)
    ))
    if do_turn:
        turn_touban_list(guild)

@bot.command(name="通知テストお願い")
async def send_example(ctx):
    """ 通知をテストします。 """
    await ctx.send("""注意:次の送信は予定通り実行されます。
------------------------------""")
    await notify(ctx.message.channel.guild, do_turn=False)


async def looper(guild, every, starting):
    """ 通知のループ """
    channel=get_available_ch(guild)

    await wait_until(starting)
    await notify(guild)
    while 1:
        await wait_until(timetime.time() + every)
        config=_rjson()
        if config[str(guild.id)].get("stopnext", False):
            config[str(guild.id)]["stopnext"]=False
            _wjson(config)
            continue
        await notify(guild)

def when_next_dow(dow, ta):
    dow_c="月火水木金土日".find(dow)
    dateobj = (datetime.datetime.now() + relativedelta(weekday=dow_c))
    dtobj = datetime.datetime(dateobj.year, dateobj.month, dateobj.day, ta[0], ta[1], 0)
    return math.ceil((dtobj-datetime.datetime.now()).total_seconds())

def when_next_day(ta):
    dateobj = (datetime.datetime.now() + datetime.timedelta(1))
    dtobj = datetime.datetime(dateobj.year, dateobj.month, dateobj.day, ta[0], ta[1], 0)
    return math.ceil((dtobj-datetime.datetime.now()).total_seconds())

def when_next_month(day, ta):
    dateobj = (datetime.datetime.now() + relativedelta(month=1))
    dtobj=None
    while not dtobj:
        infloop() # for safety
        try:
            dtobj = datetime.datetime(dateobj.year, dateobj.month, day, ta[0], ta[1], 0)
            break
        except ValueError:
            day-=1
            continue
    return math.ceil((dtobj-datetime.datetime.now()).total_seconds())

@bot.event
async def on_ready():
    for guild in bot.guilds:
        await setup_guild(guild)
        if config_ended(guild):
            config=_rjson()
            config = config[str(guild.id)]
            ta=config["time"]
            if config["cycle"]=="毎日1回":
                starting=when_next_day(ta)
                every=24*60*60
            elif config["cycle"]=="毎週1回":
                starting=when_next_dow(config["day"][0], ta)
                every=7*24*60*60
            elif config["cycle"]=="毎月1回":
                starting=when_next_month(int(config["date"][0]), ta)
                every=30.417*24*60*60 # todo: work on this!

            bot.loop.create_task(looper(guild, every, starting))

@bot.event
async def on_guild_join(guild):
    await setup_guild(guild)


if __name__=="__main__":
    with open("toubans_token.txt","r") as tokenfile:
        bot.run(tokenfile.readline().strip())

########################################### DUSTBIN CODES

# From kenny2github
"""
time_now = time.time()
time_then = time.mktime(time.strptime('2018-10-21T23:00:00Z', '%Y-%m-%dT%H:%M:%SZ'))
time_wait = time_then - time_now
time.sleep(time_wait)
"""

# Created by kenny2github
"""
timers = {}
@client.command()
async def timer(ctx, time):
    time = #do some magic to get the amount of seconds to wait from now until the time
    consttime = #do some magic to get the amount of seconds to wait between timers
    if ctx.author.id in timers:
        timers[ctx.author.id].cancel()
    async def personal_timer():
        try:
            await asyncio.sleep(timers[ctx.author.id][0])
        except asyncio.CancelledError:
            return
        try:
            timers[ctx.author.id][1].cancel()
        except asyncio.CancelledError:
            timers[ctx.author.id][0] = (consttime, asyncio.Task(personal_timer()))
    timers[ctx.author.id] = (time, asyncio.Task(personal_timer()))
"""

# Created by kenny2github
"""
import time

async def wait_until(tm):
    while 1:
        now = time.time()
        remaining = tm - now
        if remaining < 86400:
            break
        await asyncio.sleep(86400) #asyncio.sleep doesn't like times more than a day
    await asyncio.sleep(remaining)
async def _timer(user, every, starting):
    user = client.get_user(user)
    if not user.dm_channel:
        await user.create_dm()
    await wait_until(starting)
    await user.dm_channel.send('ping, timer')
    while 1:
        await wait_until(time.time() + every)
        await user.dm_channel.send('ping, timer')
@client.command()
async def timer(ctx, every: int, starting: int):
    """#every must be in seconds, starting must be in epoch time
"""
    with open('timers.txt', 'a') as f:
        f.write('{},{},{}'.format(ctx.author.id, every, starting))
    client.loop.create_task(_timer(ctx.author.id, every, starting))
@client.event
async def on_ready():
    with open('timers.txt', 'r') as f:
        for line in f:
            us, every, starting = map(int, line.strip().split(','))
            while starting < time.time():
                starting += every
            client.loop.create_task(_timer(us, every, starting))
"""
