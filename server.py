import socket
from threading import Thread
import threading
import json
import hashlib
import random,string

PATH_JSON = '/home/salvo/Scrivania/PROGETTO_UFFICIALE_1/account.json'

lock = threading.Lock()
#Funzione per generare l'iban
def generate_iban(length=8, prefix="IT"):   
    caratteri = string.ascii_uppercase + string.digits
    random_string = ''.join(random.choice(caratteri) for _ in range(length))
    return prefix + random_string
#Funzione per hashare la password inserita dall'utente
def hash_password(password):
    # Converte la password in un byte object
    password_bytes = password.encode('utf-8')

    # Genera l'hash della password utilizzando SHA-1
    hashed_password = hashlib.sha1(password_bytes).hexdigest()

    return hashed_password

#CRUD OPERATION : READ 
def load_file():
     with open(PATH_JSON, 'r') as file:
    #Preleva file JSON
        dati = json.load(file)
        return dati 
     
#CRUD OPERATION : UPDATE
def update_file(new_file):
     with open(PATH_JSON, 'w') as file:
    #modifica file json
        json.dump(new_file,file,indent=4)

#CRUD OPERATION: DELETE
def delete_account(id):

    file_json = load_file()
    file_json.pop(id)
    update_file(file_json)
    return {"status":"success"}

     

#funzione eseguita dal thread (per ogni client)
def handle_client(client_sock):
    
    while True:   
        try:
            #richiesta del client
            request = client_sock.recv(1024).decode('utf-8')
            print("richiesta:"+request)
            ##########
            if not request:
                break
            ######
            request_data = json.loads(request)
            response = handle_request(request_data)   #esegue la richiesta tramite handle_request e torna la risposta
            client_sock.send(json.dumps(response).encode('utf-8')) #invia la risposta al client

        except Exception as e:
            print(f"Errore: {e}")
        finally:
            print("operazione eseguita")
            
#funzione per verificare le credenziali durante il login
def verify_credential(file_json,username,password):
    
    password_hash = hash_password(password)
    for account_id,account_info in file_json.items():
        #se username e password sono presenti e uguali allora l'accesso avrà successo
        if account_info.get("username") == username and account_info.get("hash_password") == password_hash:
            return {"status": "success", "message": "Login avvenuto con successo","id":account_id,"iban":account_info["iban"]}
        
    return {"status": "error", "message": "Username o password non corretti"}  

#funzione per aggiornare il saldo dell'utente
def update_balance(file_json,user_id):
    
    movimenti_in_entrata = file_json[user_id].get("movimenti_in_entrata", {})
    movimenti_in_uscita = file_json[user_id].get("movimenti_in_uscita", {})
    #recupera i movimenti in entrata e uscita di un utente per poi effettuare il calcolo del saldo
    somma_entrate = sum(movimento[0] for movimento in movimenti_in_entrata.values())
    somma_uscite = sum(movimento[0] for movimento in movimenti_in_uscita.values())
    
    saldo = somma_entrate - somma_uscite
    file_json[user_id]["saldo"] = saldo
    update_file(file_json)
    return saldo

#funzione per recuperare i movimenti in entrata di un utente
def read_entrate(file_json,user_id):
    
    lista_entrate = file_json[user_id].get("movimenti_in_entrata")
    lista = []
    for values in lista_entrate.values():
        lista.append(values)
    return lista

#funzione per recuperare i movimenti in uscita di un utente
def read_uscite(file_json,user_id):
    
    lista_uscite = file_json[user_id].get("movimenti_in_uscita")
    lista = []
    for values in lista_uscite.values():
        lista.append(values)
    return lista


#### funzione per ritornare il saldo dell'utente
def read_balance(file_json,user_id):

    saldo_corrente = update_balance(file_json,user_id)
    return {"status": "success","balance":saldo_corrente}


#funzione per creare una transazione
def create_movimento(file_json,user_id,iban,importo,causale):
        #il mittente per eseguire una transazione inserisce l'iban del destinatario 
        id_destinatario = 0 
        for id_dest, user_data in file_json.items():
            if user_data["iban"] == iban:
                id_destinatario = id_dest  # Restituisce l'ID dell'utente destinatario con l'IBAN corrispondente

        if id_destinatario == 0 : 
            return {"status": "error", "message": "Iban non corretto"}
        
        # Trova l'utente con l' id specificato
        user_data_m = file_json[user_id]
        user_data_d = file_json[id_destinatario]
        
        # Recupera la lista dei movimenti in uscita del mittente e in entrata del destinatario
        movimenti_in_uscita = user_data_m.get("movimenti_in_uscita", {})
        
        movimenti_in_entrata = user_data_d.get("movimenti_in_entrata", {})

        # Trova l'ultimo ID movimento in uscita del mittente utilizzato 
        if movimenti_in_uscita:
            last_id_m = max(map(int, movimenti_in_uscita.keys()))
        else:
            last_id_m = 0

        # Trova l'ultimo ID movimento in entrata del destinatario utilizzato 
        if movimenti_in_entrata:
            last_id_d = max(map(int, movimenti_in_entrata.keys()))
        else:
            last_id_d = 0
        
        # Nuovo ID movimento uscite mittente
        new_id_m = str(last_id_m + 1)

        #Nuovo ID movimento entrata destinatario
        new_id_d = str(last_id_d + 1)

        # Crea il nuovo movimento in uscita
        nuovo_movimento_m = [importo, causale]

        #Crea il nuovo movimento in entrata
        nuovo_movimento_d = [importo, causale]

        # Aggiungi il nuovo movimento alla lista dei movimenti in uscita del mittente
        movimenti_in_uscita[new_id_m] = nuovo_movimento_m
        user_data_m["movimenti_in_uscita"] = movimenti_in_uscita

        # Aggiungi il nuovo movimento alla lista dei movimenti in entrata del destinatario
        movimenti_in_entrata[new_id_d] = nuovo_movimento_d
        user_data_d["movimenti_in_entrata"] = movimenti_in_entrata
        user_data_d["saldo"] = int(user_data_d.get("saldo")) + importo

        file_json[user_id] = user_data_m
        file_json[id_destinatario] = user_data_d
        ####aggiornata lista movimenti in uscita del mittente e in entrata del destinatario

        update_file(file_json)
        return{"status" : "success", "message" : "Transazione effettuata"}




#funzione per gestire tutti i tipi di richiesta
def handle_request(data):
    #recupero dei campi inviati nella richiesta
    operation = data.get("operation")
    account_username = data.get("username")
    account_nome = data.get("nome")
    account_cognome = data.get("cognome")
    account_password = data.get("password")
    account_id = data.get("user_id")
    iban_destinatario = data.get("iban")
    causale_movimento = data.get("causale")
    importo_movimento = data.get("importo")
    delete_username = data.get("del_user")
    delete_password = data.get("del_password")
    
    #acqusizione del lock per bloccare l'accesso alla sezione critica (cioè al file json)
    lock.acquire()
    #read del file json
    file_json = load_file()
    
    #Create account
    if operation == "create_account":
            #se l'username è già utilizzato ritorna account già esistente
            for account_id, account_info in file_json.items():
                if account_info.get('username') == account_username:
                    lock.release() 
                    return {"status": "error", "message": "Account già esistente"}
            
            #recupera l'ultimo id utente inserito nel file json
            id_massimo = max(map(int, file_json.keys()))   ##map per mappare le chiavi in una lista come interi
            new_id = str(id_massimo + 1)
            password = hash_password(account_password)
            iban = generate_iban()

            #account da inserire nel file json
            new_account = {
                 new_id : {
                      "nome": account_nome,
                      "cognome" : account_cognome,
                      "username" : account_username,
                      "hash_password": password , 
                      "iban": iban,
                      "saldo" : 0,
                      "movimenti_in_entrata":dict(),
                      "movimenti_in_uscita":dict()
                 }
                 
            }
            file_json.update(new_account)
            #update del file_json
            update_file(file_json)
            lock.release()
            #rilascio del lock 
            return {"status": "success", 
                    "message": "Account creato",
                    "id":new_id,
                    "iban":iban}
    
    #controllo login
    if operation == "read_login":
        #controllo credenziali
        result = verify_credential(file_json,account_username,account_password)
        lock.release()
        #rilascio del lock
        return result
    

    #lettura del saldo utente
    if operation == "read_balance":
        balance = read_balance(file_json,account_id)
        lock.release()
        #rilascio del lock
        return balance
    
    if operation == "create_movimento":
       message = create_movimento(file_json,account_id,iban_destinatario,importo_movimento,causale_movimento)
       lock.release()
       #rilascio del lock
       return message
    
    if operation =="read_entrate":
       result_entrate = read_entrate(file_json,account_id)
       lock.release()
       #rilascio del lock
       return {"status":"success","lista":result_entrate}
    
    if operation =="read_uscite":
       result_uscite = read_uscite(file_json,account_id)
       lock.release()
       #rilascio del lock
       return {"status":"success","lista":result_uscite}
    
    #eliminazione account 
    if operation=="delete_account":
        verifica = verify_credential(file_json,delete_username,delete_password)
        if verifica.get("status") == "success" :
            result_delete = delete_account(account_id)
            lock.release()
            return result_delete
        else:
            lock.release()
            return verifica
            
    #se l'operazione non è tra quelle possibili
    lock.release()
    return {"status": "error", "message": "Operazione non riconosciuta"}
        


def run():
    # creazione socket del server , binding e server in ascolto
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1",9000))
    server_socket.listen(10)   #10 equivale alla dimensione massima della coda di connessioni in attesa
    print("Server in ascolto sulla porta 9000\n")
    
    #lista in cui inserire i thread
    lista_client = [] 
    
    try:
        
        while True: 
            #accetta la connessione dal client e recuperare i dati
            client_sock,addr = server_socket.accept()
            print(f"Connessione accettata da {addr}")
            #creazione e start del thread ad ogni connessione in entrata accettata
            client_thread = Thread(target=handle_client,args=(client_sock,))
            client_thread.start()
            
            lista_client.append(client_thread)

        
    finally:
        
        print(lista_client)
        #join dei thread
        for thread in lista_client:
            thread.join()

        server_socket.close()
        #chiusura del server


        print("server chiuso")


if __name__=="__main__":
    run()


    






    



