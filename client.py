import socket
import json
import tkinter as tk
from tkinter import messagebox
from tkinter import *
from tkinter import ttk 
from PIL import ImageTk
import time

client_socket = None
user_balance = 0
PATH_IMMAGINE = "/home/salvo/Scrivania/PROGETTO_UFFICIALE_1/sfondo.jpg"

# funzione per la connessione al server 
def connect_to_server(server_ip):
    global client_socket
    if client_socket is None:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, 9000))

#Funzione per inviare la richiesta al server 
def send_request(data):
    global client_socket
    if client_socket is None:
        raise RuntimeError("Socket non connessa")
    start = time.time()
    client_socket.send(json.dumps(data).encode('utf-8'))   #invia la richiesta 
    print("Richiesta inviata correttamente al server.")
    response = client_socket.recv(1024).decode('utf-8')    #recupera la risposta del server
    end = time.time()
    execution_time= end -start
    print("Tempo di esecuzione: ",execution_time," secondi")
    
    if not response:
        raise RuntimeError("Nessuna risposta dal server")
    return json.loads(response)    #ritorna risposta 

#funzione per chiudere la connessione col server
def close_connection():
    global client_socket
    if client_socket:
        client_socket.close()
        client_socket = None


def validate_digits(P):
    # Verifica che l'input sia composto solo da cifre
    return P.isdigit()

#funzione per recuperare i dati inseriti nella transazione dall'interfaccia
def validate_inputs():
    global user_balance
    importo = entry_importo.get()
    iban = entry_iban.get()
    causale = entry_causale.get()
    
    if not importo.isdigit():
        messagebox.showerror("Errore", "L'importo deve contenere solo cifre")
        return False
    
    if int(importo) > user_balance:
        messagebox.showerror("Errore","L'importo è maggiore del tuo saldo")
        return False
    
    if len(iban) != 10 or not iban.isalnum():
        messagebox.showerror("Errore", "L'IBAN deve essere composto da esattamente 10 caratteri alfanumerici")
        return False
    
    if len(causale) < 1:
        messagebox.showerror("Errore", "La causale non può essere vuota")
        return False

    # Se tutti i controlli passano
    return True


#funzione corrispondente al login
def login():
    #recupero campi username e password
    username = entry_login_username.get()
    password = entry_login_password.get()
    
    if not username or not password:
        messagebox.showerror("Errore", "Tutti i campi sono obbligatori")
        return
    
    #creazione oggetto json da inviare nella richiesta
    data = {
        "operation": "read_login",
        "username": username,
        "password": password
    }
 
    #invia la richiesta contenente l'oggetto json , se avrà successo recupera username , id e iban dalla risposta
    try:
        response = send_request(data)
        if response.get("status") == "success":
            global user_id,iban,user_name
            user_name = username
            user_id = response.get("id")
            iban = response.get("iban")
            messagebox.showinfo("Risposta", "Login avvenuto con successo")
            
            #chiusura finestra di login
            login_window.destroy()
            #apertura finestra principale
            open_main_window()

        else:
            messagebox.showerror("Errore", response.get("message"))
    except Exception as e:
        messagebox.showerror("Errore", f"Errore di comunicazione con il server: {e}")

#funzione per la creazione di un account
def create_account():
    #recupero campi inseriti
    username = entry_username.get()
    name = entry_name.get()
    password = entry_password.get()
    cognome = entry_cognome.get()
    
    if not username or not name or not password or not cognome:
        messagebox.showerror("Errore", "Tutti i campi sono obbligatori")
        return
    
    #creazione oggetto json da inviare al server
    data = {
        "operation": "create_account",
        "username": username,
        "nome": name,
        "cognome": cognome,
        "password": password
    }

    #invio della richiesta al server , con successivo recupero di alcuni campi dell'utente in caso di successo
    try:
        response = send_request(data)
        if response.get("status") == "success":
            global user_id, iban,user_name
            user_name = username
            user_id = response.get("id")
            iban = response.get("iban")
            messagebox.showinfo("Risposta", "Registrazione avvenuta con successo")
            registration_window.destroy()
            open_main_window()
        else:
            messagebox.showerror("Errore", response.get("message"))
        
    except Exception as e:
        messagebox.showerror("Errore", f"Errore di comunicazione con il server: {e}")

#funzione per ottenere il saldo dell'utente
def fetch_balance():
    #richiesta al server per ottenere il saldo
    data = {
        "operation": "read_balance",
        "user_id": user_id
    }

    try:
        response = send_request(data)
        if response.get("status") == "success":
            return response.get("balance")
        else:
            return user_balance  # In caso di errore, restituisci l'ultimo saldo noto
    except Exception as e:
        print(f"Errore di comunicazione con il server: {e}")
        return user_balance  # In caso di errore, restituisci l'ultimo saldo noto
    
#funzione per aggiornare la label del saldo nell'interfaccia
def update_balance_label():
    global user_balance
    user_balance = fetch_balance()
    balance_label_saldo.config(text=f"Saldo: {user_balance} €")
    main_window.after(10000, update_balance_label)  # Aggiorna ogni 10000 millisecondi (10 secondi)

#Interfaccia di login
def run_login():
    global entry_login_username, entry_login_password, login_window

    login_window = tk.Tk()
    login_window.title("Login")
    login_window.geometry("1199x600+100+50")
    login_window.configure(bg="#1a1a1a")

    frame_principale = tk.Frame(login_window,bg="silver")
    frame_principale.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    frame_principale.config(width=450,height=350)
    frame_principale.grid_propagate(False)

    # Configura le colonne e le righe per essere centrate
    frame_principale.grid_columnconfigure(0, weight=1)
    frame_principale.grid_columnconfigure(3, weight=1)
    frame_principale.grid_rowconfigure(0, weight=1)
    frame_principale.grid_rowconfigure(6, weight=1)
    
    tk.Label(frame_principale, text="Username",font=("Arial",16,"bold"),padx=5,pady=5,bg="silver").grid(row=1,column=1,columnspan=2,pady=5)
    entry_login_username = tk.Entry(frame_principale)
    entry_login_username.grid(row=2,column=1,columnspan=2,pady=5)

    tk.Label(frame_principale, text="Password",font=("Arial",16,"bold"),padx=5,pady=5,bg="silver").grid(row=3,column=1,columnspan=2,pady=5)
    entry_login_password = tk.Entry(frame_principale,show="*")
    entry_login_password.grid(row=4,column=1,columnspan=2,pady=5)

    tk.Button(frame_principale, text="Login", bg="#1a1a1a",fg="white",command=login).grid(row=5,column=1,columnspan=2,pady=10)
    tk.Button(frame_principale, text="Registrati",bg="#1a1a1a",fg="white", command=run_registration).grid(row=6,column=1,columnspan=2,pady=10)


    login_window.protocol("WM_DELETE_WINDOW", on_closing)
    login_window.mainloop()

#Finestra di interfaccia per la registrazione
def run_registration():

    global entry_name, entry_cognome, entry_username, entry_password, registration_window,login_window
    ###########
    login_window.destroy()
    ########

    registration_window = tk.Tk()
    registration_window.title("Registrazione")
    registration_window.geometry("1199x600+100+50")
    registration_window.configure(bg="#1a1a1a")


    frame_registration = tk.Frame(registration_window,bg="silver")
    frame_registration.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    frame_registration.config(width=450,height=350)
    frame_registration.grid_propagate(False)

    # Configura le colonne e le righe per essere centrate
    frame_registration.grid_columnconfigure(0, weight=1)
    frame_registration.grid_columnconfigure(2, weight=1)
    frame_registration.grid_rowconfigure(0, weight=1)
    frame_registration.grid_rowconfigure(10, weight=1)

    tk.Label(frame_registration, text="Nome",font=("Arial",16,"bold"),padx=5,pady=5,bg="silver").grid(row=1, column=1)
    entry_name = tk.Entry(frame_registration)
    entry_name.grid(row=2, column=1)

    tk.Label(frame_registration, text="Cognome",font=("Arial",16,"bold"),padx=5,pady=5,bg="silver").grid(row=3, column=1)
    entry_cognome = tk.Entry(frame_registration)
    entry_cognome.grid(row=4, column=1)

    tk.Label(frame_registration, text="Username",font=("Arial",16,"bold"),padx=5,pady=5,bg="silver").grid(row=5, column=1)
    entry_username = tk.Entry(frame_registration)
    entry_username.grid(row=6, column=1)

    tk.Label(frame_registration, text="Password",font=("Arial",16,"bold"),padx=5,pady=5,bg="silver").grid(row=7, column=1)
    entry_password = tk.Entry(frame_registration, show="*")
    entry_password.grid(row=8, column=1)
    
    tk.Button(frame_registration, text="Registrati",bg="#1a1a1a",fg="white",padx=20,pady=5, command=create_account).grid(row=9, column=1,pady=20)

    registration_window.protocol("WM_DELETE_WINDOW", on_closing_registration)
    registration_window.mainloop()

#finestra interfaccia per creazione movimento
def crea_movimento():
    global entry_importo, entry_iban, entry_causale,crea_movimento_window
    
    crea_movimento_window = tk.Tk()
    crea_movimento_window.title("Crea movimento")
    crea_movimento_window.geometry("400x300+100+50")

    frame_movimento = tk.Frame(crea_movimento_window)
    frame_movimento.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    frame_movimento.config(width=300,height=200)
    frame_movimento.grid_propagate(False)

    # Configura le colonne e le righe per essere centrate
    frame_movimento.grid_columnconfigure(0, weight=1)
    frame_movimento.grid_columnconfigure(3, weight=1)
    frame_movimento.grid_rowconfigure(0, weight=1)
    frame_movimento.grid_rowconfigure(6, weight=1)

    tk.Label(frame_movimento, text="Importo").grid(row=1, column=1)
    entry_importo = tk.Entry(frame_movimento, validate="key")
    entry_importo['validatecommand'] = (frame_movimento.register(validate_digits), '%P')
    entry_importo.grid(row=2, column=1)

    tk.Label(frame_movimento, text="Iban destinatario").grid(row=3, column=1)
    entry_iban = tk.Entry(frame_movimento)
    entry_iban.grid(row=4, column=1)

    tk.Label(frame_movimento, text="Causale").grid(row=5, column=1)
    entry_causale = tk.Entry(frame_movimento)
    entry_causale.grid(row=6, column=1)

    tk.Button(frame_movimento, text="Invia", command=lambda: submit_movimento(frame_movimento)).grid(row=7, column=1)

#funzione per creare il movimento
def submit_movimento(window):
    global crea_movimento_window
    if validate_inputs():
        # Recupero dati 
        importo = int(entry_importo.get())
        iban = entry_iban.get()
        causale = entry_causale.get()

        #creazione oggetto json da inviare al server
        data = {
            "operation": "create_movimento",
            "importo" : importo,
            "iban" : iban,
            "causale": causale,
            "user_id" : user_id
        }

        try:
            response = send_request(data)
            if response.get("status") == "success":
                messagebox.showinfo("Risposta", "Movimento creato con successo")
                crea_movimento_window.destroy()
                
            else:
                messagebox.showerror("Errore", response.get("message"))
                crea_movimento_window.destroy()
        
        except Exception as e:
            messagebox.showerror("Errore", f"Errore di comunicazione con il server: {e}")
    
    else:
        # Se c'è un errore, la funzione termina qui e non esegue il resto del codice
        crea_movimento_window.destroy()
        return

#Interfaccia con lista dei movimenti in entrata
def open_movements_entrate(movements):
    global movements_entrate_window
    movements_entrate_window = tk.Toplevel()
    movements_entrate_window.title("Movimenti")

    # Creazione del widget Treeview
    tree = ttk.Treeview(movements_entrate_window, columns=("Amount", "Description"), show="headings")
    tree.heading("Amount", text="Importo")
    tree.heading("Description", text="Causale")
    tree.pack(expand=True, fill="both")

    # Aggiunge i movimenti al Treeview
    for movement in movements:
        tree.insert("", "end", values=movement)

    movements_entrate_window.protocol("WM_DELETE_WINDOW", on_closing_movements_entrate)
    movements_entrate_window.mainloop()

#Interfaccia con lista dei movimenti in uscita
def open_movements_uscite(movements):
    global movements_uscite_window
    movements_uscite_window = tk.Toplevel()
    movements_uscite_window.title("Movimenti")

    # Creazione del widget Treeview
    tree = ttk.Treeview(movements_uscite_window, columns=("Amount", "Description"), show="headings")
    tree.heading("Amount", text="Importo")
    tree.heading("Description", text="Causale")
    tree.pack(expand=True, fill="both")

    # Aggiunge i movimenti al Treeview
    for movement in movements:
        tree.insert("", "end", values=movement)

    movements_uscite_window.protocol("WM_DELETE_WINDOW", on_closing_movements_uscite)
    movements_uscite_window.mainloop()

    
#funzione per recuperare le entrate dell'utente tramite una richiesta al server
def read_entrate():
    data = {
        "operation":"read_entrate",
        "user_id":user_id
        }
    
    try:
            response = send_request(data)
            if response.get("status") == "success":
                lista_entrate = response.get("lista")
                open_movements_entrate(lista_entrate)
                
            else:
                messagebox.showerror("Errore")
                

    except Exception as e:
            messagebox.showerror("Errore", f"Errore di comunicazione con il server: {e}")
    
#funzione per recuperare le uscite dell'utente tramite una richiesta al server
def read_uscite():
    data = {
        "operation":"read_uscite",
        "user_id":user_id
        }
    
    try:
            response = send_request(data)
            if response.get("status") == "success":
                lista_uscite = response.get("lista")
                open_movements_uscite(lista_uscite)
                
            else:
                messagebox.showerror("Errore")
                

    except Exception as e:
            messagebox.showerror("Errore", f"Errore di comunicazione con il server: {e}")

    
#interfaccia per l'eliminazione dell'account
def open_delete_account():
    global entry_delete_username,entry_delete_password,delete_window

    delete_window = tk.Tk()
    delete_window.title("Eliminazione account")

    tk.Label(delete_window, text="Username").grid(row=0, column=0)
    entry_delete_username = tk.Entry(delete_window)
    entry_delete_username.grid(row=0, column=1)

    tk.Label(delete_window, text="Password").grid(row=1, column=0)
    entry_delete_password = tk.Entry(delete_window, show="*")
    entry_delete_password.grid(row=1, column=1)

    tk.Button(delete_window, text="Elimina", command=delete_account).grid(row=2, column=0, columnspan=2)

#funzione per l'eliminazione dell'account
def delete_account():
    #l'account può essere eliminato solo inserendo le sue corrette credenziali
    delete_username = entry_delete_username.get()
    delete_password = entry_delete_password.get()
    data = {
        "operation":"delete_account",
        "user_id":user_id,
        "del_user":delete_username,
        "del_password":delete_password   
    }

    try:
            response = send_request(data)
            if response.get("status") == "success":
                on_closing_main_window()
                delete_window.destroy()
                
                
            else:
                messagebox.showerror("Errore")
                

    except Exception as e:
            messagebox.showerror("Errore", f"Errore di comunicazione con il server: {e}")

    

#Interfaccia pagina principale
def open_main_window():
    global main_window, balance_label_saldo,balance_label_iban
    main_window = tk.Tk()
    #################  Dettagli interfaccia grafica
    main_window.title("Home Page")
    main_window.geometry("1199x600+100+50")
    
    main_window.bg = ImageTk.PhotoImage(file=PATH_IMMAGINE)
    main_window.bg_image = Label(main_window,image=main_window.bg).place(x=0,y=0,relwidth=1,relheight=1)

    frame_principale2 = tk.Frame(main_window,bg="white")
    frame_principale2.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    frame_principale2.config(width=500,height=400)
    frame_principale2.grid_propagate(False)

    # Configura le colonne e le righe per essere centrate
    frame_principale2.grid_columnconfigure(0, weight=1)
    frame_principale2.grid_columnconfigure(3, weight=1)
    frame_principale2.grid_rowconfigure(0, weight=1)
    frame_principale2.grid_rowconfigure(6, weight=1)
    
    tk.Label(frame_principale2, text=f"Benvenuto, {user_name}",font=("Arial",16,"bold"),padx=5,pady=5,bg="white").grid(row=1, column=1, columnspan=2,pady=10)
    balance_label_saldo = tk.Label(frame_principale2, text=f"Saldo: {user_balance} €",font=("Arial",16,"bold"),padx=5,pady=5,bg="white")
    balance_label_saldo.grid(row=2, column=1, columnspan=2,pady=10)
    balance_label_iban = tk.Label(frame_principale2, text=f"Il tuo IBAN: {iban} ",font=("Arial",16,"bold"),padx=5,pady=5,bg="white")
    balance_label_iban.grid(row=3, column=1, columnspan=2,pady=10)

    
    tk.Button(main_window, text="Elimina account", bg="#1a1a1a",fg="white",command=open_delete_account).grid(row=0,column = 2, sticky='e',padx=10,pady=10)
    tk.Button(frame_principale2, text="Crea Movimento", bg="#1a1a1a",fg="white", command=crea_movimento).grid(row=4, column=1, columnspan=2,pady=10)
    tk.Button(frame_principale2, text="Visualizza movimenti in entrata", bg="#1a1a1a",fg="white", command=read_entrate).grid(row=5, column=1, columnspan=2,pady=10)
    tk.Button(frame_principale2, text="Visualizza movimenti in uscita", bg="#1a1a1a",fg="white", command=read_uscite).grid(row=6, column=1, columnspan=2,pady=10)

    # Avvia l'aggiornamento del saldo
    update_balance_label()
    ################## Fine dettagli interfaccia grafica

    main_window.protocol("WM_DELETE_WINDOW", on_closing_main_window)
    main_window.mainloop()


#funzioni per la chiusura delle rispettive finestre
def on_closing():
    if login_window:
        login_window.destroy()

def on_closing_registration():
    if registration_window:
        registration_window.destroy()

def on_closing_main_window():
    if main_window:
        main_window.destroy()
    if crea_movimento_window:
        crea_movimento_window.destroy()
    on_closing_movements_entrate()
    on_closing_movements_uscite()

def on_closing_movements_entrate():
    if movements_entrate_window:
        movements_entrate_window.destroy()


def on_closing_movements_uscite():
    if movements_uscite_window:
        movements_uscite_window.destroy()


if __name__ == "__main__":
    #connessione al server
    connect_to_server("127.0.0.1")
    #run dell'interfaccia
    run_login()

    #se tutte le finestre principali sono chiuse , l'utente chiude l'applicazione e quindi la connessione al server viene chiusa.
    if not (login_window and registration_window and main_window):
        close_connection()


