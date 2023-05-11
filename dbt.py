
from src.inits import *
from src.Blacklistds import Blacklist_member
from src.Adminds import Admin
from src.Toolsds import TaxaD
from src.Membrods import Membro
from discord.client import Client
from discord.member import Member
#Base.metadata.drop_all(engine)
#Base.metadata.create_all(engine)
@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} conectou ao discord!\n')
    logger.info(f'\n')
    logger.warning(f'{len(bot.guilds)}')
    for guild in list(bot.guilds):
        logger.debug(guild)
    atividade = random.choice(atividades)
    activity = discord.Game(name=atividade, type=3)
    
    await bot.change_presence(status=discord.Status.online, activity=activity)
          
        #for p in  print(member) g.members:
        #    pint(p.name)r

        
bot.add_cog(TaxaD(bot))
bot.add_cog(Membro(bot))
bot.add_cog(Admin(bot))
bot.add_cog(Blacklist_member(bot))
bot.run(TOKEN)
