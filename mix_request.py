from firebase_admin import db

def get_mix_name(ctx):
  category_channels = ctx.channel.category.channels
  channel_names_ls = []

  for channel in category_channels:
    channel_names_ls.append(channel.name)
  
  channel_names_ls = list(set(' '.join(channel_names_ls).replace('mix', '').replace('request', '').replace('signups', '').replace('-', '').split(' ')))
  channel_names_ls = list(filter(None, channel_names_ls))

  num_ls = list(map(int, channel_names_ls))

  if len(num_ls) == 0:
    mix_name = 'mix_1'
  else:
    for i in range(1, max(num_ls)+2):
      if i not in num_ls:
        mix_name = f'mix_{i}'
        break

  return mix_name


def format_mix_request(ctx, mix_name):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/")
  details = ref.get()

  formatted = f"""Team Name: {details["team_name"]}\nDivision: {details["division"]}\nDate and Time: {details["time_date"]}\nMaps: {details["maps"]}\nServer: {details["server"]}\n\nROSTER\n{details["roster"]}"""
  return formatted


def get_user_for_mix_msg(ctx, class_name, mix_name):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/accepted_players")
  accepted_dict = ref.get()

  user_id = accepted_dict.get(class_name, '')
  if user_id != '':
    return f'<@{user_id}>'
  else:
    return ''


def format_6s_mix_team(ctx, mix_name):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/accepted_players")
  accepted_dict = ref.get()

  if accepted_dict == 'None':
    formatted = f"MIX TEAM\nPocket Scout:\nFlank Scout:\nPocket Soldier:\nRoamer:\nDemoman:\nMedic:"

  else:
    pscout = get_user_for_mix_msg(ctx, 'pscout', mix_name)
    fscout = get_user_for_mix_msg(ctx, 'fscout', mix_name)
    psoldier = get_user_for_mix_msg(ctx, 'psoldier', mix_name)
    roamer = get_user_for_mix_msg(ctx, 'roamer', mix_name)
    demo = get_user_for_mix_msg(ctx, 'demo', mix_name)
    med = get_user_for_mix_msg(ctx, 'med', mix_name)

    formatted = f"MIX TEAM\nPocket Scout: {pscout}\nFlank Scout: {fscout}\nPocket Soldier: {psoldier}\nRoamer: {roamer}\nDemoman: {demo}\nMedic: {med}"

  return formatted


def format_hl_mix_team(ctx, mix_name):
  guild_id = str(ctx.message.guild.id)
  game_format = get_format(ctx)
  ref = db.reference(f"/{guild_id}/active_mixes/{game_format}/{mix_name.replace('-', '_')}/accepted_players")
  accepted_dict = ref.get()

  if accepted_dict == 'None':
    formatted = f"MIX TEAM\nScout:\nSoldier:\nPyro:\nDemoman:\nHeavy:\nEngineer:\nMedic:\nSniper:\nSpy:"

  else:
    scout = get_user_for_mix_msg(ctx, 'scout', mix_name)
    soldier = get_user_for_mix_msg(ctx, 'soldier', mix_name)
    pyro = get_user_for_mix_msg(ctx, 'pyro', mix_name)
    demo = get_user_for_mix_msg(ctx, 'demo', mix_name)
    heavy = get_user_for_mix_msg(ctx, 'heavy', mix_name)
    engie = get_user_for_mix_msg(ctx, 'engie', mix_name)
    med = get_user_for_mix_msg(ctx, 'med', mix_name)
    sniper = get_user_for_mix_msg(ctx, 'sniper', mix_name)
    spy = get_user_for_mix_msg(ctx, 'spy', mix_name)

    formatted = f"MIX TEAM\nScout: {scout}\nSoldier: {soldier}\nPyro: {pyro}\nDemoman: {demo}\nHeavy: {heavy}\nEngineer: {engie}\nMedic: {med}\nSniper: {sniper}\nSpy: {spy}"

  return formatted


def check_valid_class(ctx, mix_name, class_name):
  game_format = get_format(ctx)

  class_name_code = None
  class_name_full = None

  ref = db.reference(f"/class_names/{game_format}")
  accepted_names = ref.get()

  for key, value in accepted_names.items():
    accepted_names = value['accepted_names'].split(' | ')
    if class_name in accepted_names:
      class_name_code = key
      class_name_full = value['full_name']
      break

  return class_name_code, class_name_full


def get_format(ctx):
  sixes_kw = ['6s', "6's", 'sixes']
  hl_kw = ['hl', 'highlander']
  format = None

  category = ctx.channel.category.name

  for kw in sixes_kw:
    if kw in category:
      format = '6s'
      break
  
  for kw in hl_kw:
    if kw in category:
      format = 'hl'
      break

  return format