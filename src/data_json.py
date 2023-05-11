import pandas as pd
import json

def init_json(dirname):
  with open(dirname, encoding="utf-8") as cfg_file:
    cfg = json.load(cfg_file)
    return cfg

def save_json(data,dirname):
  with open(dirname, 'w') as f:
    json.dump(data,f,indent=4)
    
def update_json(new_data, filename='data.json'):
    with open(filename,'r+', encoding="utf-8") as file:
      #try: 
      # First we load existing data into a dict.
      #print(new_data)
      file_data = json.load(file)
        # Join new_dat3a with file_data
      file_data.update(new_data)
      #print(file_data)
        # Sets file's current position at offset.
      file.seek(0)
          # convert back to json.
      json.dump(file_data, file, indent = 4)


def rguild(id,id_albion, name_guild:str, lang="pt-br", taxa=10):
  da = {
    id: {
      "name": name_guild,
      "id": id_albion,
      "lang": lang,
      "taxa": taxa,
      "not-tax":[]
    }
  }
  bufstr = da
  #bufstr = json.dumps(da, indent = 4)
  #print(bufstr)
  return bufstr
        #return True
      #except:
       # print("error!")
       # return False
def read_banco_txt (file_in, tipo = 0):
    d = pd.read_csv(file_in,encoding="utf-8")
    if tipo == 0:
        motivo = "Depósito"
    else:
        motivo = "Saque"
    #print(d.columns)
    #print(d.Data)
    #d = d.drop(columns='Data')
    d = d.loc[d.Motivo == motivo]
    d = d.drop(columns=d.columns[0])
    d = d.drop(columns=d.columns[1])
    d = d.to_dict('records')
    return d

def balance_form (resp):
  out = resp
  out = out.replace('"Date"','"Data"')
  out = out.replace('"Player"','"Jogador"')
  out = out.replace('"Reason"','"Motivo"')
  out = out.replace('"Amount"','"Quantidade"')
  out = out.replace('"Deposit"','"Depósito"')
  out = out.replace('"Withdrawal"','"Saque"')
  out = out.replace('"	"',",")
  out = out.replace('"',"")
  return out

cols_name=["timestamp","player", "conte", "qtde", "fr"] #NOME DAS COLUNAS
last_len = 0
# consulta novos loots e retorna o mais recente
def dataconsulta(arquivo):
    global last_len
    dataloot = pd.read_csv(arquivo, sep=";", header=None, names=cols_name)
    now_len = len(dataloot)
    if now_len != last_len:  
        #print ("Contagem Agora: " + str(now_len) +  " Antes: " + str(last_len)) 
        nowloot =  dataloot.loc[last_len:now_len,:]
        #print(nowloot)
        last_len = now_len
        return nowloot