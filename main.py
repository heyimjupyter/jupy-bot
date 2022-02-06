import os
import time

from keep_alive import keep_alive
from mix_request import get_mix_name, format_mix_request, format_6s_mix_team, format_hl_mix_team, check_valid_class, get_format
# from utils import get_role
import discord
from discord.ext import commands
from discord.utils import get
import firebase_admin
from firebase_admin import db

fb_cred = firebase_admin.credentials.Certificate('firebase_key.json')
default_app = firebase_admin.initialize_app(fb_cred, {
	'databaseURL': 'https://jupy-bot-default-rtdb.asia-southeast1.firebasedatabase.app/'
	})

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'Bot has logged in as {bot.user}')


# -------------------- SETUP COMMANDS --------------------

@bot.command(name='set-up-mix-bot')
async def set_up_mix_bot(ctx):
  guild_id = str(ctx.message.guild.id)
  ref = db.reference("/")
  firebase = ref.get()

  if guild_id in firebase:
    await ctx.send('jupy-bot has already been set up in this server.')
    return 

  jupyter = await bot.fetch_user(371646606413398017)
  await ctx.send(f'welcome to jupy-bot! you will be asked a series of questions to help set the bot up. for any assistance, contact {jupyter.mention}')
  
  # get guild info and store in firebase
  guild_info = {}

  def check(m):
    return (m.channel == ctx.message.channel) and (m.author != bot.user)
  
  def format_check(m):
    return (m.content.lower() in ['6s', 'hl', 'all']) and (m.channel == ctx.message.channel) and (m.author != bot.user)

  await ctx.send('what is the name of the **mix host role**?')
  time.sleep(0.5)
  try:
    mix_host = await bot.wait_for("message", timeout=300.0, check=check)
    try:
      guild_info['mix_host_role'] = get(ctx.guild.roles, name=mix_host.content).id
    except:
      await ctx.send('there is no such role! please create the relevant roles before starting the mix bot. try again by restarting the command `!set-up-mix-bot`.')
      return 
  except:
    await ctx.send('the request has timed out since there was 5 minutes of inactivity. please try again later.')
    return

  await ctx.send('would you like to set up mix channels for only `6s`, `hl` or `all`?')
  time.sleep(0.5)
  try:
    allowed_format = await bot.wait_for("message", timeout=300.0, check=format_check)
    if 'all' == allowed_format.content.strip():
      guild_info['allowed_format'] = '6s, hl'
      guild_info['active_mixes'] = {'6s': 'None', 'hl': 'None'}
    elif '6s' == allowed_format.content.strip():
      guild_info['allowed_format'] = '6s'
      guild_info['active_mixes'] = {'6s': 'None'}
    elif 'hl' == allowed_format.content.strip():
      guild_info['allowed_format'] = 'hl'
      guild_info['active_mixes'] = {'hl': 'None'}
  except:
    await ctx.send('the request has timed out since there was 5 minutes of inactivity. please try again later.')
    return

  if '6s' in guild_info['allowed_format']:
    await ctx.send('what is the name of **6s mix role**? this is the name of the role you would like to notify to sign up for 6s mixes.')
    time.sleep(0.5)
    try:
      sixes_mix = await bot.wait_for("message", timeout=300.0, check=check)
      try:
        guild_info['6s_mix_role'] = get(ctx.guild.roles, name=sixes_mix.content).id
      except:
        await ctx.send('there is no such role! please create the relevant roles before starting the mix bot. try again by restarting the command `!set-up-mix-bot`')
        return 
    except:
      await ctx.send('the request has timed out since there was 5 minutes of inactivity. please try again later.')
      return
  if 'hl' in guild_info['allowed_format']:
    await ctx.send('what is the name of **highlander mix role**? this is the name of the role you would like to notify to sign up for highlander mixes.')
    time.sleep(0.5)
    try:
      hl_mix = await bot.wait_for("message", timeout=300.0, check=check)
      try:
        guild_info['hl_mix_role'] = get(ctx.guild.roles, name=hl_mix.content).id
      except:
        await ctx.send('there is no such role! please create the relevant roles before starting the mix bot. try again by restarting the command `!set-up-mix-bot`')
        return 
    except:
      await ctx.send('the request has timed out since there was 5 minutes of inactivity. please try again later.')
      return

  firebase[guild_id] = guild_info

  # create category, mix-request and mix-sign-ups channels
  if '6s_mix_role' in guild_info.keys():
    mix_category = await ctx.guild.create_category('6s-mixes')

    req_channel = await ctx.guild.create_text_channel('mix-request', category=mix_category)
    await req_channel.edit(slowmode_delay=15.0)
    req_msg = await req_channel.send('to start a mix request, use `!mix-request`')
    await req_msg.pin()
    signups_channel = await ctx.guild.create_text_channel('mix-signups', category=mix_category)
    await signups_channel.edit(slowmode_delay=15.0)
    signups_msg = await signups_channel.send('to sign up for a mix, use the format `!sign-up <mix name> <class name>`, e.g. `!sign-up mix-1 pscout`. to view the list of accepted class names, use `!list-classes`')
    await signups_msg.pin()
  
  if 'hl_mix_role' in guild_info.keys():
    mix_category = await ctx.guild.create_category('hl-mixes')

    req_channel = await ctx.guild.create_text_channel('mix request', category=mix_category)
    await req_channel.edit(slowmode_delay=15.0)
    req_msg = await req_channel.send('to start a mix request, use `!mix-request`')
    await req_msg.pin()
    signups_channel = await ctx.guild.create_text_channel('mix-signups', category=mix_category)
    await signups_channel.edit(slowmode_delay=15.0)
    signups_msg = await signups_channel.send('to sign up for a mix, use the format `!sign-up <mix name> <class name>`, e.g. `!sign-up mix-1 scout`. to view the list of accepted class names, use `!list-classes`')
    await signups_msg.pin()

  ref.set(firebase)
  await ctx.send('jupy-bot for mixes has been successfully set up!')

  return

# -------------------- UN-SETUP COMMANDS --------------------
@bot.command(name='remove-mix-bot')
async def remove_mix_bot(ctx):
  guild_id = str(ctx.message.guild.id)
  ref = db.reference(f"/")
  firebase = ref.get()

  if guild_id not in firebase:
    await ctx.send('jupy-bot has not been set up in this server.')
    return 
  
  del firebase[guild_id]
  
  ref = db.reference(f"/{guild_id}/")
  guild_details = ref.get()
  
  # finding categories and channels we created and deleting them all
  deleted = False
  if '6s' in guild_details['allowed_format']:
    category = get(ctx.guild.categories, name='6s-mixes')
    for channel in category.text_channels:
      await channel.delete()
    await category.delete()
    deleted = True
    await ctx.send(f"6s mixes category and channels have been deleted.")
  
  if 'hl' in guild_details['allowed_format']:
    category = get(ctx.guild.categories, name='hl-mixes')
    for channel in category.text_channels:
      await channel.delete()
    await category.delete()
    deleted = True
    await ctx.send(f"highlander mixes category and channels have been deleted.")

  ref = db.reference(f"/")
  ref.set(firebase)

  if deleted:
    jupyter = await bot.fetch_user(371646606413398017)
    await ctx.send(f"we're sorry to see you go! if you have any feedback, contact {jupyter.mention}")
    return
  else:
    await ctx.send(f"an error has occured, please contact {jupyter.mention}")


# -------------------- MIX-REQUEST COMMANDS --------------------

@bot.command(name='mix-request')
async def before_mix_req(ctx):
  if ctx.channel.name != "mix-request":
    return

  mix_name = get_mix_name(ctx)

  guild_id = str(ctx.message.guild.id)
  ref = db.reference(f'/{guild_id}/mix_host_role')
  mix_host_role = ctx.guild.get_role(ref.get())

  overwrites = {
    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False), # no one else can see
    mix_host_role: discord.PermissionOverwrite(read_messages=True), # for mix hosters to have permission, test
    ctx.guild.me: discord.PermissionOverwrite(read_messages=True), # for bot to have permission
    ctx.author: discord.PermissionOverwrite(read_messages=True), # for author mix requester to have permission, test
  }

  mix_ticket = await ctx.message.guild.create_text_channel(f'{mix_name.replace("_", "-")}-request', category=ctx.channel.category, overwrites=overwrites)
  await ctx.send(
        f'hello {ctx.message.author.mention}! jupy-bot has opened a mix-request ticket in a new channel.'
  )
  await mix_ticket.send(
        f'hello {ctx.message.author.mention}! thanks for requesting a mix with jupy-bot.\n\nbefore starting, please prepare the following information:\n   1. team name\n   2. division\n   3. time and date\n   4. maps\n   5. server\n   6. your team roster\n\n   - after starting the bot, you will be given **1 minute** per question.\n   - after completing the signup, you may update this information or delete this mix request later if needed.\n   - once you are ready, start with `!start-mix-request`\n   - to view a sample of the information you will need to provide when starting a request, use `!get-sample`\n   - if at any time you want to close the ticket, use `!close-request`'
  )
  return
 

@bot.command(name='get-sample')
async def get_sample(ctx):
  await ctx.send(
    f'**HIGHLANDER**\n\nTeam Name: Master Yoga\nFormat: hl\nDivision: Silver/Plat\nDate and Time: Tonight 9pm\nMaps: Swiftwater, Product\nServer: qix sg\n\nROSTER\nScout: birdfly\nSoldier: snoopy\nPyro: sumet123\nDemoman: heria\nHeavy: lickass\nEngineer: jupyter\nMedic: kpopbobo\nSniper: shizzy\nSpy: zippy'
    )
  await ctx.send(
    f'**6S**\n\nTeam Name: Team Panda\nFormat: 6s\nDivision: div 1\nDate and Time: Tonight 9pm\nMaps: Process, Product\nServer: qix sg\n\nROSTER\nPocket Scout: kai1\nFlank Scout: kai2\nPocket Soldier: jia1\nRoamer: jia2\nDemoman: le1\nMedic: le2'
    )
  return


@bot.command(name='list-classes')
async def get_accepted_class_names(ctx):
  if ctx.channel.name != "mix-signups":
    return

  ref = db.reference(f"/class_names")
  accepted_names = ref.get()
  formatted = '**Accepted class names:** '

  for k1, v1 in accepted_names.items():
    formatted += f'\n\n{k1}'
    for k2, v2 in v1.items():
      formatted += f'\n{v2["full_name"]}: `{v2["accepted_names"]}`'

  await ctx.send(formatted)
  
  return


async def get_6s_roster(ctx):
  def check(m):
    return (m.channel == ctx.message.channel) and (m.author != bot.user)

  timeout_msg = '**you have exceeded the 1 minute and the bot has timed out. please try again after getting all the information necessary.**'
  
  await ctx.send('6a. who is your pocket scout?')
  time.sleep(0.5)
    
  try:
      pscout = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6b. who is your flank scout?')
  time.sleep(0.5)
    
  try:
      fscout = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6c. who is your pocket soldier?')
  time.sleep(0.5)
    
  try:
      psolly = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6d. who is your roamer?')
  time.sleep(0.5)
    
  try:
      roamer = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6e. who is your demoman?')
  time.sleep(0.5)
    
  try:
      demo = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6f. who is your medic?')
  time.sleep(0.5)
    
  try:
      medic = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  return f'Pocket Scout: {pscout.content}\nFlank Scout: {fscout.content}\nPocket Soldier: {psolly.content}\nRoamer: {roamer.content}\nDemoman: {demo.content}\nMedic: {medic.content}'


async def get_hl_roster(ctx):
  def check(m):
    return (m.channel == ctx.message.channel) and (m.author != bot.user)

  timeout_msg = '**you have exceeded the 1 minute and the bot has timed out. please try again after getting all the information necessary.**'
  
  await ctx.send('6a. who is your scout?')
  time.sleep(0.5)
    
  try:
      scout = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6b. who is your soldier?')
  time.sleep(0.5)
    
  try:
      solly = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6c. who is your pyro?')
  time.sleep(0.5)
    
  try:
      pyro = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6d. who is your demoman?')
  time.sleep(0.5)
    
  try:
      demo = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6e. who is your heavy?')
  time.sleep(0.5)
    
  try:
      heavy = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6f. who is your engineer?')
  time.sleep(0.5)
    
  try:
      engie = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6g. who is your medic?')
  time.sleep(0.5)
    
  try:
      medic = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'
  
  await ctx.send('6h. who is your sniper?')
  time.sleep(0.5)
    
  try:
      sniper = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'

  await ctx.send('6i. who is your spy?')
  time.sleep(0.5)
    
  try:
      spy = await bot.wait_for("message", timeout=60.0, check=check)
  except:
      await ctx.send(timeout_msg)
      return 'None'
  
  return f'Scout: {scout.content}\nSoldier: {solly.content}\nPyro: {pyro.content}\nDemoman: {demo.content}\nHeavy: {heavy.content}\nEngineer: {engie.content}\nMedic: {medic.content}\nSniper: {sniper.content}\nSpy: {spy.content}'


@bot.command(name='start-mix-request')
async def start_mix_req(ctx):
    mix_dict = {}

    def check(m):
        return (m.channel == ctx.message.channel) and (m.author != bot.user)

    def format_check(m):
        return (m.content.lower() in ['6s', 'hl']) and (m.channel == ctx.message.channel) and (m.author != bot.user)

    timeout_msg = '**you have exceeded the 1 minute and the bot has timed out. please try again after getting all the information necessary.**'

    mix_dict["requester"] = ctx.author.id
    mix_dict["accepted_players"] = 'None'
    mix_dict["on_hold_players"] = 'None'

    await ctx.send(
        'the mix request has started. you are given **1 minute** for each question.'
    )
    await ctx.send('1. what is your team name?')
    time.sleep(0.5)
    try:
        team_name = await bot.wait_for("message", timeout=60.0, check=check)
        mix_dict["team_name"] = team_name.content
    except:
        await ctx.send(timeout_msg)
        mix_dict = 'None'
        return

    await ctx.send("2. what is the team's division? i.e. div 1-4 in 6s, steel/silver/plat in highlander, etc.")
    time.sleep(0.5)
    try:
        division = await bot.wait_for("message", timeout=60.0, check=check)
        mix_dict['division'] = division.content
    except:
        await ctx.send(timeout_msg)
        mix_dict = 'None'
        return

    await ctx.send("3. what is date and time? e.g. `tonight 9pm` or `2nd Jan 9pm`")
    time.sleep(0.5)
    try:
        time_date = await bot.wait_for("message", timeout=60.0, check=check)
        mix_dict['time_date'] = time_date.content
    except:
        await ctx.send(timeout_msg)
        mix_dict = 'None'
        return

    await ctx.send("4. which maps are to be played?")
    time.sleep(0.5)
    try:
        maps = await bot.wait_for("message", timeout=60.0, check=check)
        mix_dict['maps'] = maps.content
    except:
        await ctx.send(timeout_msg)
        mix_dict = 'None'
        return

    await ctx.send("5. what server will be used?")
    time.sleep(0.5)
    try:
        server = await bot.wait_for("message", timeout=60.0, check=check)
        mix_dict['server'] = server.content
    except:
        await ctx.send(timeout_msg)
        mix_dict = 'None'
        return

    game_format = get_format(ctx)
    
    if not game_format:
      await ctx.channel.send('jupy-bot was unable to detect the format from the category name. a moderator may have changed the name, please contact a server mod.')
      return

    if game_format == '6s':
      roster = await get_6s_roster(ctx)
    elif game_format == 'hl':
      roster = await get_hl_roster(ctx)

    if roster == 'None':
      return

    mix_dict['roster'] = roster

    await ctx.send(
        f"thank you {ctx.author.mention}! your submission is now pending the mods' approval. \n   - if errors were made, submit a new request with `!start-mix-request` in **this channel** to overwrite previous information. these changes have to be approved by a mod again. \n   - to close or cancel a mix request, `!close-request`"
    )
    
    mix_name = ctx.channel.name.split('-request')[0].replace('-', '_')
    guild_id = str(ctx.message.guild.id)
    
    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}")
    ref.set(mix_dict)
    formatted = format_mix_request(ctx, mix_name)

    ref = db.reference(f'/{guild_id}/mix_host_role')
    mix_host_role = ctx.guild.get_role(ref.get())

    await ctx.channel.send(
      f'hello {mix_host_role.mention}! please approve with `!accept-request`. the request is as follows:\n\n{formatted}'
    )

    return


@bot.command(name='accept-request')
async def accept_mix_req(ctx):
  guild_id = str(ctx.message.guild.id)
  ref = db.reference(f'/{guild_id}/mix_host_role')
  mix_host_role = ctx.guild.get_role(ref.get())
  game_format = get_format(ctx)

  if mix_host_role in ctx.author.roles:
    mix_name = ctx.channel.name.split('-request')[0].replace('-', '_')

    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/requester")
    requester = ref.get()
    requester_user = await bot.fetch_user(requester)

    overwrites = {
      ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False), # no one else can type
      mix_host_role: discord.PermissionOverwrite(send_messages=True), # for mix hosters to have permission, test
      ctx.guild.me: discord.PermissionOverwrite(send_messages=True), # for bot to have permission
  }

    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}")
    mix_details = ref.get()

    if game_format == '6s':
      formatted_mix_team = format_6s_mix_team(ctx, mix_name.replace('_', '-'))
      ref = db.reference(f"/{guild_id}/6s_mix_role/")
      mix_role = ctx.guild.get_role(ref.get())
      eg_command = '`!sign-up mix-1 pscout`. Note that class names must be **ONE WORD** e.g. `pocketscout` instead of `pocket scout`.'
    elif game_format == 'hl':
      formatted_mix_team = format_hl_mix_team(ctx, mix_name.replace('_', '-'))
      ref = db.reference(f"/{guild_id}/hl_mix_role/")
      mix_role = ctx.guild.get_role(ref.get())
      eg_command = '`!sign-up mix-1 scout`.'

    mix_channel = await ctx.message.guild.create_text_channel(f'{mix_name.replace("_", "-")}', category=ctx.channel.category, overwrites=overwrites)
    sent_message = await mix_channel.send(f'{format_mix_request(ctx, mix_name)}\n\n{formatted_mix_team}\n\nplayers are accepted at the discretion of {requester_user.mention}')
    
    mix_details['sent_message_id'] = sent_message.id
    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}")
    ref.set(mix_details)

    mix_signup_channel_name = 'mix-signups'
    await mix_channel.send(f'{mix_role.mention} sign up at {get(ctx.channel.category.channels, name=mix_signup_channel_name).mention} in the format: `!sign-up <mix name> <class name>`, e.g. {eg_command}')

    await ctx.send(
      f'hello {ctx.author.mention} and {requester_user.mention}! the mix request has been accepted and a new channel has opened for sign ups. \n   - you will be notified of signups in this private channel where you will then be given a chance to accept/deny here as well. \n   - please do not deny players unless absolutely you are sure, **this cannot be undone**.\n   - to send accepted players the string before the mix begins, you can use `!ping-string <connect string here>`.'
    )
  
  else:
    await ctx.send(
      f'sorry {ctx.author.mention}, you do not have permission to accept this mix request.'
    )

  return


@bot.command(name='onhold')
async def get_players_on_hold(ctx):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{ctx.channel.name.split('-request')[0].replace('-', '_')}/on_hold_players")
  on_hold_dict = ref.get()


  if on_hold_dict == 'None':
    await ctx.send(
      f'There are currently no players on hold and pending replies.'
    )
  else:
    await ctx.send(
      'Players on hold: \n' + '\n'.join([f'<@{value}>: {key}' for key, value in on_hold_dict.items()])
    )
  
  return


@bot.command(name='sign-up')
async def mix_req_sign_up(ctx, mix_name, class_name):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)

  if ctx.channel.name != "mix-signups":
    return
  
  mix_name = mix_name.lower()
  class_name = class_name.lower()

  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/requester")
  requester = ref.get()

  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/accepted_players")
  accepted_dict = ref.get()

  if (requester is None) or (accepted_dict is None):
    await ctx.send(f'hi {ctx.author.mention}, this mix does not exist.')
    return 

  if accepted_dict == 'None':
    in_accepted = False
    accepted_classes = ''
  else:
    in_accepted = str(ctx.author.id) in accepted_dict.values()
    accepted_classes = accepted_dict.keys()

  if not in_accepted:
    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/on_hold_players")
    on_hold_dict = ref.get()

    if on_hold_dict == 'None':
      in_hold = False
    else:
      in_hold = str(ctx.author.id) in on_hold_dict.keys()

    if not in_hold:
      class_name_code, class_name_full = check_valid_class(ctx, mix_name, class_name)

      if class_name_code:

        if class_name_code not in accepted_classes:

          if on_hold_dict == 'None':
            ref.set({ctx.author.id: class_name_code})
            
          else:
            on_hold_dict[ctx.author.id] = class_name_code
            ref.set(on_hold_dict)

          await get(ctx.channel.category.channels, name=f"{mix_name.replace('_', '-')}-request").send(f"hi <@{requester}>! {ctx.author.mention} has signed up to play {class_name_full}. \n   - to accept, use the command `!accept-player <tag discord user>` e.g. `!accept-player @jupyter`. you may also accept multiple players at a time, `!accept-player @jupyter @bong`\n   - to deny, `!deny-player <tag discord user>`, this action **cannot be undone**.")
          await ctx.send(f'hi {ctx.author.mention}, your sign-up request has been sent. you will be notified if you have been accepted/denied.')
        
        else:
          await ctx.send(f'hi {ctx.author.mention}, another player has already been accepted for the class {class_name_full}')

      else:
        await ctx.send(f'hi {ctx.author.mention}, this class name is not accepted for this mix. to view the list of accepted class names, use `!list-classes`')

    else:
      await ctx.send(f'hi {ctx.author.mention}, you have already signed up for this mix. if you wish to sign up as a different class, please sign out and sign back in.')
  
  else:
    await ctx.send(f'hi {ctx.author.mention}, you have already been accepted in this mix and cannot sign up again.')

  return
  

@bot.command(name='sign-out')
async def mix_req_sign_out(ctx, mix_name):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  if ctx.channel.name != "mix-signups":
    return

  mix_name = mix_name.lower()

  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/on_hold_players")
  on_hold_dict = ref.get()

  try:
    for key, value in on_hold_dict.items():
      if key == str(ctx.author.id):
        del on_hold_dict[key]
        await ctx.send(f'{ctx.author.mention} you have signed out successfully.')
        break

  except:
    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/accepted_players")
    accepted_dict = ref.get()

    found = False
 
    for key, value in accepted_dict.items():
      if value == str(ctx.author.id):
        del accepted_dict[key]
        found = True
        if accepted_dict == {}:
          accepted_dict = 'None'
        ref.set(accepted_dict)
        break
    
    if found:
      ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/")
      mix_details = ref.get()
      mod_role_name = 'mix-host'

      game_format = get_format(ctx)

      if game_format == '6s':
        formatted_mix_team = format_6s_mix_team(ctx, mix_name)
      elif game_format == 'hl':
        formatted_mix_team = format_hl_mix_team(ctx, mix_name)

      sent_message = await get(ctx.channel.category.channels, name=mix_name).fetch_message(mix_details['sent_message_id'])
      await sent_message.edit(content=f'{format_mix_request(ctx, mix_name)}\n\n{formatted_mix_team}\n\nplayers are accepted at the discretion of <@{mix_details["requester"]}>')
      await get(ctx.channel.category.channels, name=f"{mix_name.replace('_', '-')}-request").send(f"hello <@{mix_details['requester']}> and {get(ctx.guild.roles, name=mod_role_name).mention}! an accepted player {ctx.author.mention} has signed out.")
      await ctx.send(f'{ctx.author.mention} you have signed out successfully. note that signing out less than 1 hour before the mix begins without a sub may incur a ban as stated in the mix rules.')

    else:
      await ctx.send(f'{ctx.author.mention} you cannot sign out as you did not sign up.')

  if on_hold_dict == {}:
    on_hold_dict = 'None'
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/on_hold_players")
  ref.set(on_hold_dict)
  
  return


@bot.command(name='accept-player')
async def mix_req_accept_player(ctx):
  guild_id = str(ctx.message.guild.id)
  mix_name = ctx.channel.name.split('-request')[0].replace('-', '_')
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/on_hold_players")
  on_hold_dict = ref.get()

  for player_user in ctx.message.mentions:
    player = str(player_user.id)

    if player in on_hold_dict:
      class_name = on_hold_dict[player]

      ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/accepted_players")
      accepted_dict = ref.get()
      if accepted_dict == 'None':
        accepted_dict = {}

      if class_name in accepted_dict.keys():
        await ctx.send(f'{ctx.author.mention} the slot for {class_name} has already been taken.')
      
      else:
        del on_hold_dict[player]
        if on_hold_dict == {}:
          on_hold_dict = 'None'
        ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/on_hold_players")
        ref.set(on_hold_dict)

        ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/accepted_players")

        if accepted_dict == 'None':
          ref.set({class_name: player})
        else:
          accepted_dict[class_name] = player
          ref.set(accepted_dict)
        
        mix_signup_channel_name = 'mix-signups'
        await get(ctx.channel.category.channels, name=f"{mix_signup_channel_name}").send(f"hi {player_user.mention}! you have been accepted for {mix_name.replace('_', '-')} as {class_name}.")
        await ctx.send(f'{ctx.author.mention} player {player_user.mention} has been successfully accepted as {class_name}.')

        ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}")
        mix_details = ref.get() 
        requester = mix_details['requester']
        requester_user = await bot.fetch_user(requester)

        game_format = get_format(ctx)

        if game_format == '6s':
          formatted_mix_team = format_6s_mix_team(ctx, mix_name.replace('_', '-'))
        elif game_format == 'hl':
          formatted_mix_team = format_hl_mix_team(ctx, mix_name.replace('_', '-'))

        sent_message = await get(ctx.channel.category.channels, name=mix_name.replace('_', '-')).fetch_message(mix_details['sent_message_id'])
        await sent_message.edit(content=f'{format_mix_request(ctx, mix_name)}\n\n{formatted_mix_team}\n\nplayers are accepted at the discretion of {requester_user.mention}')
  
    else:
      await ctx.send(f'{player_user.mention} did not sign up for the mix and cannot be accepted.')

  return


@bot.command(name='deny-player')
async def mix_req_deny_player(ctx):
  guild_id = str(ctx.message.guild.id)
  mix_name = ctx.channel.name.split('-request')[0].replace('-', '_')
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/on_hold_players")
  on_hold_dict = ref.get()

  player = str(ctx.message.mentions[0].id)
  player_user = ctx.message.mentions[0]

  if player in on_hold_dict:
    class_name_code = on_hold_dict[player]

    ref = db.reference(f"/class_names/{game_format}/{class_name_code}/full_name")
    class_name_full = ref.get()

    del on_hold_dict[player]
    if on_hold_dict == {}:
      on_hold_dict = 'None'
    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/on_hold_players")
    ref.set(on_hold_dict)

    mix_signup_channel_name = 'mix-signups'
    await get(ctx.channel.category.channels, name=f"{mix_signup_channel_name}").send(f"sorry {player_user.mention}! you have been denied for {mix_name.replace('_', '-')} as {class_name_full}.")
    await ctx.send(f'{ctx.author.mention} player {player_user.mention} has been successfully denied as {class_name_full}.')
  
  else:
    await ctx.send(f'this user did not sign up for the mix and cannot be denied.')

  return


@bot.command(name='ping-string')
async def ping_string(ctx, *, arg):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  if 'connect' in arg and 'password' in arg:
    mix_name = ctx.channel.name.split('-request')[0]
    ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/accepted_players")
    accepted_dict = ref.get()
    if accepted_dict != 'None': 
      await get(ctx.channel.category.channels, name=f"{mix_name}").send(f"{' '.join([f'<@{value}>' for key, value in accepted_dict.items()])} connect string: {arg}")
      await ctx.send(f'ping is successful.')
    else:
      await ctx.send(f'there are no accepted players to ping.')
  else:
    await ctx.send('hmm... this does not look like a connect string. please try again!')

  
  return


@bot.command(name='close-request')
async def close_mix_req(ctx):
  guild_id = str(ctx.message.guild.id)
  await ctx.send(
    f'thanks for creating a mix request with jupy-bot. this channel will close soon.'
    )
  time.sleep(5)
  mix_name = ctx.channel.name.split('-request')[0].replace('-', '_')
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/")
  active_mix_dict = ref.get()

  try:
    del active_mix_dict[mix_name]
  except:
    pass

  if active_mix_dict == {}:
    active_mix_dict = 'None'

  ref.set(active_mix_dict)
  await ctx.channel.delete()
  try:
    await get(ctx.channel.category.channels, name=mix_name.replace('_', '-')).delete()
  except:
    pass
  
  return


@bot.command(name='remove-player')
async def remove_player(ctx):
  guild_id = str(ctx.message.guild.id)
  ref = db.reference(f'/{guild_id}/mix_host_role')
  mix_host_role = ctx.guild.get_role(ref.get())

  if mix_host_role not in ctx.author.roles:
    await ctx.send(f'sorry {ctx.author.mention}, you do not have permission to accept this mix request.')
  
  mix_name = ctx.channel.name.split('-request')[0].replace('-', '_')

  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}/accepted_players")
  accepted_dict = ref.get()
  
  if accepted_dict == 'None':
    await ctx.send('no players have been accepted, and so no one can be removed.')
    return
  
  for player_user in ctx.message.mentions:
    player = str(player_user.id)

    if player in accepted_dict.values():
      accepted_dict = {key:val for key, val in accepted_dict.items() if val != player}
      if accepted_dict == {}:
        accepted_dict = 'None'

      ref.set(accepted_dict)
      await ctx.send(f'{player_user.mention} has been removed.')

      # alerting person who signed up that they are now removed
      mix_signup_channel_name = 'mix-signups'
      await get(ctx.channel.category.channels, name=f"{mix_signup_channel_name}").send(f"hi {player_user.mention}, you have been removed from {mix_name.replace('_', '-')}. if you are unclear why, please contact a mix host.")

      # updating message in mix channel to remove the player
      game_format = get_format(ctx)
      ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name}")
      mix_details = ref.get() 
      requester = mix_details['requester']
      requester_user = await bot.fetch_user(requester)

      game_format = get_format(ctx)

      if game_format == '6s':
        formatted_mix_team = format_6s_mix_team(ctx, mix_name.replace('_', '-'))
      elif game_format == 'hl':
        formatted_mix_team = format_hl_mix_team(ctx, mix_name.replace('_', '-'))

      sent_message = await get(ctx.channel.category.channels, name=mix_name.replace('_', '-')).fetch_message(mix_details['sent_message_id'])
      await sent_message.edit(content=f'{format_mix_request(ctx, mix_name)}\n\n{formatted_mix_team}\n\nplayers are accepted at the discretion of {requester_user.mention}')
    else:
      await ctx.send(f'{player_user.mention} has not been accepted, and so cannot be removed.')

  return


# -------------------- EASTER EGG COMMANDS --------------------
# https://www.youtube.com/watch?v=-1OU4tkFJns
# !blackbean


keep_alive()
bot.run(os.environ['token'])
