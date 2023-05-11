import sys
import pandas as pd
import logging
import colorlog
from deep_translator import GoogleTranslator

# ultls
import os
import random
import sys
import logging
from hurry.filesize import size, si
from services.data import *

#discord imports
import discord
from discord.colour import Color
from dotenv import load_dotenv
from discord.ext import tasks, commands
from services.Albionapi import *
#requests imports
import requests
import pandas as pd
import asyncio
# data ultls
intents = discord.Intents.all()
#role_file = cfg["role_file"] #[path] cargos de cada discord registrados
#guilds = cfg["data_guild"] #[path] configração de cada discord
#bldb = cfg["blacklist"] #[path] banco de blacklist por discord
#tdb = cfg["taxa_fixa"] #[path] do banco de pagamento de taxa
prefix = cfg["prefix"]  # prefixo do bot
#datag = init_json(guilds) # dados de configuração de cada discord
atividades= cfg["atividades"] #lista de atividades "customizadas"
bot = commands.Bot(command_prefix=prefix, intents=intents) #pré-inicialização com atribuição do prefixo
#ao = Ao() #objeto de requisições do servidor do albion

fot = "Bot by: [@LeandroLimaPRO#0227](https://discord.gg/qSjPnBfZW3)\n[Contribua](https://bityli.com/l4KVV) para manter o bot marocando." #footer dos embeds de cada mensagem do bot

logger = logging.getLogger('') # obtem todos os loggers ativos  -> em outros arquivos chamar logger = logging.getLogger(__name__) 
logger.setLevel(logging.INFO) #seta nivel de logger 
fh = logging.FileHandler(f"debug{random.randint(0,10000)}.log",encoding="utf-8")# Cria arquivo de logger (NOME)
sh = logging.StreamHandler(sys.stdout) # atribui cmd como ouvinte dos loggers
#configura formato de logger
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(colorlog.ColoredFormatter('%(log_color)s [%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%a, %d %b %Y %H:%M:%S'))
logger.addHandler(fh)
logger.addHandler(sh)

def date_format(date):
            data = date.split('-')
            hour = data[2].split('T')
            #print(hour)
            hour = hour[1].split(':')
            #print(hour)
            return f"{data[2][:2]}/{data[1]}/{data[0]}  {hour[0]}:{hour[1]}"
        
def mudarLingua(lang):
    tr = GoogleTranslator()
    lang = [l for l in tr.supported_languages if l == lang]
    if not lang:
        return False
    return  GoogleTranslator(source='auto', target=lang[0])

    
def is_guild_owner(ctx):
    return ctx.guild is not None and ctx.guild.owner_id == ctx.author.id


def has_roles (ctx):
    #datag = init_json(guilds)
    #rol = init_json(role_file)
    idg = ctx.guild.id
    rolesctx = ctx.author.roles
    roles = []
    for role in rolesctx:
        if role.name != "None":
            roles.append(role.name)
    if is_guild_reg(idg):
        for role in roles:
            cargo = is_cargo(idg,role)
            
        if is_guild_owner(ctx) or cargo == True:
            return True
        else:
            return False
    else:
        return False


def search_member(member, search):
    result = False
    player = member.nick
    if not bool(player):
        player = member.name
    if bool(player.count(search)):
            return member
    return result