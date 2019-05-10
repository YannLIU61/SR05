import tkinter as Tkinter
import sys
import threading
import time

class STDIOMonitorThread(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self._running = True
        self._callback = callback
    

    def run(self):
        # sys.stderr.write("Thread Booted\n")
        while self._running:
            for line in sys.stdin:
                #sys.stderr.write("[{}] Message received: {}\n".format(time.time(), line))
                self._callback(line.replace("\n", "") if line[-1] == '\n' else line)
    

    def stop(self):
        self._running = False  
        self.join()    


class AutoSendThread(threading.Thread):
    def __init__(self, timeout, callback):
        threading.Thread.__init__(self)
        self._running = True
        self._callback = callback
        self._timeout = timeout

    def run(self):
        # sys.stderr.write("Thread Booted\n")
        while self._running:
            self._callback()
            time.sleep(self._timeout / 1000)
    
    def stop(self):
        self._running = False
        

"""
light.tk UI
#### DEFINITION DES ZONES DE L'INTERFACE #############################

#### zone pour l'emission
labelframe .out -pady 2 -padx 2 -text "Message � envoyer"
entry .out.msg -width 24 -textvariable var_message_envoye
pack .out.msg -side left -fill y -pady 2

#### zone pour la reception
labelframe .in -pady 2 -padx 2 -text "Message re�u"
label .in.msg -text $var_message_recu -width 32
pack .in.msg -side left -fill y -pady 2

#### zone des boutons
frame .bt
button .bt.quit -text "Quitter" \
		-activebackground red \
		-foreground red \
		-font $var_fonte_bouton \
		-width 10 \
		-command { exit }

button .bt.snd -text "Envoyer" \
		-activebackground SeaGreen4 \
		-foreground SeaGreen4 \
		-font $var_fonte_bouton \
		-width 10 \
		-command { proc_emission_message }

button .bt.auto -text "Mode auto" \
		-activebackground SeaGreen4 \
		-foreground SeaGreen4 \
		-font $var_fonte_bouton \
		-width 8 \
		-command proc_aut_btdebut

pack  .bt.quit .bt.snd .bt.auto -side right


### zone du timer
labelframe .aut -pady 2 -padx 2 -text "Emission p�riodique \[�tat : d�sactiv�\]"

label .aut.lfrq -text "fr�quence (ms) :"
spinbox .aut.sfrq -values "500 800 1000 2000 3000 5000 10000" -width 6 \
		-textvariable var_aut_frq

pack .aut.lfrq .aut.sfrq -side left -padx 2

#### affichage des zones horizontales
pack .bt .in .out .aut -fill both -expand yes -side top -pady 5
"""
class AsyncIOWindow:
    def __init__(self):
        # Init thread
        self._thread = STDIOMonitorThread(self.on_message)
        self._send_thread = None

        # Init variables
        self._send_content = "-"
        self._auto_send = False
        self._auto_send_timeout = 500

        # Init window
        self._window = Tkinter.Tk(className="[SR05] - Async IO")

        # Out Label Frame and its components
        self._out_label_frame = Tkinter.LabelFrame(self._window, pady=2, padx=2, text="Message à envoyer")

        self._out_msg_entry = Tkinter.Entry(self._out_label_frame, width=36)
        self._out_msg_entry.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)


        # In Label Frame and its components
        self._in_label_frame = Tkinter.LabelFrame(self._window, pady=2, padx=2, text="Message reçu")

        self._in_msg_label = Tkinter.Label(self._in_label_frame, width=36, text="-")
        self._in_msg_label.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)


        # Button zone
        self._button_zone = Tkinter.Frame(self._window)
        
        self._btn_quit = Tkinter.Button(self._button_zone, text="Quitter", activebackground="red", \
            foreground="red", width=10, command=self.on_quit)
        self._btn_send = Tkinter.Button(self._button_zone, text="Envoyer", activebackground="SeaGreen4", \
            foreground="SeaGreen4", width=10, command=self.send_message)
        self._btn_auto = Tkinter.Button(self._button_zone, text="Mode auto", activebackground="SeaGreen4", \
            foreground="SeaGreen4", width=8, command=self.switch_auto_send)
        self._btn_debug = Tkinter.Button(self._button_zone, text="Débogage", activebackground="Blue", \
            foreground="Yellow", width=8, command=self.switch_debug)

        self._btn_quit.pack(side=Tkinter.RIGHT)
        self._btn_send.pack(side=Tkinter.RIGHT)
        self._btn_debug.pack(side=Tkinter.RIGHT)
        self._btn_auto.pack(side=Tkinter.RIGHT)


        # Timer zone
        self._auto_zone = Tkinter.LabelFrame(self._window, pady=2, padx=2, text="Emission périodique [état : désactivé]")

        self._auto_frequence = Tkinter.Label(self._auto_zone, text="fréquence (ms) :")
        self._auto_spinbox = Tkinter.Spinbox(self._auto_zone, values=(500, 800, 1000, 2000, 3000, 5000, 10000), width=6)

        self._auto_frequence.pack(side=Tkinter.LEFT, padx=2)
        self._auto_spinbox.pack(side=Tkinter.LEFT, padx=2)

        self._debug_zone = Tkinter.LabelFrame(self._window, text="Zone de débogage")
        self._text_debug = Tkinter.Text(self._debug_zone, height=10, width=48)

        self._text_debug.pack(side=Tkinter.LEFT, expand=Tkinter.YES)

        self._debug_zone.visibility = False

        # Pack zones
        self._button_zone.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)
        self._in_label_frame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)
        self._out_label_frame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)
        self._auto_zone.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)

        # Boot
        self._thread.start()


    def send_message(self):
        self._send_content = self._out_msg_entry.get()

        send_time = time.time()
        self._text_debug.insert(Tkinter.END, "[{}] Message sent: {}\n".format(send_time, self._send_content))
        self._text_debug.see(Tkinter.END)
        sys.stderr.write("[{}] Message sent: {}\n".format(send_time, self._send_content))

        sys.stdout.write(self._send_content + "\n")
        sys.stdout.flush()
    

    def on_quit(self):
        self._window.quit()


    def on_message(self, content):
        receive_time = time.time()
        self._text_debug.insert(Tkinter.END, "[{}] Message received: {}\n".format(receive_time, content))
        self._text_debug.see(Tkinter.END)
        sys.stderr.write("[{}] Message received: {}\n".format(receive_time, content))
        
        self._in_msg_label["text"] = content


    def mainloop(self):
        if self._window and hasattr(self._window, "mainloop"):
            self._window.mainloop()
            self._thread.stop() # Request thread to quit

    def switch_auto_send(self):
        if self._auto_send:
            self._send_thread.stop()
            self._send_thread = None
            self._auto_zone["text"] = "Emission périodique [état : désactivé]"
            self._btn_auto["text"] = "Mode auto"
            self._auto_send = False
        else:
            self._auto_send_timeout = int(self._auto_spinbox.get())
            self._send_thread = AutoSendThread(self._auto_send_timeout, self.send_message)
            self._send_thread.start()
            self._auto_send = True
            self._auto_zone["text"] = "Emission périodique [état : activé]"
            self._btn_auto["text"] = "Fin auto"

    def switch_debug(self):
        if self._debug_zone.visibility:
            self._debug_zone.pack_forget()
        else:
            self._debug_zone.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)
        
        self._debug_zone.visibility = not self._debug_zone.visibility

    def __del__(self):
        # Do clean works
        pass
        #del self._thread

