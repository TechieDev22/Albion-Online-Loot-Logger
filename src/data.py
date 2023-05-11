import os
import json
import logging
from sqlalchemy import create_engine, exists
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref
from sqlalchemy import Column, Integer, String, Float,Boolean ,ForeignKey, BigInteger
from dotenv import load_dotenv
from sqlalchemy.sql.expression import except_

from services.data_json import *
logger = logging.getLogger(__name__)

#carrega arquivo .env
load_dotenv()
# atribui constantes 
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
STRINGSQL = os.getenv('STRING_SQL')
cfg = init_json("./data/config.json") #[path] configurações do bot
msg = init_json("./data/msg.json")


engine = create_engine(STRINGSQL, echo=False)
Base = declarative_base()
Session = sessionmaker(engine)
session = Session()

class Guild(Base):
    __tablename__ = 'guild'

    id = Column(BigInteger, primary_key=True, comment="id da guild")
    id_ao = Column(String, comment="Id da guild no albion")
    id_ali = Column(String, comment="Id da Aliança")
    name = Column(String, comment="Name da guild")
    lang = Column(String, comment="Language")
    top = Column(Boolean, comment="Sistema Top da guild")
    taxap_s = Column(Boolean, comment="Sistema de taxa de prata")
    taxac_s = Column(Boolean, comment= "Sistema de taxa de coleta")
    canal_top = Column(BigInteger, comment="DISCORD canal top")
    canal_blacklist = Column(BigInteger, comment= "DISCORD canal blacklist")
    canal_taxa = Column(BigInteger, comment="DISCORD canal de taxa")
    canal_info = Column(BigInteger, comment="DISCORD canal info")
    taxa_p =  Column(Integer, comment="Taxa de prata")
    taxa =  Column(Integer, comment="taxa")
    fame_taxa = Column(Integer, comment="taxa de c")
    members = relationship("Members", back_populates='guild',cascade="all, delete, delete-orphan", passive_deletes=True)
    cargos = relationship("Cargos", back_populates='guild', cascade="all, delete, delete-orphan", passive_deletes=True)
    blacklist = relationship("Blacklist", back_populates="guild", cascade="all, delete, delete-orphan", uselist=False)
    #field_data = relationship('members', backref="guild", uselist=False)
    ##relação

    def __repr__(self):
       return f"<Guild(id='{self.id}' |  name='{self.name}' | lang='{self.lang}')>"

class Members(Base):
    __tablename__ = 'members'
    name = Column(String, primary_key=True)
    id_ao = Column(String)
    fame = Column(BigInteger)
    guild_id = Column(BigInteger, ForeignKey(Guild.id, ondelete="CASCADE"))
    is_cargo = Column(Boolean, default=False, comment="Define oficial")
    is_blacklist = Column(Boolean, default=False, comment="Bane Player")
    isention = Column(Boolean, default=False, comment="Isencao de taxa")
    ref_discord = Column(BigInteger, comment="Id ou nome do discord player")
    nick_discord = Column(String)
    #relacões
    taxa = relationship("Taxa", back_populates="members", cascade="all, delete, delete-orphan", uselist=False)
    guild = relationship("Guild", back_populates="members")
    def __repr__(self):
        return f"<Members(name='{self.name}'\n| taxa='{self.taxa} | blacklist='{self.is_blacklist})>"

class Taxa(Base):
    __tablename__ = 'taxa'
    name = Column(String, ForeignKey("members.name", ondelete="CASCADE"), primary_key=True)
    deposito = Column(Float)
    saldo = Column(Float)
    ciclo = Column(Float)
    guild_id = Column(BigInteger)
    members = relationship("Members", back_populates="taxa")
    def __repr__(self):
        return "<Taxa(deposito='%s'| saldo='%s' | ciclo='%s')>" % (self.deposito,  self.saldo, self.ciclo)

class Blacklist(Base):
    __tablename__ = 'blacklist'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    reason = Column(String)
    police = Column(String)
    guild_id = Column(BigInteger, ForeignKey("guild.id", ondelete="CASCADE"))
    guild= relationship("Guild",back_populates="blacklist")
    def __repr__(self):
        return "<Blacklist(name='%s' | motivo='%s'| police='%s')>" % (self.name, self.reason, self.police)
class Cargos(Base):
    __tablename__ = 'cargos'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    guild_id = Column(BigInteger, ForeignKey("guild.id", ondelete="CASCADE"))
    
    guild = relationship("Guild",back_populates="cargos")
    def __repr__(self):
        return f"<Cargos({self.id}| {self.name})>"

#verifica se a guild foi registrada
def is_guild_reg (id):
    try:
        return bool(session.query(exists().where(Guild.id == id)).scalar()) #retorna bool se existir
    except SQLAlchemyError as e:
        logger.error(e)
        return False
#verifica se a guilda tem sistema taxa de prata ativa
def is_tax_silver_system(id):
    try:
        
        return bool(session.query(Guild).filter(Guild.id == id, Guild.taxap_s == True).first()) #retorna bool se existir
    except SQLAlchemyError as e:
        logger.error(e)
        return False
#verifica se a guilda tem sistema de taxa de coleta ativa
def is_tax_grather_system(id):
    try:
        return bool(session.query(Guild).filter(Guild.id == id, Guild.taxac_s == True).first())
    except SQLAlchemyError as e:
        logger.error(e)
        return False
#verifica se o player está na tabela membros
def is_player_exist_on_guild(guild_id,nick_player):
    try:  
        return bool(session.query(Members).filter(Members.guild_id == guild_id, Members.name == nick_player).first()) #retornretorna bool se existir
    except SQLAlchemyError as e:
        logger.error(e) 
#verifica se o player está na tabela membros
def is_player_exist(nick_player):
    try:  
        return bool(session.query(Members).filter(Members.name == nick_player).first()) #retornretorna bool se existir
    except SQLAlchemyError as e:
        logger.error(e) 
#verifica se o player tem contribuição
def is_tax_exist(nick_player):  
    try:
        return bool(session.query(exists().where(Taxa.name == nick_player)).scalar()) #retorna bool se existir
    except SQLAlchemyError as e:
        logger.error(e)
        return False
#verifica se o player está blacklistado
def is_blacklisted_from_guild(guild_id, nick_player):
        re = False  
        try:
            re = session.query(Blacklist).filter(Blacklist.name == nick_player , Blacklist.guild_id == guild_id).first()
            '''re = session.query(exists().where(
            Members.name == nick_player
            and Members.guild_id == guild_id
            and Members.is_blacklist == True)).first() '''#retorna bool se existir
        except SQLAlchemyError as e:
            re = None
            logger.error(e)
        return re
#verifica se existe o cargo
def is_cargo(guild_id, name):
    try:
        #print(session.query(Cargos).filter(Cargos.name == name and Cargos.guild_id ==guild_id).first())
        return bool(session.query(Cargos).filter(Cargos.name == name , Cargos.guild_id ==guild_id).first())
    except SQLAlchemyError as e:
        logger.error(e)
        return False

#lista todos os cargos da guilda
def cargos_list(guild_id):
    try:
        return session.query(Cargos).filter(Cargos.guild_id == guild_id).all()
    except SQLAlchemyError as e:
        logger.error(e)
        return False

#salvar dados no banco de dados (objetos)
def add_dados(mapper):
    session.add(mapper)
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(e)
        return False
#pegar objeto do banco de dados GUILD, MEMBRO, TAXA, CARGO, BLACKLIST
def obter_dados(mapper, pk):
    try:
        return session.query(mapper).get(pk)
    except SQLAlchemyError as e:
        logger.error(e)
        return False

def deletar_dados(mapper,pk):
    deletar = session.query(mapper).get(pk)
    session.delete(deletar)
    try:
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(e)
        return False


### admin
#remove player da taxa.json
def remove_tax(id,nick):
    if is_guild_reg(id):
        deletar_dados(Taxa,nick)
        return True
    else:
        
        logging.warning(f"GUILD <{id}> Não registrada. Não foi possivel remover: {nick}")
        return False
#checa player isention
def check_isention(id,nick):
    if is_guild_reg(id):
        try:
            return bool(session.query(Members).filter(Members.name == nick , Members.isention ==True).first())
        except SQLAlchemyError as e:
            logger.error(e)
            return False
    else:
        logging.warning(f"GUILD <{id}> Não registrada")
        return False

#remove player da isention
def remove_isention(id,nick):
    if is_guild_reg(id):
        if check_isention(id,nick):
            try:
               result = obter_dados(Members,nick)
               result.isention = False
               session.commit()
            except :
                return False
        else:
           logging.warning(f"Sem isenção")
           return False 
    else:
        logging.warning(f"GUILD <{id}> Não registrada")
        return False    
#adiciona player na isenção
def add_isention(id,nick):
    if is_guild_reg(id):
        if check_isention(id,nick):
            try:
               result = obter_dados(Taxa,nick)
               result.isention = True
               session.commit()
               return True
            except :
                return False
        else:
           logging.warning(f"Sem isenção")
           return False 
    else:
        logging.warning(f"GUILD <{id}> Não registrada")
        return False    

def generate_all_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
def update_db():
    Base.metadata.update(engine)