import math
from asyncio.events import new_event_loop, set_event_loop
from datetime import time
from logging import Logger

from sqlalchemy.sql.elements import or_
from discord import embeds, player
from discord.errors import HTTPException
from .inits import *

 

class Admin(commands.Cog):
    '''
        METODOS PRIVATIVOS
    '''
    
    
    #obtem novos jogadores
    async def get_new_players_in_guild(self, guild, members = None):
        logger.info(f"OBTENÇÃO: {guild.name}")
        if guild.id_ao is not None or not "":
            if members == None:
                logger.info("Tentando obter dados novamente")
                try:
                    members = await get_guild_members(guild.id_ao)
                except aiohttp.ContentTypeError as e:
                    logger.error(e)
                    members = False
            n_p  = 0
            a_p = 0
            new_players = []
            if  members:
                for p in members:
                    
                    p_name = p["Name"]
                    p_fame = int(p["KillFame"]) +int(p["LifetimeStatistics"]["PvE"]["Total"])+ int(p["LifetimeStatistics"]["Crafting"]["Total"]) + int(p["LifetimeStatistics"]["Gathering"]["All"]["Total"])
                    #pesquisa no discord
                    dsPlayer = self.members_ds(guild,p_name)
                    nick_discord = None
                    ref_discord = None
                    if dsPlayer:
                        ref_discord = dsPlayer.id
                        nick_discord = dsPlayer.nick

                    #registra - NOVO
                    if not is_player_exist(p_name):
                        
                        new_player = Members(
                            guild_id=guild.id,
                            name=p_name,
                            fame = int(p_fame),
                            is_blacklist = False,
                            is_cargo = False,
                            ref_discord = ref_discord,
                            nick_discord = nick_discord
                        )
                        session.add(new_player)
                        session.flush()
                        new_player_tax = Taxa(
                            name = p_name,
                            guild_id = guild.id, 
                            saldo = 0, 
                            deposito = 0,
                            ciclo = 0
                        )
                        session.add(new_player_tax)
                        session.flush()
                        
                        logger.debug(f"<{p_name}> adicionado")
                        msg = f"{p_name}"
                        if ref_discord:
                            msg += f" - Discord <@{ref_discord}>"      
                        new_players.append(msg)
                        n_p += 1
                    #ATUALIZA    
                    else:
                        pl = obter_dados(Members,p_name)
                        #print(pl)
                        if bool(pl):
                            tx = obter_dados(Taxa,p_name)
                            pl.fame = int(p_fame)
                            pl.guild_id = guild.id
                            if tx:
                                tx.guild_id = guild.id
                            pl.ref_discord = ref_discord
                            pl.nick_discord = nick_discord
                            session.flush()
                        logger.debug(f"<{p_name}> atualizando fama: {p_fame}")
                        a_p += 1

                session.commit()
                logger.info(f"Processo de obtenção de players realizado. NOVOS: {n_p} ATUALIZADOS: {a_p}")
                return new_players
            else:
                logger.warning(f"Não tem membros.")
                return None
        else:
           
            logger.debug(f"<{guild.name}> não pode verificar novos players devido a falta do ID DO ALBION. Tente atualizar com <?rg>")     
            return None   

    #obtem novos jogadores
    async def remove_players_in_guild(self, guild, members = None):
        #db_memb = session.query(Members).filter_by(guild_id = guild_id)
        logger.info("REMOVE")
        if guild.id_ao is not None or not "":
            #print(members)
            if members == None:
                try:
                    members = await get_guild_members(guild.id_ao)
                except aiohttp.ContentTypeError as e:
                    logger.error(e)
                    members = None
            logger.info(f"Verificando...")
            db_memb = session.query(Members).filter_by(guild_id = guild.id).all()
            count_db = len(db_memb) if isinstance(db_memb,(list,tuple,dict)) else 0
            count_api = len(members) if isinstance(members,(list,tuple,dict)) else 0
            logger.warning(f"CONTAGENS: DB: {count_db} :: API:{count_api}")
            p_list = []
            del_p = 0
            del_players = []
            if members:

                for p in members:
                    p_list.append(p["Name"])
 
                for memb in db_memb:

                    if memb.name not in p_list:
                        if bool(memb.ref_discord):
                            try:
                                dsguild = bot.get_guild(guild.id)
                            except HTTPException as e:
                                dsguild = False
                                logger.error(e)
                            if bool(dsguild):
                                dsmember = dsguild.get_member(memb.ref_discord)
                                if bool(dsmember):
                                    try:
                                        await dsmember.edit(roles=[], reason="Exit from guild albion")
                                    except HTTPException as e:
                                        logger.error(e)
                        msg = f"{memb.name} "
                        if memb.ref_discord:
                            msg += f"- Discord <@{memb.ref_discord}>"
                        del_players.append(msg)

                        try:
                            session.delete(memb)
                        except SQLAlchemyError as e:
                            session.rollback()
                            logger.error(e)
                        session.flush()
                        del_p +=1
                           
                logger.info(F"Processo de delete de players realizado. DELETADO {del_p}")
                session.commit()
                return del_players
            else:
                logger.warning(F"Não foi possibel obter membros")
                return None
        else:
            logger.debug(f"<{guild.name}> não pode verificar novos players devido a falta do ID DO ALBION. Tente atualizar com <?rg>")      
            return None 
    #obtem ranking semanal do albion
    async def ranking_semanal(self,gid, tipo_ranking=0, sub_g = 0, region=0):
        '''
        gid:            ID Guild Albion
        tipo_ranking :  PvE, 1= Gatherering
        sub_g:          All | Fiber | Hide | Ore | Rock | Wood
        region:         Total | Royal | Outlands | Hellgate
        obtem o top 10 players pve da guilda
        '''
        #print(f'{sub_g} : {sub_g}: {region}')
        data_ranking = await get_statistics_guild(gid, types=tipo_ranking, subtype=sub_g,  region =region)
        d_p={}
        i = 0

        for p in data_ranking:
            i +=1
            d_p[i] = { "Name": p["Player"]["Name"],
                        "Fame": p["Fame"]
                    }
            d_p.update(d_p)
        logger.debug(f"Dados dos players no top pve semanal \n\n{d_p}")
        return d_p
    
        #Obtem devedores - SISTEMA DE CONTRIBUIÇÃO
    # OBTEM LISTA DE DEVEDORES -SISTEMAS DE TAXAS
    async def calculate_guild_tax (self,taxa_d,gd,memb):
        c_m =len(memb)
        taxa_n = []
        for p in taxa_d:
            taxa_n.append(p.name)
        min_fame = gd.fame_taxa
        c_taxa = gd.taxa_p
        logger.info(f'Quantidade de players: {c_m}')
        count_tx = len(taxa_n)
        isentions = session.query(Members).filter_by(guild_id = gd.id, isention = True).all()
        p_o = session.query(Members).filter_by(guild_id =gd.id).all()
        listpl = []
        for p in p_o:
            listpl.append(p.name)
        for p in memb:
            pn = p["Name"]
            taxa_n.append(pn)
            pf = p["KillFame"] +p["LifetimeStatistics"]["PvE"]["Total"]+ p["LifetimeStatistics"]["Crafting"]["Total"] + p["LifetimeStatistics"]["Gathering"]["All"]["Total"]
            if p not in listpl:
                new_player = Members(name = pn, guild_id = id)
                add_dados(new_player)
                logger.debug(f"Player adicionado ao banco: {new_player}")
            if pn not in taxa_n and pf >= min_fame:
                if pn not in isentions:
                    new_contrib = Taxa(name=pn, depositos = 0, saldo = -c_taxa, ciclo = 1)
                    add_dados(new_contrib)
                else:
                    logger.debug(f"{pn} é isento")
            else:
                logger.debug(f"Não incluido: {pn}")
        #se o player sair,é removido do banco de dados
        for p in taxa_d:
            if p not in taxa_n:
                deletar_dados(Taxa,p)
                deletar_dados(Members,p)
                logger.warning(f'>{gd["name"]}  player: {p} removido por ter saido da guilda! Ou ser da lista de isencao')
        dev = session.query(Taxa).filter_by(guild_id=gd.id)
        c_m = session.query(Members).filter_by(guild_id = gd.id).count()
        count_tx = dev.count()
        logger.info(f'\n>>>Total de membors: {c_m}>>> \nTotal no sistema de taxas: {count_tx} \n>>> Diferença: {c_m - count_tx} \n>>>Total de devedores: {count_tx}')
        return dev
    
    #comando de ajuda de instalação do bot
    @commands.command(name="h", help="Tutorial for instalation bot in server")
    async def help_guild_register(self, ctx, lang="english"):
        g = obter_dados(Guild,ctx.guild.id)
        if g:
            lang = g.lang
        mdb = init_json(cfg['msg_path'])
        tr = mudarLingua(lang)
        for info in mdb['tutorial']:
            embed = discord.Embed(title=tr.translate(info.get('title')),color=discord.Color.dark_green())
            embed.description = tr.translate(info.get('desc'))
            if info.get("commands"):
                coms = info.get("commands")
                for com in coms:
                    link =""
                    if com.get('u'):
                        link = " [Click-me](" + str(com.get('u')) + ")"
                    ms = tr.translate(str(com.get('i'))) + link
                    #print(ms)
                    embed.add_field(name=tr.translate(com.get('c')), value=ms, inline=False)
                    embed.video.url = com.get('u')
            embed.add_field(name=tr.translate("Mais"), value = tr.translate(mdb['footer']))
            await ctx.send(embed=embed)
                        
    @commands.command(name="list_language")
    async def lista_liguagens(self,ctx):
            tr = GoogleTranslator()
            m = ""
            lg = tr.get_supported_languages()
            for l in lg:
                m += str(l) + "\n"
            await ctx.send(m)
    #comando para registrar discord e guild ok
    @commands.command(name="rg", help="Register guild and discord in bot. note: If the name has a space, replace the space with '_' . Ex: ?rg S A M U -> ?rg S_A_M_U")
    async def guild_register(self, ctx, guildname="",language="english"):
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(language)

        news = None
        if not tr:
            lista = "\n"
            for l  in GoogleTranslator().supported_languages:
                lista += l + "\n"
            await ctx.send(f"Is language not available. please try another language: {lista}")
            return 0
        else:
            embed = discord.Embed(title=tr.translate(msg['rg']['title']),color=discord.Color.dark_green())
            embed.add_field(name=tr.translate("Mais"), value = tr.translate(msg['footer']))
            await ctx.channel.trigger_typing()
            logger.info(f"#Registrando Guilda {bool(is_guild_owner(ctx))}")
            if is_guild_owner(ctx):
                if len(guildname)<1:
                    guildname=ctx.guild.name
                else:
                    guildname = guildname.replace("_", " ")
                await ctx.channel.trigger_typing()
                try:    
                    id_guild = await get_guild_id(guildname)
                except aiohttp.ContentTypeError as e:
                    id_guild = None
                    logger.error(e)
                    logger.error(msg["rg"]["fail-ao"].format(guildname))
                    embed.description = tr.translate(msg["rg"]["fail-ao"].format(guildname))
                    embed.color = discord.Color.red()
                    await ctx.send(embeds=embed)

                await ctx.channel.trigger_typing()
                logger.info(f"Registrando: {ctx.guild.id}")
                id_ali = ""
                if id_guild:
                    try:
                        guild = await get_guild_info(id_guild)
                    except aiohttp.ContentTypeError as e:
                        guild = None
                        logger.error(e)
                    # SALVA DADOS EM VARIAVEIS
                    if guild:
                            id_ali = guild['AllianceId']
                if is_guild_reg(ctx.guild.id):

                    result = obter_dados(Guild,ctx.guild.id)
                    result.name = guildname
                    session.flush()
                    result.id_ao = id_guild
                    session.flush()
                    result.id_ali = id_ali
                    session.flush()
                    result.lang = language
                    session.commit()
                    embed.description = tr.translate(msg["rg"]["players"]["search"].format(result.id_ao)) + "\n" + tr.translate(msg["rg"]["updated"].format(guildname))
                    embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))
                    embed.color = discord.Color.blue()                   
                    await ctx.send(embed = embed)
                else:
                    new = Guild(
                        id = ctx.guild.id,
                        name = guildname,
                        id_ali = id_ali,
                        id_ao = id_guild,
                        lang = language,
                        top = False,
                        taxap_s = False,
                        taxac_s = False
                    )
                    await ctx.channel.trigger_typing()
                    try:
                        add_dados(new)
                    except:
                        embed.description = tr.translate(msg["rg"]["fail"].format(guildname)) + ctx.author.mention
                        embed.color = discord.Color.red()
                        embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))      
                        await ctx.send(embed = embed)
                        return 
                    else:
                        embed.description = tr.translate(msg["rg"]["sucess"].format(guildname))
                        embed.color = discord.Color.green()
                        embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))                          
                        logger.info(msg["rg"]["sucess"].format(guildname))
                        await ctx.send(embed=embed)
                        if new.id_ao != None != "":
                            embed.description = tr.translate(msg["rg"]["players"]["search"].format(new.id_ao))
                            embed.color = discord.Color.dark_teal()
                            embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))
                            await ctx.send(embed=embed)
                        else:
                            embed.description = tr.translate(msg["rg"]["players"]["fail"])
                            embed.color = discord.Color.dark_purple()
                            embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))
                            await ctx.send(embed=embed)
                    result = new
                try:
                       new_members =  await self.get_new_players_in_guild(result)
                except: 
                    new_members = False
                    embed.description = tr.translate(msg["rg"]["players"]["fail"])
                    embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))
                    embed.color = discord.Color.dark_purple()
                    await ctx.send(embed=embed)
                if new_members:
                    for m in new_members:
                        news += f"{m}\n"
                    new_members = False
                    embed.description = news
                    embed.color = discord.Color.green()
                    embed.add_field(name=tr.translate(msg['more']),value = tr.translate(msg['footer']))
                    await ctx.send(embed=embed)
            else:
                await ctx.send(tr.translate(tr.translate(msg["rg"]["is-owner"]) + ctx.author.mention))
    
    #comando para listar guilds registradas ok
    @commands.command(name="lg", help="Lists guilds registered in the bot")
    @commands.is_owner()
    async def guilds_list(self,ctx, lang ="english"):
        '''
        LISTA GUILDS
        '''
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return

        #print(commands.Bot.owner.name)
        try:
            datag = session.query(Guild).all()
        except discord.errors.HTTPException as e:
            msg = f"Bad request guild list: {e}"
            logger.error(tr.translate(msg))
        else:
            bf =""
            for g in datag:
                bf += g.name
                bf += "\n"
            logger.info("[lg] Ok!")
            await ctx.send(bf)
    
    #comando para cadastrar cargos(roles) ok
    @commands.command(name="rr", help="Requires prior registration. Add management positions")
    async def register_role(self,ctx, roles:str, language ="english"):
        #        '''
        #        REGISTRA CARGO NO BOT
        #        DEVE TER PERMISSÃO     
        #        '''
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(language)

        idg = ctx.guild.id
        if is_guild_reg(idg):
            guildg = obter_dados(Guild,idg)
            if  guildg is None:
                    await ctx.send("<DB Error> not get GUILD! Try it")
                    return
            tr = GoogleTranslator(source='auto', target=guildg.lang)
            if has_roles(ctx):
                    if roles not in cargos_list(idg):
                        new = Cargos(
                            name = roles,
                            guild_id = ctx.guild.id
                        )
                        add_dados(new)
                        logger.info(f"[rr] {ctx.guild.name} o {ctx.author.nick} registrou o cargo {roles}.")
                        await ctx.send(tr.translate(msg["rr"]["sucess"].format(ctx.guild.name,ctx.author.mention,roles)))
                    else:
                        await ctx.send(tr.translate(f"<{roles}> has already been added!"))
            else:
                await ctx.send(tr.translate(msg["rr"]["not-role"].format(ctx.guild.name, ctx.author.mention)))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))
    
    #comando para listar cargos adicionados ok
    @commands.command("lr", help="list added positions")
    async def lista_cargos(self,ctx, lang="english"):
        msg = init_json(cfg['msg_path'])

        g = obter_dados(Guild,ctx.guild.id)
        if g:
            lang = g.lang
        tr = mudarLingua(lang)
        
        '''
        LISTA CARGOS COM PERMISSÕES CADASTRADOS NO BOT (POR SERVIDOR)
        '''
        bf=""
        ro = session.query(Cargos).filter(Cargos.guild_id == ctx.guild.id).all()
        #print(f"<<{ro}>> {len(ro)}")
        for r in ro:
            #print(r.name)
            bf+= r.name
            bf+="\n"
        if (len(ro)>0):
            logger.info("[lr] ok!")
            await ctx.send(bf)
        else:
            await ctx.send(tr.translate("Roles Not registred!\n[Owner Server] Use **?rr** for registration role administration."))
    

    '''
     TAREFAS DE TRANSMISSÕES DO TOP - TASKS
    '''
    # SISTEMA DE CONTRIBUIÇÃO
    @tasks.loop(hours=6)
    async def contrib_tax(self):
        lang = "english"
        tr = mudarLingua(lang)
        datag = session.query(Guild).filter(Guild.taxap_s == True).all()
        #client = discord.Client()
        ss = 0
        for g in datag:
            lang = g.lang
            tr = mudarLingua(lang)

            try:
                channel = bot.get_channel(g.canal_taxa)
            except :
                logger.error("Fail get channel for send contrib!")
                return
            logger.warning(f'Iniciando sistema de contribuição da guilda: {g.name}')

            taxa = session.query(Members).join(Taxa).filter(Members.guild_id == g.id, Members.isention == False, Taxa.saldo <0 ).all()
            embed = discord.Embed(title=tr.translate(msg["title_tax"]), color = discord.Color.dark_magenta())
            desc = "\n"

            desc2 = desc
            desc3 = desc
            desc4 = desc
            p2 = None
            p3 = None 
            p4 = None
            c = 0
            max_ = math.ceil(len(taxa)/75)
            for p in taxa:
                c+=1
                sald = abs(p.taxa.saldo)
                ss+= abs(p.taxa.saldo)
                if c < 75:
                    if c == 1:
                        desc = f"\n**P 1/{int(max_)}** \n\n "
                    desc += f'{c}º **{p.name} ** <@{p.ref_discord}> \n {size(sald,system=si)}\n\n'
                if c >= 75 and c <150:
                    p2 = True
                    if c == 75:
                        desc2 = f"\n**P 2/{int(max_)}** \n\n "
                    desc2 += f'{c}º **{p.name} ** <@{p.ref_discord}> \n {size(sald,system=si)}\n\n'
                if c >= 150 and c <225:
                    p3 = True
                    if c == 150:
                        desc3 = f"\n**P 3/{int(max_)}** \n\n "
                    desc3 += f'{c}º **{p.name} ** <@{p.ref_discord}> \n {size(sald,system=si)}\n\n'
                if c >= 225 and c <300:   
                    p4 = True 
                    if c == 225:
                        desc4 = f"\n**P 4/{int(max_)}** \n\n "
                    desc4 += f'{c}º **{p.name} ** <@{p.ref_discord}> \n {size(sald,system=si)}\n\n'
                    
            embed.add_field(name=tr.translate("Quantidade de Inadiplente"), value = len(taxa), inline=True)
            embed.add_field(name=tr.translate(msg["tax"]["info"]), value = size(ss,system=si), inline=True)
            embed.add_field(name=tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
            embed.set_footer(text = tr.translate(msg["tax"]["foot"]))
            
            try:
                embed.description= desc
                await channel.send(embed=embed)
            except:
                logger.warning("Não existe canal")
            
            if p2 == True:
                embed.description= desc2
                try:
                    await channel.send(embed=embed)
                except:
                    logger.warning("Não existe canal")
            if p3 == True:
                embed.description= desc3
                try:
                    await channel.send(embed=embed)
                except:
                    logger.warning("Não existe canal")
                    
            if p4 == True:
                embed.description= desc4
                try:
                    await channel.send(embed=embed)
                except:
                    logger.warning("Não existe canal")
            logger.info(f'Fim do sistema de contribuição da guilda: {g.name}')

                
    #top pve
    @tasks.loop(hours=24)
    async def players_top_pve(self):
            lang = "english"
            tr = mudarLingua(lang)
            logger.info("Trabalhando para emitir top semanal pve")
            datag = session.query(Guild).filter_by(top = True).all()
            for g in datag:
                lang = g.lang
                tr = mudarLingua(lang)
                if  g.top == True:
                    client = discord.Client()
                    if(g.canal_top is not None and g.id_ao is not None):
                        try:
                            channel = bot.get_channel(g.canal_top)
                        except:
                            logger.warning(f"Canal não localizado da guilda {g.name}")
                            return
                        if not tr:
                            await channel.send(tr)
                            return
                        logger.info(tr.translate(f"<{g.name}> Aguardando dados do Albion"))
                        try:
                            d = await self.ranking_semanal(g.id_ao)
                        except:
                            logger.debug(f"<{g.name}> Não foi possivel enviar informações do top ranking")
                            await channel.send(tr.translate(f"<{g.name}> Please verify re-register in bot. No get data from albion."))
                        embed = discord.Embed(title= tr.translate(msg["title_c"].format(g.name)), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                        
                        embed.add_field(name= tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                        
                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Não foi possivel enviar mensagem")

                        logger.info("Trabalho realizado com sucesso!")

    
    #top coletores
    @tasks.loop(hours=24)
    async def players_top_g(self):
            lang = "english"
            tr = mudarLingua(lang)

            datag = session.query(Guild).filter_by(top = True).all()
            logger.info("Trabalhando para emitir top semanal coletor")
            for g in datag:
                lang = g.lang
                tr = mudarLingua(lang)
                if  g.top == True:
                    #client = discord.Client()
                    if(g.canal_top is not None and g.id_ao is not None):
                        try:
                            channel = bot.get_channel(g.canal_top)
                        except:
                            logger.warning(f"Canal não localizado da guilda {g.name}")
                        if not tr:
                            await channel.send(tr)
                            return
                        logger.info(f"<{g.name}>Aguardando dados do Albion")
                        try:
                            d = await self.ranking_semanal(g.id_ao, tipo_ranking= 1)
                        except:
                            logger.error("Não foi possivel enviar informações do top ranking")
                            try:
                                await channel.send(tr.translate("Please verify re-register in bot. No get data from albion."))
                            except HTTPException as e:
                                logger.error(e)
                        embed = discord.Embed(title= tr.translate(msg["title_pve"].format(g.name)), color=discord.Color.gold())
                        for p in d:
                            if d[p]["Fame"] >1000:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=size(d[p]["Fame"],system=si), inline=False)
                            else:
                                embed.add_field(name= f'{p}º {d[p]["Name"]}', value=d[p]["Fame"], inline=False)
                            
                        embed.add_field(name=tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)

                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Não foi possivel enviar mensagem")

                        logger.info("Trabalho realizado com sucesso!")


    
    #obtem gerencia jogaores
    @tasks.loop(hours=6)
    async def gerencia_jogadores(self):
        tr = mudarLingua("english")
        sttot = dt.now()    
        list_guild_reg = session.query(Guild).filter(Guild.id_ao != None).all()
        total = len(list_guild_reg)
        num = 0
        for guild in list_guild_reg:
            num += 1
            st = dt.now()
            logger.info(f"{num}/{total} - Removendo jogadores que sairam <{guild.name}>")
            tentativa = 0
            encontrou = False
            logger.info("Tentando encontrar registros no albion: ")
            while tentativa <= 5 and encontrou == False:
                tentativa += 1
                logger.info(f"T {tentativa}/5")
                try:
                    members = await get_guild_members(guild.id_ao)
                except aiohttp.ContentTypeError as e:
                    logger.error(e)
                    members = False
                if members:
                    logger.info(f"Encontrou registros: {len(members)} na tentativa {tentativa}")
                    encontrou = True
                if tentativa == 5:
                    logger.warning("Não foi possivel encontrar registros")
            saiu = await self.remove_players_in_guild(guild, members)
            logger.info(f"Verificando novos jogadores da guild <{guild.name}>")
            entrou = await self.get_new_players_in_guild(guild, members)
            logger.info(f"({dt.now() - st}) Sucess <{guild.name}>")
            #print(guild.canal_info)
            if guild.canal_info:
                tr = mudarLingua(guild.lang)  
                try:
                    channel = bot.get_channel(guild.canal_info)
                except HTTPException as e:
                    channel = None
                    logger.error(e)
                if channel:
                    if saiu:
                        desc = ""
                        embed = discord.Embed(title= tr.translate("Jogadores que sairam da guild"), color=discord.Color.red())
                        for player in saiu:
                            desc += f"{player} \n"
                        embed.description = desc
                        try:
                            await channel.send(embed=embed)
                        except HTTPException as e:
                            logger.error(e)
                    if entrou:
                        desc = ""
                        embed = discord.Embed(title= tr.translate("Jogadores que Entraram da guild"), color=discord.Color.gold())
                        for player in entrou:
                            desc += f"{player} \n"
                        embed.description = desc
                        try:
                            await channel.send(embed=embed)
                        except HTTPException as e:
                            logger.error(e)
            else:
                logger.info(f"<{guild.name}> não possui canal info registrado")
        logger.info(f"Tarefa de gerenciamento de jogadores concluido! ({dt.now() - sttot})")
        

    @tasks.loop(hours=24)
    async def players_top_pvp(self):
            
            lang = "english"
            tr = mudarLingua(lang)
            datag = session.query(Guild).filter_by(top = True).all()
            logger.info("Trabalhando para emitir top semanal PVP")
            for g in datag:
                logger.info(f"Iniciando {g.name}")
                lang = g.lang
                tr = mudarLingua(lang)
                if(g.canal_top is not None and g.id_ao is not None):
                    #print(f"{g.name} : {g.canal_top} > {g.id_ao}")

                    try:
                        channel = bot.get_channel(g.canal_top)
                    except:
                        logger.warning(f"Canal não localizado da guilda {g.name}")
                    if not tr:
                        await channel.send(tr)
                        return
                    logger.info("Aguardando dados do Albion")
                    try:
                        tops = await get_guild_top_kills(g.id_ao)
                    except aiohttp.ContentTypeError as e:
                        tops = False
                        logger.error(e)
                        try:
                            await channel.send(tr.translate("Não foi possivel obter TOP PVP - Não foi possivel comunicar com albion"))
                        except:
                            logger.error("Canal não existe")
                    if bool(tops):
                        embed = discord.Embed(title= tr.translate(msg["title_pvp"].format(g.name)), color=discord.Color.gold())
                        #aqui
                        k = 0
                        for kill in tops:
                            k += 1
                            if isinstance(kill,dict):
                                totalFame = kill['TotalVictimKillFame']
                                if totalFame >1000:
                                    totalFame =  size(totalFame, system=si)
                                data = date_format(kill['TimeStamp'])
                                killer = kill['Killer']['Name']
                                vitima = kill['Victim']['Name']
                                text = f"{k}º {killer} -  ☠️ {vitima}"
                                
                                text = tr.translate(text)
                                    
                                val = f"{totalFame} Fama em {data}"

                                if kill['numberOfParticipants']:
                                    assistencia = kill['numberOfParticipants']
                                    if assistencia > 0:
                                        val += f" com {assistencia} assistências"
                                
                            embed.add_field(name= text , value=val, inline=False)
                                
                        embed.add_field(name=tr.translate(msg["more"]), value=tr.translate(msg["footer"]), inline=False)
                        try:
                            await channel.send(embed=embed)
                        except:
                            logger.error("Canal não existe")
                    logger.info("Trabalho realizado!")

    #negativados - lista de devedores de taxas_fixas
    '''
    @tasks.loop(hours=6)
    async def negativados(self):
        #1 - verifica se TODOS os player tem contribuições (TAXA.JSON)
        
        datag = session.query(Guild).filter_by(taxap_s = True).all()
        for g in datag:
            channel = bot.get_channel(datag.canal_taxa)
            embed = discord.Embed(title= f'NEGATIVADOS [{datag.name}]', color=discord.Color.red())
            data = session.query(Taxa).filter_by(guild_id = g.id).all()
            #1.1 - ADICIONA LISTA :
            for p in data:
                saldo = data.saldo
                #debito = deposito - taxa_fixa*ciclo
                taxa = g.taxa_p
                #PLAYER com debito  de debito   = SE deposito < taxa_fixa*ciclo
                if saldo < taxa:  
                    embed.add_field(name = p)
                    embed.add_field(value = saldo)  
                    #2 - ENVIA A LISTA DOS PLAYERS EM DEBITOS
            embed.add_field(name= "Mais", value=fot, inline=False)
            await channel.send(embed=embed)
    '''
    '''
        Registro de canal para transmisção dos top
    '''
    #comando registra canal top
    @commands.command("rt", help="Register channel for TOP's transmission")
    async def registra_canal_top(self,ctx, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            lang = datag.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if has_roles(ctx):
                
                datag.top = True
                session.flush()
                datag.canal_top = ctx.channel.id
                session.commit()
                logger.info(f"Canal para transmitir top semanal: {ctx.channel.name}")
                await ctx.send(tr.translate(f"Canal para transmitir top semanal: {ctx.channel.name}"))
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(tr.translate(msg["english"]["not-reg"]))
    
    #comando registra canal taxa
    @commands.command("rtx", help="Register channel for tax transmission")
    async def registra_canal_taxa(self,ctx, tax = None, min_fame = None, lang = "english"):
        tr = mudarLingua(lang)
        msg = init_json(cfg['msg_path'])
        embed = discord.Embed(title= tr.translate("Sistema de Taxa de guild"), color=discord.Color.gold())
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            embed = discord.Embed(title= tr.translate(msg["taxa"]['title'].format(datag.name)), color=discord.Color.gold())
            
            lang = datag.lang
            tr = mudarLingua(lang)
            if has_roles(ctx):
                datag.taxap_s = True
                session.flush()
                datag.canal_taxa = ctx.channel.id
                session.flush()
                if tax:
                    datag.taxa_p = int(tax)
                    session.flush()
                if min_fame:
                    datag.fame_taxa = int(min_fame)
                    session.flush()
                session.commit()
                logger.info(f"Canal para transmitir taxa: {ctx.channel.name}")
                embed.description = tr.translate(f"Canal para transmitir taxa: #{ctx.channel.name}") 
                embed.add_field(name=tr.translate("Taxa de prata:"), value=datag.taxa_p)
                embed.add_field(name=tr.translate("Fama minima:"), value=datag.fame_taxa)
                embed.add_field(name=tr.trans(msg['more']), value = msg['footer'])
                await ctx.send(embed=embed)
            else:
                embed.description = tr.translate(tr.translate(msg["rg"]["is-owner"]))
                embed.add_field(name=tr.trans(msg['more']), value = msg['footer'])
                await ctx.send(embed=embed)
        else:
            embed.color= discord.Color.dark_red()
            embed.description = tr.translate(tr.translate(msg["not-reg"]))
            embed.add_field(name=tr.trans(msg['more']), value = msg['footer'])
            await ctx.send(embed=embed)
    
    #comando registra canal blacklist
    @commands.command("rb", help="Register channel for blacklist transmission")
    async def registra_canal_black(self,ctx, lang="english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            lang = datag.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if has_roles(ctx):
                datag.canal_blacklist = ctx.channel.id
                session.commit()
                logger.info(tr.translate(f"({ctx.guild.id}) - Canal para transmitir blacklist: {ctx.channel.name}"))
                await ctx.send(tr.translate(f"({ctx.guild.id}) - Canal para transmitir blacklist: {ctx.channel.name}"))
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(tr.translate(msg["english"]["not-reg"]))
    
    #comando registra canal 
    
    @commands.command("rgi", help="Register channel for guild info transmission")
    async def registra_canal_guild_info(self,ctx):
        lang = "english"
        tr = mudarLingua(lang)
        if is_guild_reg(ctx.guild.id):
            datag = obter_dados(Guild,ctx.guild.id)
            tr = mudarLingua(datag.lang)
            if has_roles(ctx):
                datag.canal_info = ctx.channel.id
                session.commit()
                logger.info(f"({ctx.guild.id}) - Canal para transmitir info: {ctx.channel.name}")
                await ctx.send(f"({ctx.guild.id}) - Canal para transmitir info: {ctx.channel.name}")
            else:
                await ctx.send(tr.translate(msg["rg"]["is-owner"]))
        else:
            await ctx.send(msg["not-reg"])
    
    '''
        COMANDOS TASKS
    '''
    #ativa task top pve
    @commands.command("stpve", help= "Starts task of presenting weekly top every 8h")
    @commands.is_owner()
    async def start_top_pve(self,ctx):
        logger.info("Iniciou tarefa de emitir top semanal pve!")
        await ctx.send(self.players_top_pve.start())
    
    #ativa task top coletor
    @commands.command("stg", help= "Starts task of presenting weekly top collection every 8h")
    @commands.is_owner()
    async def start_top_g(self,ctx):
        logger.info("Iniciou tarefa de emitir top coleta semanal coleta!") 
        await ctx.send(self.players_top_g.start())
   
    @commands.command("stt", help= "Starts task of tax silver every 12h")
    @commands.is_owner()
    async def start_contrib(self,ctx):
        logger.info("Iniciou tarefa de emitir devedores!") 
        await ctx.send(self.contrib_tax.start())
   
    @commands.command("stp", help= "Starts task of player for tick 12h")
    @commands.is_owner()
    async def start_gplayer(self,ctx):
        logger.info("Iniciou tarefa de gerenciar players!") 
        await ctx.send(self.gerencia_jogadores.start())

    @commands.command("stpvp", help= "Starts task of player for tick 12h")
    @commands.is_owner()
    async def start_process(self,ctx):
        await ctx.send(self.players_top_pvp.start())
        logger.info("Pronto")
        
        
    @commands.command("gpl", help = "list all players in guild")
    async def guild_players_list(self,ctx, lang = "english"):
        tr = mudarLingua(lang)
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            lang = guild.lang
            tr = mudarLingua(lang)
            players = guild.members
            #print(players)
            if not players:
                #print(
                players = session.query(Members).filter_by(guild_id = ctx.guild.id).all()
                #print(players)
            if not players:
                await ctx.send(tr.translate("Your guild has no players, or has not been registered in our junk"))
            else:
                msg = ""
                msg2 = ""
                count = len(players)
                embed = discord.Embed(title= tr.translate(f"Players({count}) List"), color=discord.Color.gold())
                #print(count)
                c =0
                for p in players:
  
                    if c <= 150:
                        msg += f"{p.name}"
                        if p.ref_discord:
                            msg += f"<@{p.ref_discord}>"
                        msg += "\n"
                        if c == 150:
                            embed.description =  msg
                            await ctx.send(embed=embed)
                    else:
                        msg2 += f"{p.name}"
                        if p.ref_discord:
                            msg2 += f"<@{p.ref_discord}>"
                        msg2 += "\n"
                        if c >= count:
                            embed.description =  msg
                            await ctx.send(embed=embed)
                    c+=1
            logger.info("Fim de busca - players")
        else:
            await ctx.send(tr.translate("Sua guild não foi encontrada nos meus bagulhos"))


    @commands.command("gpc", help = "check player in guild")
    async def guild_players_check(self,ctx, nick, lang= "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return

        #print(nick)
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            #print(guild)
            player = obter_dados(Members,nick)
            lang = guild.lang
            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return
            if guild.id != player.guild.id:
                player = None
            if not player:
                embed = discord.Embed(title= tr.translate(f"player is no your guild, or has not been registered in our junk"), color=discord.Color.red())
                #await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title= tr.translate(f"{player.name} is in {player.guild.name}"), color=discord.Color.blue())
                # v= size(player.fame,system='si')
                # embed.description = f"Fame: {v}" 
            await ctx.send(embed=embed)
            logger.info("Fim de busca - players")

    @commands.command("remove_guild", help = "remove guild")
    @commands.is_owner()
    async def remove_guild(self, ctx, id_g = None, lang = 'english'):
        id = ctx.guild.id
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if(id_g):
            id= id_g
        deletar_dados(Guild,id)
        await ctx.send(tr.translate("sua guild foi removida"))
        

    @commands.command()
    @commands.is_owner()
    async def teste(self,ctx):
        guild = obter_dados(Guild,ctx.guild.id)
        logger.info(f"INICIANDO")
        st = dt.now()
        tentativa = 0
        encontrou = False
        logger.info("Tentando encontrar registros no albion: ")
        while tentativa <= 5 and encontrou == False:
            tentativa += 1
            logger.info(f"T {tentativa}/5")
            try:
                members = await get_guild_members(guild.id_ao)
            except aiohttp.ContentTypeError as e:
                logger.error(e)
                members = False
            if members:
                logger.info(f"Emcontrou registros: {len(members)} na tentativa {tentativa}")
                encontrou = True
            if tentativa == 5:
                logger.warning("Não foi possivel encontrar registros")
        saiu = await self.remove_players_in_guild(guild, members)
        print(saiu)
        logger.info(f"Verificando novos jogadores da guild <{guild.name}>")
        entrou = await self.get_new_players_in_guild(guild, members)
        print(entrou)
        logger.info(f"({dt.now() - st}) Sucess <{guild.name}>")
        #print(guild.canal_info)
        if guild.canal_info:
            tr = mudarLingua(guild.lang)  
            try:
                channel = bot.get_channel(guild.canal_info)
            except HTTPException as e:
                channel = None
                logger.error(e)
            if channel:
                if saiu:
                    desc = ""
                    embed = discord.Embed(title= tr.translate("Jogadores que sairam da guild"), color=discord.Color.red())
                    for player in saiu:
                        desc += f"{player} \n"
                    embed.description = desc
                    try:
                        await channel.send(embed=embed)
                    except HTTPException as e:
                        logger.error(e)
                if entrou:
                    desc = ""
                    embed = discord.Embed(title= tr.translate("Jogadores que Entraram da guild"), color=discord.Color.gold())
                    for player in entrou:
                        desc += f"{player} \n"
                    embed.description = desc
                    try:
                        await channel.send(embed=embed)
                    except HTTPException as e:
                        logger.error(e)
        else:
            logger.info(f"<{guild.name}> não possui canal info registrado")
 
    
    @commands.command("lpd", help = "check player in guild")
    async def list_player_debito(self,ctx, minDebito = 0, lang ="english"): 
        guild = obter_dados(Guild,ctx.guild.id)
        msg = init_json(cfg['msg_path'])
        lang = guild.lang
        logger.info(f"INICIANDO")
        tr = mudarLingua(lang)
        logger.info(f"Tentando encontrar registros de devedores no albion: {guild.name}")
        embed = discord.Embed(title= tr.translate(f"Sistema de Taxa de guild - DEVEDORES 💰{guild.name}💰"), color=discord.Color.red())
        if guild:
            if guild.taxap_s == True:
                memb = ''
                memb2 = ''
                memb3 = ''
                list_caloteiro =  session.query(Members).join(Taxa).filter(Members.guild_id == ctx.guild.id, Members.isention == False, Taxa.saldo < int(minDebito)).all()
                count =0
                #logger.warning(list_caloteiro)
                #logger.warning(f"Total de devedores: {len(list_caloteiro)}")
                p2 = None
                p3 = None
                p4 = None
                max_ = math.ceil(len(list_caloteiro)/75)
                saldoTot = 0
                for p in list_caloteiro:
                    saldoTot += abs(p.taxa.saldo)
                    count +=1
                    if count <75:
                        if count == 1:
                            memb = tr.translate(f"\n**P 1/{int(max_)}**")
                        memb += f"\n\n{count}º **{p.name}** - <@{p.ref_discord}> \n{size(-p.taxa.saldo, system=si)}"

                    if  count >= 75 and count <150:
                        p2 = True
                        if count == 75 :
                            memb2 = tr.translate(f"**P 2/{int(max_)}**")
                        memb2 += f"\n\n{count}º **{p.name}** - <@{p.ref_discord}> \n{size(-p.taxa.saldo, system=si)}"
                    if count >=150 and count <=225:
                        p3 = True
                        if count == 150 :
                            memb3 = tr.translate(f"**P 3/{int(max_)}**")
                        memb3 += f"\n\n{count}º **{p.name}** - <@{p.ref_discord}> \n{size(-p.taxa.saldo, system=si)}"
                    if count >=225 and count <=300:
                        p4 = True
                        if count == 225 :
                            memb4 = tr.translate(f"**P 4/{int(max_)}**")
                        memb4 += f"\n\n{count}º **{p.name}** - <@{p.ref_discord}> \n{size(p.taxa.saldo, system=si)}"                        
                embed.description= memb
                embed.add_field(name=tr.translate(f"Quantidade de Devedores"), value = count, inline=True)
                embed.add_field(name=tr.translate("Débito Total"), value = size(saldoTot,system=si), inline=True)
                embed.add_field(name=tr.translate(msg['more']), value = tr.translate(msg['footer']), inline=False)
                await ctx.send(embed=embed)
                if p2 == True:
                    embed.description= memb2
                    await ctx.send(embed=embed)
                
                if p3 == True:
                    embed.description= memb3
                    await ctx.send(embed=embed)  
                if p4 == True:
                    embed.description= memb4
                    await ctx.send(embed=embed)                       
            else:
                ctx.description= tr.translate(msg['tax']['not-tax'])
                await ctx.send(embed=embed)
        else:
            embed.description= tr.translate(msg['not-reg'])
            await ctx.send(embed=embed)
 
        
    def members_ds(self, g, player):
        dsg = bot.get_guild(g.id)
        res = False
        if bool(dsg):
            if bool(dsg.members):
                for membs in dsg.members:
                    res = search_member(membs, player)
                    if res:
                        return res
        return res

