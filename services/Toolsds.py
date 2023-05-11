from .inits import *
from os import remove

class TaxaD(commands.Cog):
    #função retorna fama coletada na semana
    async def fama_coleta_semanal(self, idguild:str ,player:str, lang="english"):

        logger.info("Iniciando coleta de estatistica")
        #stats_ = await get_statistics_guild(idguild, range= "week", types="Gathering", subtype="All")

        try:
            stats_ = await get_statistics_guild(guild_id=idguild, range=0, types=1, limit = 100)
        except :
            logger.error("Não foi possivel  obter estatisticas")      
            return 0

        if len(stats_)>2:
            logger.debug(stats_)
            logger.info("Encontrou dados!")
            c = 0
            logger.info(f'Quantidade de players: {len(stats_)}')
            for p in stats_:
                c +=1
                pname = p["Player"]["Name"]
                pfame = p["Fame"]
                #print(f'{pname} | contagem {c}')
                if pname  == player:
                    logger.info(f"COLETA! {pname} : {pfame}")
                    return pfame
                elif len(stats_) == c:
                    logger.info(f"Player não consta no Top ranking")
                    return 1
        else:
            logger.warning("Não há dados no banco do albion")
            return 0
    #função calcula doação de coleta baseada na fama    
    async def doacao_coleta(self, fame_semanal=0, t_doar=5, taxa=0):
        '''
        calcula a taxa de doação de coleta
        fama_semanal : int
        t_doar: int
        taxa: int
        '''
        val = 0
        if t_doar == 5:
            val = round(((fame_semanal/100)* taxa)/22)
            return val
        elif  t_doar == 6:
            val = round(((fame_semanal/100)* taxa)/33)
            return val
        elif  t_doar == 7:
            val = round(((fame_semanal/100)* taxa)/44)
            return val
        elif  t_doar == 8:
            val = round(((fame_semanal/100)* taxa)/55)
            return val
        else:
            return val
    #comando muda taxa de doação
    @commands.command(name = 'mt', help= "Change guild Gathering rate")
    async def mudar_taxa(self,ctx,tax_colector=None,tax_silver = None, min_fame=None,lang="english"):
        tr = mudarLingua(lang)
        if is_guild_reg(ctx.guild.id):
            guildb = obter_dados(Guild, ctx.guild.id)
            embed= discord.Embed(title=tr.translate(msg["taxa"]["title"]), color=discord.Color.dark_gold())
            #embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
            tr = mudarLingua(guildb.lang)
            if has_roles(ctx):
                    embed= discord.Embed(title=tr.translate(msg["taxa"]["title"].format(guildb.name)), color=discord.Color.dark_gold())
                    taxa_coletor =int(0 if tax_colector is None else tax_colector)
                    taxa_silver = int(0 if tax_silver is None else tax_silver)
                    min_fame = int(0 if min_fame is None else min_fame)
                    if tax_colector !=guildb.taxa and taxa_coletor >=  0:
                        guildb.taxa= taxa_coletor
                        guildb.taxac_s = True
                        session.flush()

                    if tax_silver != guildb.taxa_p or taxa_silver >=0:
                        guildb.taxa_p = taxa_silver
                        guildb.taxap_s = True
                        session.flush()

                    if min_fame != guildb.fame_taxa or min_fame>=0:
                        guildb.fame_taxa = min_fame
                        guildb.taxap_s = True
                        session.flush()
                    session.commit()
                    embed.add_field(name = tr.translate("Taxa de Prata"), value = size(taxa_silver,system=si), inline = True)
                    embed.add_field(name = tr.translate("Taxa de Coleta"), value = str(size(taxa_coletor,system=si)) + " %", inline=True)
                    embed.add_field(name = tr.translate("Fama minima"), value = size(min_fame,system=si), inline=False)
                    embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
                    logger.info(f"[mudartaxa] {ctx.guild.name} Taxa de coleta foi alterada para {tax_colector}% prata para: {taxa_silver} fama minima: {min_fame}")
                    await ctx.send(embed=embed)

            else:
                await ctx.send(tr.translate(msg["not-role"]))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))

    #comando envia dados de contribuição de taxa fixa
    @commands.command(name = 'cts', help= "Sends contribution deposit data")
    async def contribuicoes_taxas_semanais(self,ctx):
        await ctx.channel.trigger_typing()
        lang = "english"
        tr = mudarLingua(lang)
        #variaveis locais inicializadas
        total = 0 #variavel de prata total arrecadado
        #totaldp = 0
        #totalsal = 0
        id_ = str(ctx.guild.id) #id do discord
        file_ = f'./balances/cts{id_}.txt' #local  onde será salvo o arquivo de texto com nome
        #taxa_file =  #[path] do banco de pagamento de taxa
        if has_roles(ctx):
            #print("role passou!")
            #verifica se a guild foi registrada
            if is_guild_reg(id_):
                #print("guild registrado")
                g = obter_dados(Guild, id_) #inicializa banco de guilds
                tr = mudarLingua(g.lang)
                tx = session.query(Taxa).filter_by(guild_id = id_).all() #inicializa banco de taxas
                lang = g.lang #obtem lingua apartir do banco
                taxa_p = g.taxa_p
                # import requests 
                attachment_url = ctx.message.attachments[0].url
                # file_request = requests.get(attachment_url)
                resp = requests.get(f"{attachment_url}")
                ## obtem respose converte e decotifica para string utf8
                resp = str(resp.content, encoding="utf-8")
                #formata arquivo de balanço
                out = balance_form(resp)
                #verifica se o arquivo existe se exstir apaga
                await ctx.channel.trigger_typing()
                if os.path.exists(file_):
                    remove(file_)
                #cria arquivo para salvar
                f = open(file_, "a+",encoding='utf-8')
                #grava o content (string) do response no arquivo
                f.write(out)
                f.write("\n")
                f.flush()#libera
                f.close()#fecha arquivo
                await ctx.channel.trigger_typing()
                await asyncio.sleep(1) #aguarda alguns segundos
                #tenta ler arquivo de texto criado
                await ctx.channel.trigger_typing()
                try:
                    data= read_banco_txt(file_)
                except:
                    await ctx.send(tr.translate("Error ao ler arquivo de balanço"))
                    return
                #INTERFACE - cria embed do discord
                embed= discord.Embed(title=tr.translate(msg["tax"]["title"]), color=discord.Color.dark_gold())
                desc =""
                total = 0
                await ctx.channel.trigger_typing()
                for p in data:
                    pl = p["Jogador"]
                    qt = float(p["Quantidade"])
                    total += qt
                    embed.add_field(name=pl, value=size(qt, system=si), inline=False)
                    for j in tx:
                        if j.name == pl:
                            dep = qt
                            sal = j.saldo + dep
                            j.deposito = dep
                            session.flush()
                            j.saldo = sal
                            session.flush()
                session.commit()
                await ctx.channel.trigger_typing()
                desc += tr.translate(msg["tax"]["info-dep"].format(size(total,system=si)))
                embed.description = desc
                embed.add_field(name=tr.translate(msg["more"]),value=tr.translate(msg["footer"]))
                await ctx.send(embed=embed)
            else:
                await ctx.send(tr.translate(msg["not-reg"]))
        else:
            await ctx.send(tr.translate(msg["not-role"]))
            
    @commands.command(name = 'adp', help= "increment value from tax deposit")
    async def depositarPrataManualmente(self, ctx, nickname, deposito = 0,  lang = "english"):
        tr = mudarLingua(lang)
        msg = init_json(cfg['msg_path'])
        id_ = ctx.guild.id #id do discord
        embed= discord.Embed(title=tr.translate("Ajuste de contribuição"), color=discord.Color.dark_gold())
        #taxa_file = cfg["taxa_fixa"] [path] do banco de pagamento de taxa
        if is_guild_reg(id_):
            if has_roles(ctx):
                g = obter_dados(Guild, id_) #inicializa banco de guilds
                #verifica se a guild foi registrado
                tr = mudarLingua(g.lang) #obtem lingua apartir do banco
                mb = is_player_exist_on_guild(ctx.guild.id,nickname)
                if mb:
                    tx = obter_dados(Taxa,nickname)
                    embed= discord.Embed(title=f"Ajuste de contribuição - {nickname}", color=discord.Color.dark_gold())
                    embed.description = tr.translate(f"Autor: {ctx.author.mention}")
                
                    if tx:
                        #sal = p.saldo
                        #tx.deposito = deposito
                        #   ~[ ,k ,k ,k ,k ,k ,k ,k ,ksession.flush()
                        tx.saldo += deposito
                        session.flush()
                    session.commit()
                    if tx.saldo >= 0:
                        embed.add_field(name=tr.translate("Saldo"), value= size(tx.saldo, system=si))
                    else:
                        embed.add_field(name=tr.translate("Saldo"), value= -size(abs(tx.saldo), system=si))
                    embed.add_field(name=tr.translate("Deposito"), value= size(tx.deposito, system=si))
                else:
                    embed.description = tr.translate("Este player não pertence a sua guilda!")
                embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
                await ctx.send(embed=embed)
            else:
                embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
                await ctx.send(tr.translate(msg["not-role"]))
        else:
            embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
            embed.description = tr.translate(msg["not-reg"])
            await ctx.send(embed=embed)  
  
            
    @commands.command(name = 'at', help= "Starts new contribution period (adds + fee to be paid)")
    async def atualiza_periodo(self, ctx, lang = "english"):
        tr = mudarLingua(lang)
        msg = init_json(cfg['msg_path'])
        id_ = ctx.guild.id #id do discord
        embed= discord.Embed(title=tr.translate(msg["taxa"]["title"]), color=discord.Color.dark_gold())
        embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
        #taxa_file = cfg["taxa_fixa"] [path] do banco de pagamento de taxa
        if is_guild_reg(id_):
            if has_roles(ctx):
            #verifica se a guild foi registrada
            
                g = obter_dados(Guild, id_) #inicializa banco de guilds
                tr = mudarLingua(g.lang) #obtem lingua apartir do banco
                tx =session.query(Members).join(Taxa).filter(Members.guild_id == g.id, Members.isention == False).all() #inicializa banco de taxas LEANDRO
                embed= discord.Embed(title=tr.translate(msg["taxa"]["title"]), color=discord.Color.dark_gold())
                taxa_p = g.taxa_p
                for p in  tx:
                    ptx = obter_dados(Taxa,p.name)
                    if ptx:
                        if ptx.ciclo >=0 :
                            sal = ptx.saldo
                            ptx.ciclo += 1
                            session.flush()
                            ptx.saldo = sal - taxa_p
                            session.flush()
                        else:
                            continue
                    else:
                        newT = Taxa(name = p.name, saldo = -taxa_p, ciclo = 1, guild_id = g.id)
                        add_dados(newT)
                session.commit()
                embed.description = tr.translate(f"{ctx.author.mention} A **new cycle** has started! Debit of **{size(taxa_p,system=si)}** has been added to taxpayers")
                embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(tr.translate(msg["not-role"]))
        else:
            embed.description = tr.translate(msg["not-reg"])
            await ctx.send(embed=embed)
    #comando retorna a taxa atual da guilda
    @commands.command(name="tax",help= "Return tax")
    async def taxa(self,ctx, lang = "english"):
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(lang)
        embed= discord.Embed(title=tr.translate(msg["taxa"]["title"].format(ctx.guild.id)), color=discord.Color.dark_gold())
        embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
        await ctx.channel.trigger_typing()
        datag = obter_dados(Guild,ctx.guild.id)
        if datag:
            tr = mudarLingua(datag.lang)
            embed= discord.Embed(title=tr.translate(msg["taxa"]["title"].format(datag.name)), color=discord.Color.green())
            
            taxa_coleta = datag.taxa
            taxa_prata = datag.taxa_p
            fama_minima = datag.fame_taxa
            embed.add_field(name=tr.translate("Taxa de Prata"), value=size(int(0 if taxa_prata is None else taxa_prata),system=si), inline=True)
            embed.add_field(name=tr.translate("Taxa de Coleta"), value=size(int(0 if taxa_coleta is None else taxa_coleta),system=si), inline=True)
            embed.add_field(name=tr.translate("Fama minima para cobrança"),value=size(int(0 if fama_minima is None else fama_minima),system=si),inline=False)
        else:
            embed.description = tr.translate(msg["not-reg"])
        embed.add_field(name=tr.translate(msg["more"]), value = tr.translate(msg["footer"]), inline=False)
        await ctx.send(embed = embed)

    #comando para retornar a taxa de contribuição
    @commands.command(name = 'c', help= "How much should you donate collection. Your weekly fame and the level you want to collect are needed.") #calculadora de taxa de coleta
    async def calcular_taxa_coleta(self,ctx, nick_player: str, tier, lang="english"):
        msg = init_json(cfg['msg_path'])
        tr = mudarLingua(lang)
        await ctx.channel.trigger_typing()
        idg=str(ctx.guild.id)
        tier = int("".join(filter(str.isdigit, tier)))
        if is_guild_reg(idg):
            datag = obter_dados(Guild,idg)
            guild_name = datag.name
            guild_id = datag.id
            tr = mudarLingua(datag.lang)
            if is_tax_grather_system(idg):
                taxa = datag.taxa
                
                await ctx.channel.trigger_typing()
                try:
                    fama_coleta = await self.fama_coleta_semanal(guild_id,nick_player)
                except:
                    fama_coleta = 0
                    logger.error("Não foi Possivel Obter fama de coleta")
                a_doar = await self.doacao_coleta(fama_coleta,tier,taxa)

                #logger.info(f"{type(taxa)} || {type(fama_coleta)}:{fama_coleta} ")
                if fama_coleta < 1000:
                    info_player= f"{fama_coleta}"
                else:
                    info_player = f"{size(fama_coleta,si)}"
                        #print(f"{fama_coleta}::{a_doar} :::{taxa}")
                await ctx.channel.trigger_typing()
                await ctx.send(ctx.author.mention)
                embeds = discord.Embed(title=tr.translate(f'{nick_player} deve contribuir com'), color =  Color.darker_grey())     
                if int(a_doar) == 0:
                    cor = Color.blurple()
                    resposta = tr.translate(f"Tente novamente. Lembre-se não aceitamos Tiers abaixo do 5")
                else:
                        cor = Color.dark_blue()
                        embeds.add_field(name=tr.translate("Quantidade de recursos"), value=a_doar)
                        embeds.add_field(name= tr.translate("Tier dos recursos"), value=f'T{tier}')
                        #resposta = f"**{nick_player}** você deve pagar **{a_doar}** unidades de recursos no **T{tier}**."
                embeds.add_field(name= tr.translate("Fama Semanal"), value = info_player)
                embeds.add_field(name=tr.translate("Observações"), value= tr.translate(f"\n\nLembre-se de colocar os recursos no bau de doação! \nNão esqueça de contatar um oficial."), inline=False)
                    
                embeds.set_thumbnail(url="https://raw.githubusercontent.com/LeandroLimaPRO/tesourAO/main/images/paypal_qr.png")
                    
                fot2 = tr.translate(f"Taxa de {taxa}% contribubição da guilda.\n") + fot
                embeds.add_field(name= tr.translate("Mais"), value=fot2, inline=False)
                logger.info(tr.translate(f"[c]{a_doar} de T{tier}. FAMA TOTAL {fama_coleta}"))
                await ctx.send(embed=embeds)
            else:
                await ctx.send(tr.translate(msg["not-tax"]))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))
        
    #comando para adicionar isenção no player ok
    @commands.command("ai", help="Add player insention of tax")
    async def add_player_i(self,ctx, nick_player, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            lang = guild.lang

            tr = mudarLingua(lang)
            if not tr:
                await ctx.send(tr)
                return

            if has_roles(ctx):
                add_isention(ctx.guild.id,nick_player)
                await ctx.send(tr.translate(f"{nick_player} added in insention!"))
                remove_tax(ctx.guild.id,nick_player)
                await ctx.send(tr.translate(f"{nick_player} is removed from tax system!"))
            else:
                await ctx.send(tr.translate("Not available role!"))
        else:
            await ctx.send(tr.translate(msg["english"]["not-reg"])) 
    
    #remove player da isenção ok 
    @commands.command("ri", help="remove player insention of tax system")
    async def re_player_i(self,ctx, nick_player, lang = "english"):
        tr = mudarLingua(lang)
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            if guild.lang:
                lang = guild.lang
            tr = mudarLingua(lang)
            if has_roles(ctx):
                remove_isention(ctx.guild.id,nick_player)
                await ctx.send(tr.translate(f"{nick_player} is removed insention of tax system"))
            else:
                await ctx.send(tr.translate("Not available role!"))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))
    #remove player da isenção ok
    @commands.command("rtax", help="remove player tax system")
    async def re_player_t(self,ctx, nick_player, lang = "english"):
        tr = mudarLingua(lang)
        if not tr:
            await ctx.send(tr)
            return
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            if guild.lang:
                lang = guild.lang
                tr = mudarLingua(lang)
                if not tr:
                    await ctx.send(tr)
                    return
            if has_roles(ctx):
                gd = session.query(Members).get(ctx.guild.id)
                new_tax = session.query(Taxa).filter_by(name = nick_player,guild_id = ctx.guild.id).first()
                new_tax.deposito = 0
                session.flush()
                new_tax.saldo = gd.taxa_p
                session.flush()
                new_tax.ciclo = 1
                session.commit()
                await ctx.send(tr.translate(f"{nick_player} is removed from tax"))
            else:
                await ctx.send(tr.translate("Not available role!"))
        else:
            await ctx.send(tr.translate(msg["not-reg"]))                
    
    #checa taxa ok
    @commands.command("ti", help="check tax of player")
    async def ck_player_t(self,ctx, nick_player, lang="english"):
        tr = mudarLingua(lang)
        dsid = str(ctx.guild.id)
        if is_guild_reg(dsid):
            dg = obter_dados(Guild,dsid)
            lang = dg.lang
            tr = mudarLingua(lang)
            if is_tax_silver_system(dsid):
                if is_tax_exist(nick_player):
                    p = session.query(Taxa).get(nick_player)
                    m = session.query(Members).get(nick_player)
                    deposito = p.deposito
                    saldo = p.saldo
                    ciclo = p.ciclo
                    if not m.isention:
                        if saldo >=0:
                            embed = discord.Embed(title= tr.translate(msg["tax"]["title"]),color=discord.Color.green())
                            embed.add_field(name=tr.translate(msg["tax"]["saldo"]), value=size(saldo,system=si))
                        else:
                            embed = discord.Embed(title= tr.translate(msg["tax"]["ck-title"]),color=discord.Color.red())
                            embed.add_field(name=tr.translate(msg["tax"]["saldo"]), value=f'-{size(-saldo,system=si)}')
                        embed.description= nick_player
                        #embed.add_field(name=tr.translate(msg["tax"]["depo"], value=size(deposito,system=si))
                        embed.add_field(name=tr.translate(msg["tax"]["cicle"]), value=int(ciclo))
                    else:
                        embed = discord.Embed(title= tr.translate(msg["tax"]["title"]),color=discord.Color.blue())
                        embed.description= tr.translate(msg["tax"]["isention"])
                    
                    embed.add_field(name=tr.translate(msg["more"]), value= tr.translate(msg["footer"]), inline=False)

                    await ctx.send(embed=embed)
                else:
                    await ctx.send(tr.translate(msg["tax"]["not-pl"]))
            else:
                await ctx.send(tr.translate(msg["tax"]["not-tax"]))
        else:
            await ctx.send(tr.translate(msg["tax"]["no-reg"]))
            
    @commands.command("te", help="Enable/Desable tax system")    
    async def sistema_taxa(self,ctx, lang= "english"):
            tr = mudarLingua(lang)
            msg = init_json(cfg['msg_path'])
            embed = discord.Embed(title= tr.translate(msg["tax"]["title"].format('')),color=discord.Color.red())
            if is_guild_reg(ctx.guild.id):
                guild = obter_dados(Guild,ctx.guild.id)
                embed = discord.Embed(title= tr.translate(msg["tax"]["title"].format(guild.name)),color=discord.Color.gold())
                tr = mudarLingua(guild.lang)
                if has_roles(ctx):
                    guild.taxap_s = not guild.taxap_s
                    guild.taxac_s = not guild.taxac_s
                    session.commit()
                    embed.description = tr.translate(f"Sistema de Prata: {tr.translate('Ativado') if guild.taxap_s ==True else tr.translate('Desativado')} \n Sistema Coleta: {tr.translate('Ativado') if guild.taxac_s ==True else tr.translate('Desativado')} ")
                    embed.add_field(name=tr.translate(msg['more']),value=tr.translate(msg['footer']))
                    await ctx.send(embed=embed)
                else:
                    embed.description = tr.translate(msg['not-role'])
                    embed.add_field(name=tr.translate(msg['more']),value=tr.translate(msg['footer']))
                    await ctx.send(embed=embed)
            else:
                embed.description = tr.translate(msg['not-reg'])
                embed.add_field(name=tr.translate(msg['more']),value=tr.translate(msg['footer']))
                await ctx.send(embed=embed)