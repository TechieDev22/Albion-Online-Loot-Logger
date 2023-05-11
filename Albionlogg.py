import json
import asyncio
import logging
import aiohttp
from datetime import datetime as dt
logger = logging.getLogger(__name__)

def _url(endpoint):
            logger.debug(f"Setou url: {'https://gameinfo.albiononline.com/api/gameinfo' + endpoint}")
            return 'https://gameinfo.albiononline.com/api/gameinfo' + endpoint
        
def url_market(item,qualidade, city ='Caerleon'):
    return f"https://www.albion-online-data.com/api/v2/stats/prices/{item}?locations={city}&qualities={qualidade}"

def url_render(item):
    return f"https://render.albiononline.com/v1/item/{item}.png"

async def request (url, params=None):
        st = dt.now()
        if params is not None:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    j_ = await resp.json()
                    logger.info(f"{dt.now() - st}s Resposta(Params): \n {len(j_)}")
                    return j_
        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    j_ = await resp.json()
                    logger.info(f"{dt.now() - st}s Resposta(Params): \n {len(j_)}")
                    return j_
async def get_statistics_guild( guild_id:str,range= 0, types=0, subtype=0, region=0, limit = 0):
        '''	
        range:	week | month ::
        limit:	1 - 9999 ::
        offset:	1 - 9999 ::
        type:	PvE | Gatherering ::
        subtype:	All | Fiber | Hide | Ore | Rock | Wood ::
        region:	Total | Royal | Outlands | Hellgate ::
        guildId:	Restrict to a guild ::
        allianceId:	Restrict to an alliance ::
        '''
        if range==0:
            r = "week"
        else:
            r = "month"

        if types ==1:
                tr = "Gathering"
        else:
                tr = "PvE"
            #subtype
        if subtype == 1:
                st = "All"
        elif subtype == 2:
                st ="Fiber"
        elif subtype == 3:
                st = "Hide"
        elif subtype == 4:
                st = "Ore"
        elif subtype == 5:
                st = "Rock" 
        elif subtype == 6:    
                st="Wood"
        else:
            st = "All"
        #region
        if region ==1:
            rg = "Total"
        elif region ==2:
                rg = "Royal"
        elif region ==3: 
                rg = "Outlands" 
        elif region ==4:
                rg= "Hellgate"
        else:
                rg= "Total"

        params = {}
        params['guildId'] = guild_id
        params['range'] = r
        params['type'] = tr
        if limit >10:
            li = limit
            params['limit'] = li
        if tr != "PvE":
            params['subtype']= st
        else:
            params['region']= rg
        logger.info(f"Parametros: {params}")
        return await request(_url("/players/statistics"), params=params)

async def get_player_id( player_name):
            player = await search(player_name)
            return player['players'][0]['Id']

async def get_player_info( player_id):
            return await request(_url('/players/{player_id}'.format(
                player_id=player_id)))

async def get_player_kills(player_id):
            return await request(_url('/players/{player_id}/kills'.format(player_id=player_id)))

async def get_player_topkills( player_id, offset=0, limit=11,
                                _range='week'):
            params = {}
            params['offset'] = offset
            params['limit'] = limit
            if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                params['range'] = _range
            return await request(_url('/players/{player_id}/topkills'.format(
                player_id=player_id)), params=params)

async def get_player_solokills( player_id, offset=0, limit=11,
                                _range='week'):
            params = {}
            params['offset'] = offset
            params['limit'] = limit
            if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                params['range'] = _range
            return await request(_url('/players/{player_id}/solokills'.format(
                player_id=player_id)), params=params)

async def get_player_death( player_id):
            return await request(_url('/players/{player_id}/deaths'.format(
                player_id=player_id)))

async def get_guild_id( guild_name):
            guild = await search(guild_name)
            if len(guild['guilds']) > 0:
                print(guild)
                return guild['guilds'][0]['Id']
            return None
       
async def get_guild_info( guild_id):
            return await request(_url(
                '/guilds/{guild_id}'.format(guild_id=guild_id)))

async def get_guild_data( guild_id):
            return await request(_url('/guilds/{guild_id}/data'.format(
                guild_id=guild_id)))

async def get_guild_top_kills( guild_id, offset=0, limit=10,_range='week'):
            params = {}
            params['offset'] = offset
            params['limit'] = limit
            if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                params['range'] = _range

            return await request(
                _url('/guilds/{guild_id}/top'.format(guild_id=guild_id)),
                params=params)

async def get_guild_stats( guild_id):
            return await request(_url('/guilds/{guild_id}/stats'.format(
                guild_id=guild_id)))

async def get_guild_members( guild_id):
            return await request(_url('/guilds/{guild_id}/members'.format(
                guild_id=guild_id)))

async def get_guild_fued( guild_id, rival_guild_id):
            return await request(
                _url('/guilds/{guild_id}/fued/{rival_guild_id}'.format(
                    guild_id=guild_id, rival_guild_id=rival_guild_id)))

async def get_server_status( server='live'):
            if server == 'live' or server == 'staging':
                try:
                    return await request(
                        'http://{server}.albiononline.com/status.txt'.format(
                            server=server))
                # Adding a hack to catch invalid json returned from the API
                except json.decoder.JSONDecodeError:
                    response = await request(
                        'http://{server}.albiononline.com/status.txt'.format(
                            server=server))
                    return json.loads(response.text[3:])

async def get_event( event_id):
            return await request(_url('/events/{event_id}'.format(
                event_id=event_id)))

async def get_recent_events( limit=50, offset=0):
            params = {}
            params['limit'] = limit
            params['offset'] = offset

            return await request(_url('/events'), params=params)

async def get_events_between( start_event, end_event):
            return await request(
                _url('/events/{start_event}/history/{end_event}'.format(
                    start_event=start_event, end_event=end_event)))

async def get_guildmatches( match_id, offset=0, limit=6):
            params = {}
            params['offset'] = offset
            params['limit'] = limit

            return await request(
                _url('/guildmatches/{guild_id}'.format(
                    guild_id=match_id)), params=params)

async def get_guildmatches_top(self):
            return await request(_url('/guildmatches/top'))

async def get_guildmatches_next( offset=0, limit=11):
            params = {}
            params['offset'] = offset
            params['limit'] = limit

            return await request(_url('/guildmatches/next'),
                                params=params)

async def get_guildmatches_past( offset=0, limit=51):
            params = {}
            params['offset'] = offset
            params['limit'] = limit

            return await request(_url('/guildmatches/past'),
                                params=params)

async def get_guildmatches_history( guild_id, rival_guild_id):
            return await request(_url(
                '/guildmatches/history/{guild_id}/{rival_guild_id}'.format(
                    guild_id=guild_id, rival_guild_id=rival_guild_id)))

async def search( query):
            params = {}
            params['q'] = query
            return await request(_url('/search'), params=params)

async def top_player_kill_fame( offset=0, limit=11, _range='week'):
            params = {}
            params['offset'] = offset
            params['limit'] = limit
            if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                params['range'] = _range

            return await request(_url('/playerfame'), params=params)

async def top_guild_kill_fame( offset=0, limit=11, _range='week'):
                params = {}
                params['offset'] = offset
                params['limit'] = limit
                if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                    params['range'] = _range

                return await request(_url('/guildfame'), params=params)

async def top_kill_fame_ratio( offset=0, limit=11, _range='week'):
            params = {}
            params['offset'] = offset
            params['limit'] = limit
            if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                params['range'] = _range

            return await request(_url('/fameratio'), params=params)

async def top_guilds_by_attack( offset=0, limit=11, _range='week'):
                params = {}
                params['offset'] = offset
                params['limit'] = limit
                if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                    params['range'] = _range

                return await request(_url('/topguildsbyattack'),
                                    params=params)

async def top_guilds_by_defense( offset=0, limit=11, _range='week'):
                params = {}
                params['offset'] = offset
                params['limit'] = limit
                if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                    params['range'] = _range

                return await request(_url('/topguildsbydefense'),
                                    params=params)

async def player_weapon_ranking( offset=0, limit=11, _range='week'):
                params = {}
                params['offset'] = offset
                params['limit'] = limit
                if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                    params['range'] = _range

                return await request(_url('/playerweaponfame'),
                                    params=params)

async def get_battles( offset=0, limit=51, _range=None,
                        sort='recent'):
            params = {}
            params['offset'] = offset
            params['limit'] = limit
            if _range and _range in ['week', 'lastWeek', 'month', 'lastMonth']:
                params['range'] = _range
            if sort and sort in ['recent', 'topfame']:
                params['sort'] = sort

            return await request(_url('/battles'),
                                params=params)

async def get_weapon_categories():
    return await request(_url('/items/_weaponCategories'))

async def get_weapon(item):
    return await request(_url(f'/items/{item}/data'))

async def get_prince_item(item,qualidade,city='Caerleon'):
    return await request(url_market(item,qualidade,city))