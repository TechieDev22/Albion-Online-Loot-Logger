from .errors import HTTPException
from .inits import *

class Membro (commands.Cog):
    '''
    CLASSE DESTINADA À PLAYERS
    '''
    '''
        METODOS PRIVATIVOS
    '''
    #função obtem ranking semanal do albion
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

    '''
        COMANDOS UTEIS
    '''
    #comando consulta player no albion
    @commands.command(name = 'pi', help= "Consulta informações do player no Albion")
    async def player_info(self, ctx, nick:str, lang="english"):
        await ctx.channel.trigger_typing()
        #atribui lingua de resposta (pt ou en)
        tr = mudarLingua(lang)
        mensao = ctx.author.mention
        cor = discord.Color.green()
        if is_guild_reg(ctx.guild.id):
                g = obter_dados(Guild,ctx.guild.id)
                lang = g.lang
                tr = mudarLingua(lang)
                player = obter_dados(Members, nick)
                fot = tr.translate(msg["footer"])
                if bool(player):
                    cor = discord.Color.blue()
                    embed = discord.Embed(title= tr.translate(msg["pi"]["title"].format(player.name)), color = cor)
                    embed.description = tr.translate(f"Este jogador está registrado!")
                    if player.is_blacklist:
                        cor= discord.Color.red()
                        embed.description = tr.translate(f"Este jogador está blacklistado!")
                        embed.add_field(name = tr.translate(f"Por {player.blacklist.reason}"), value = tr.translate(f"Police: {player.blacklist.police}"))
                    embed.color = cor
                    embed.add_field(name = tr.translate(f"Discord"), value = tr.translate(f"{player.nick_discord}"))
                    embed.add_field(name=tr.translate(msg["more"]), value=fot, inline=False)
                    await ctx.send(embed=embed)
        logger.debug(f"[pi] {ctx.author} procurando player {nick}")
        #tenta obter id do player
        #await ctx.send("Wait looking in Albion's junk! It might take a while.")
        try:
            p_id = await get_player_id(nick)
        except:
            logger.error(f"[pi] {ctx.author} deu error ao consultar id")
            await ctx.send(tr.translate(f"{ctx.author.mention} Não foi possivel obter id do {nick}. Tente Novamente"))
            return
        
        logger.info(f"[pi] {ctx.author} - Jogador ID:{p_id}")
        logger.info(f"[pi] {ctx.author} procurando informações do {nick}")
        await ctx.channel.trigger_typing()
        #tenta obter informações do player
        try:
            p_info = await get_player_info(p_id)
        except:
            logger.error(f"[pi] {ctx.author} deu error ao consultar as informações")
            await ctx.send(tr.translate(f"{ctx.author.mention} Não foi possivel obter informações do jogador. Tente novamente"))
            return
        logger.debug(f"[pi] {ctx.author} procurando as covas que o {nick} fez")
        await ctx.channel.trigger_typing()
        #tenta obter as kills do player
        try:
            p_kills = await get_player_kills(p_id)
        except aiohttp.ContentTypeError as e:
            logger.warning(f"[pi] {ctx.author} deu error ao consultar as kills. {e}")
            await ctx.send(tr.translate(f"{ctx.author.nick} Não foi possivel obter cemiterio de defuntos do player. Aguarde"))
            p_kills = {}
        logger.debug(f"[pi] {ctx.author} Quantidade de dados: {len(p_info)} do {nick}")
        #se houver informações
        if len(p_info)>0:

            pvp = round(p_info['KillFame'])
            pve = round(p_info['LifetimeStatistics']['PvE']['Total'])
            coleta = round(p_info['LifetimeStatistics']['Gathering']['All']['Total'])
            crafting = round(p_info['LifetimeStatistics']['Crafting']['Total'])
            total = round(pvp+pve+coleta+crafting)
            data_att = p_info['LifetimeStatistics']['Timestamp']
            embed = discord.Embed(title= tr.translate(msg["pi"]["title"].format(p_info['Name'])), color = cor)
            embed.description = tr.translate(msg["pi"]["desc"].format(size(total,system=si)))

            embed.add_field(name= tr.translate(msg["pi"]["f-pve"]), value=size(pve,system=si))

            embed.add_field(name= tr.translate(msg["pi"]["f-pvp"]), value= size(pvp,system=si))

            embed.add_field(name= tr.translate(msg["pi"]["f-col"]), value= size(coleta,system=si))

            embed.add_field(name= tr.translate("🛠 Crafting:"), value= size(crafting,system=si))
            kills =""
            for k in p_kills:
                kills= kills + "\n" +tr.translate(msg["pi"]["kill"].format(k['Victim']['AllianceName'],k['Victim']['Name'],k['TimeStamp'][0:10]))
            if len(p_kills)>0:
                embed.add_field(name= tr.translate(msg["pi"]["kills"]),value=kills, inline=False)   
            else:
                embed.add_field(name= tr.translate(msg["pi"]["nkills"]),value="🧸", inline=False)  
            embed.set_thumbnail(url="https://raw.githubusercontent.com/LeandroLimaPRO/tesourAO/main/images/paypal_qr.png")
            fot = tr.translate(msg["footer"])
            fot2 = tr.translate(msg["pi"]["att"].format(data_att)) + fot
            embed.add_field(name=tr.translate(msg["more"]), value=fot2, inline=False)
            logger.info(f"[pi] {ctx.author} Player consultado com sucesso!\n")
            await ctx.send(embed=embed)
            await ctx.send(mensao + tr.translate(f"Agora você pode usar **{prefix}rme [nick_albion]** para registra-se à guilda"))

        else:
            logger.warning(f"[pi] {ctx.author} Player Não Encontrado!\n")

    @commands.command("rme", help= "Registra player da guilda")
    async def register_me(self, ctx, nick_name, lang = 'english'):
        tr= mudarLingua(lang)
        logger.info("Iniciando registro de player")
        return ctx.send(tr.translate("Este comando foi desabilitado. Pois há um sistema automatico para entradas e saidas de players da sua guillda"))
        if is_guild_reg(ctx.guild.id):
            guild = obter_dados(Guild,ctx.guild.id)
            tr = mudarLingua(guild.lang)
            try:
                jogador = obter_dados(Members,nick_name)
            except SQLAlchemyError as e:
                jogador = False
                logger.error(e)
            if not bool(jogador):
                id = await get_player_id(nick_name)
                if id:
                    try:
                        jogador = await get_player_info(id)
                    except aiohttp.ContentTypeError as e:
                        jogador = False
                        logger.error(e)
                    if bool(jogador):
                        name = jogador['Name']
                        guild_name = jogador['GuildName']
                        if guild.name == guild_name:
                            nmDs = ctx.author.name + "#" + ctx.author.discriminator
                            new = Members(name = name, guild_id = guild.id, ref_discord = ctx.author.id ,nick_discord = nmDs)
                            newtax = Taxa(name=name, guild_id = guild.id, saldo = 0, deposito = 0, ciclo = 0)
                            print(new)
                            try:
                                add_dados(new)
                            except SQLAlchemyError as e:
                                session.rollback()
                                logger.error(f"Não foi possivel adicionar. {e}")
                                await ctx.send(tr.translate("Não foi possivel Adicionar seus dados."))
                                return
                            add_dados(newtax)
                            await ctx.send(tr.translate(f"Bem vindo a {guild_name}! Sr(a) {new.name}"))
                            return
                else:
                    await ctx.send(tr.translate("Este jogador ainda não foi registrado no sistema. Aguarde 24 Horas, para que o albion nos atualize"))
                    return
            else:
                if not jogador.is_blacklist:
                    jogador.nick_discord = ctx.author.name + "#" + ctx.author.discriminator
                    jogador.ref_discord = ctx.author.id
                    jogador.id_guild = ctx.guild.id
                    jogador.taxa.id_guild = ctx.guild.id
                    try:
                        session.commit()
                    except SQLAlchemyError as e:
                        logger.error(e)
                        session.rollback()
                        await ctx.send(tr.translate("Não foi possivel atualizar seus dados."))
                        return
                    try:
                        await ctx.author.edit(nick = jogador.name)
                    except HTTPException as e:
                        await ctx.send(tr.translate("Não foi possivel Editar Seu Nick seus dados.Você está um cargo acima do meu."))
                        logger.error(e)
                    await ctx.send(tr.translate(f"Bem vindo a {guild.name}! Sr(a) {jogador.name}"))
                else:
                    await ctx.send(tr.translate(f"Solicitação negada. Está blaclistado motivo: {jogador.blaclist.reason}"))
        else:
            await ctx.send(tr.translate("Guild não registrada no sistema"))    
    
    
        
###