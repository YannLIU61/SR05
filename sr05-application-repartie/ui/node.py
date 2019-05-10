import tkinter as Tkinter
import sys
import threading
import time
import copy

sys.path.insert(0, "../")

from util.clock import Clock
import json


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


class QueueThread(threading.Thread):
    SEND = 0
    RECEIVE = 1
    TRANS = 2
    UPDATE = 3

    def __init__(self, send_callback, receive_callback, update_callback):
        threading.Thread.__init__(self)
        self._send_callback = send_callback
        self._receive_callback = receive_callback
        self._update_callback = update_callback
        self._queue = list()
        self._running = True

    def add_action(self, action, message):
        if self._running:
            self._queue.append((action, message))  # Thread safe

    def run(self):
        while self._running:
            while len(self._queue) > 0:
                element = self._queue.pop(0)
                if element[0] == self.SEND or element[0] == self.TRANS:
                    self._send_callback(element[1], element[0] == self.TRANS)
                elif element[0] == self.RECEIVE:
                    self._receive_callback(element[1])
                elif element[0] == self.UPDATE:
                    self._update_callback(element[1])
            time.sleep(0.1) # Wait for next element
        self._queue.clear()

    def stop(self):
        self._running = False
        self.join()


class NodeWindow:
    def __init__(self, ident, encoder, decoder, auto_mode=False):
        # Init thread
        self._thread = STDIOMonitorThread(self.on_message)
        self._send_thread = None
        self._queue_thread = QueueThread(self.send_async, self.receive_async, self.on_update_value)

        # Init variables
        self._ident = ident
        self.x = 0.0
        self._join_net = False
        self._send_content = str(self.x)
        self._msg_counter = 0

        # Init variable de snapshot
        self._save_status = False
        self._count_snapshot = 0
        self._saving = False

        # Init vector clock
        self._clock_vector = Clock()
        self._clock_vector.clocks.update({self._ident: 0})

        self._saved_clock = Clock()
        self._saved_clock.clocks.update({self._ident: 0})

        self._msg_received = dict()

        # Init encoder, decoder
        self._encoder = encoder
        self._decoder = decoder

        # self._mes_id_recu = 0
        # self._mes_sender = 0
        # self._mes_id = 0

        # Init window
        self._window = Tkinter.Tk(className="[SR05] - System reparti")

        # Out Label Frame and its components
        self._out_label_frame = Tkinter.LabelFrame(self._window, pady=2, padx=2, text="Mise à jour de X")


        self._out_msg_entry = Tkinter.Entry(self._out_label_frame, width=32)
        self._out_update_btn = Tkinter.Button(self._out_label_frame, text="Mise à jour", width=10, command=self.update_value)

        self._out_msg_entry.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._out_update_btn.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)

        # In Label Frame and its components
        self._in_label_frame = Tkinter.LabelFrame(self._window, pady=2, padx=2, text="Valeur de X au courant")

        self._in_msg_label = Tkinter.Label(self._in_label_frame, width=40, text=str(self.x))
        self._in_msg_label.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)

        # Button zone
        self._button_zone = Tkinter.LabelFrame(self._window, text="Noeud: " + "".join(ident))
        self._button_zone_1 = Tkinter.Frame(self._button_zone)
        self._button_zone_2 = Tkinter.Frame(self._button_zone)

        self._btn_quit = Tkinter.Button(self._button_zone_2, text="Quitter", activebackground="red", \
            foreground="red", width=20, command=self.on_quit)
        self._btn_force_send = Tkinter.Button(self._button_zone_1, text="Envoyer", activebackground="SeaGreen4", \
            foreground="SeaGreen4", width=12, command=self.send_message, state="disable")
        self._btn_start = Tkinter.Button(self._button_zone_1, text="Commencer", activebackground="SeaGreen4", \
            foreground="SeaGreen4", width=12, command=self.toggle_send)
        self._btn_debug = Tkinter.Button(self._button_zone_1, text="Débogage", activebackground="Blue", \
            foreground="Yellow", width=12, command=self.switch_debug)

        self._button_zone_1.pack(side=Tkinter.TOP)
        self._button_zone_2.pack(side=Tkinter.TOP)

        # save button
        self._btn_save = Tkinter.Button(self._button_zone_2, text="Sauvegarder", \
            width=20, command=self.save_snapshot)
        self._btn_quit.pack(side=Tkinter.RIGHT)
        self._btn_force_send.pack(side=Tkinter.RIGHT)
        self._btn_save.pack(side=Tkinter.RIGHT)
        self._btn_debug.pack(side=Tkinter.RIGHT)
        self._btn_start.pack(side=Tkinter.RIGHT)

        self._debug_zone = Tkinter.LabelFrame(self._window, text="Zone de débogage")

        self._debug_zone_display = Tkinter.Frame(self._debug_zone)
        self._debug_zone_encode = Tkinter.Frame(self._debug_zone)
        self._debug_zone_encode_2 = Tkinter.Frame(self._debug_zone)

        self._text_debug = Tkinter.Text(self._debug_zone_display, height=10, width=40)
        self._label_debug_protocol = Tkinter.Label(self._debug_zone_encode, width=8, text="Protocole:")
        self._entry_debug_protocol = Tkinter.Entry(self._debug_zone_encode, width=4)
        self._label_debug_content = Tkinter.Label(self._debug_zone_encode, width=8, text="Content:")
        self._entry_debug_content = Tkinter.Entry(self._debug_zone_encode, width=8)

        self._label_debug_receiver = Tkinter.Label(self._debug_zone_encode_2, width=10, text="Recepteurs:")
        self._entry_debug_receiver = Tkinter.Entry(self._debug_zone_encode_2, width=18)
        self._btn_debug_reset = Tkinter.Button(self._debug_zone_encode, text="Reset", activebackground="Red", foreground="red", width=6, command=self.reset_debug)

        self._btn_debug_send = Tkinter.Button(self._debug_zone_encode_2, text="Envoyer", activebackground="SeaGreen4", width=6, command=self.pack_message)

        self._debug_zone_display.pack(side=Tkinter.TOP)
        self._debug_zone_encode.pack(side=Tkinter.TOP)
        self._debug_zone_encode_2.pack(side=Tkinter.TOP)
        self._debug_zone.visibility = False

        self._text_debug.pack(side=Tkinter.LEFT, expand=Tkinter.YES)
        self._label_debug_protocol.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._entry_debug_protocol.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._label_debug_content.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._entry_debug_content.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._label_debug_receiver.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._entry_debug_receiver.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._btn_debug_send.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)
        self._btn_debug_reset.pack(side=Tkinter.LEFT, fill=Tkinter.Y, pady=2)

        # Pack zones
        self._button_zone.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)
        self._in_label_frame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)
        self._out_label_frame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)

        # Boot receive message
        self._queue_thread.start()
        self._thread.start()

        if auto_mode:
            self.toggle_send()

    def save_snapshot(self):
        if self._save_status == True:
            if self._saved_clock.clocks[self._ident] < self._clock_vector.clocks[self._ident]:
                self._save_status = False
                self.save_snapshot()
        else:
            # save the snapshot
            self._save_status = True
            file = open("snapshot.txt",'a')
            text = "SNAPSHOT "+str(self._count_snapshot)+", ident="+str(self._ident)\
                +", x="+str(self.x)+", vector="+str(self._clock_vector.clocks)+"\n"
            file.write(text)
            self._saving = True
            self._count_snapshot += 1
            # send marker
            marker = self._encoder.encode(self._ident, '', '3', json.dumps(dict()), str(self._msg_counter))
            self._msg_counter += 1

            self._queue_thread.add_action(QueueThread.TRANS, marker)
            #send_time = time.time()
            #self._text_debug.insert(Tkinter.END, "[{}][{}] Message sent: {}\n".format(send_time, self._ident, marker))
            #self._text_debug.see(Tkinter.END)
            #sys.stderr.write("[{}][{}] Message sent: {}\n".format(send_time, self._ident, marker))

            #sys.stdout.write(marker + "\n")
            #sys.stdout.flush()
            self._saving = False

            # save the clock saved
            self._saved_clock = copy.deepcopy(self._clock_vector)   # Not good, maybe we should do sth

    def toggle_send(self):
        if self._join_net:
            self._join_net = False
            self._btn_force_send["state"] = "disable"
            self._btn_start["text"] = "Commencer"
        else:
            self._join_net = True
            self._btn_force_send["state"] = "normal"
            self._btn_start["text"] = "Finir"


    def send_message(self, content=None):
        if self._join_net:
            if not content:
                # Self send
                self._clock_vector.clocks[self._ident] += 1

                self._send_content = self.x

                content = dict()
                content.update({"x": float(self._send_content)})
                content.update({"clock": self._clock_vector.clocks})

                content = self._encoder.encode(self._ident, '', '1', json.dumps(content), str(self._msg_counter))
                # Log to message received
                self._msg_received.update({"{}-{}".format(self._ident, self._msg_counter): time.time()})
                self._msg_counter += 1

            send_time = time.time()
            self._text_debug.insert(Tkinter.END, "[{}][{}] Message sent: {}\n".format(send_time, self._ident, content))
            self._text_debug.see(Tkinter.END)
            sys.stderr.write("[{}][{}] Message sent: {}\n".format(send_time, self._ident, content))

            sys.stdout.write(content + "\n")
            sys.stdout.flush()



    def pack_message(self):
        content = dict()
        content.update({"x": float(self._entry_debug_content.get())})
        content.update({"clock": copy.copy(self._clock_vector.clocks)})
        content["clock"][self._ident] += 1

        content = self._encoder.encode(self._ident, self._entry_debug_receiver.get(), self._entry_debug_protocol.get(), json.dumps(content), str(self._msg_counter))

        send_time = time.time()
        self._text_debug.insert(Tkinter.END, "[{}][{}] Message generated: {}\n".format(send_time, self._ident, content))
        self._text_debug.see(Tkinter.END)
        sys.stderr.write("[{}][{}] Message generated: {}\n".format(send_time, self._ident, content))

        if self._join_net:
            self._clock_vector.clocks[self._ident] += 1

            send_time = time.time()
            self._text_debug.insert(Tkinter.END, "[{}][{}] Message sent: {}\n".format(send_time, self._ident, content))
            self._text_debug.see(Tkinter.END)
            sys.stderr.write("[{}][{}] Message sent: {}\n".format(send_time, self._ident, content))

            sys.stdout.write(content + "\n")
            sys.stdout.flush()

            self._msg_counter += 1


    def on_quit(self):
        self._window.quit()


    def on_message(self, content):
        self._queue_thread.add_action(QueueThread.RECEIVE, content)


    def on_update_value(self, value):
         self.x = value
         self._in_msg_label["text"] = str(float(self.x))
         self._clock_vector.clocks[self._ident] += 1


    def update_value(self):
        value = self._out_msg_entry.get()
        #self.on_update_value(value) # updates itself, doesn't need codage
        #self._clock_vector.clocks[self._ident] += 1

        self._queue_thread.add_action(QueueThread.UPDATE, value)
        self._queue_thread.add_action(QueueThread.SEND, value)
        #self._send_content = str(value)
        #self.send_message()


    def mainloop(self):
        if self._window and hasattr(self._window, "mainloop"):
            self._window.mainloop()
            if self._thread.is_alive():
                self._thread.stop() # Request thread to quit
            if self._queue_thread.is_alive():
                self._queue_thread.stop()

    def switch_debug(self):
        if self._debug_zone.visibility:
            self._debug_zone.pack_forget()
        else:
            self._debug_zone.pack(fill=Tkinter.BOTH, expand=Tkinter.YES, side=Tkinter.TOP, pady=5)

        self._debug_zone.visibility = not self._debug_zone.visibility

    def reset_debug(self):
        self._entry_debug_protocol.delete(0, Tkinter.END)
        self._entry_debug_protocol.insert(0, "1")

        self._entry_debug_content.delete(0, Tkinter.END)

        self._entry_debug_receiver.delete(0, Tkinter.END)

    def send_async(self, content, direct=False):
        if direct:
            self.send_message(content)
        else:
            self._send_content = str(content)
            self.send_message()

    def receive_async(self, content):
        receive_time = time.time()
        self._text_debug.insert(Tkinter.END, "[{}][{}] Message received: {}\n".format(receive_time, self._ident, content))
        self._text_debug.see(Tkinter.END)
        sys.stderr.write("[{}][{}] Message received: {}\n".format(receive_time, self._ident, content))
        #value = int(content)

        values = self._decoder.decode(content)

        frame = json.loads(values["content"])

        if "{}-{}".format(values["identity"], values["message_counter"]) in self._msg_received.keys():
            self._text_debug.insert(Tkinter.END, "[{}][{}] Message dropped: {}\n".format(receive_time, self._ident, content))
            self._text_debug.see(Tkinter.END)
            sys.stderr.write("[{}][{}] Message dropped: {}\n".format(receive_time, self._ident, content))
            return
        else:
            # Log to message received
            self._msg_received.update({"{}-{}".format(values["identity"], values["message_counter"]): time.time()})
            if values["protocol"] == str(1):
                other_clock = Clock()
                other_clock.clocks = frame["clock"]

                if self._ident in other_clock.clocks.keys() and self._clock_vector.clocks[self._ident] < other_clock.clocks[self._ident]:
                    # Incoherence
                    self._text_debug.insert(Tkinter.END, "[{}][{}] Clock not sync, incoherence: {} < {}\n"\
                        .format(receive_time, self._ident, other_clock.clocks, self._clock_vector.clocks))
                    self._text_debug.see(Tkinter.END)
                    sys.stderr.write("[{}][{}] Clock not sync, incoherence: {} < {}\n"\
                        .format(receive_time, self._ident, other_clock.clocks, self._clock_vector.clocks))
                else:
                    if self._saving == True:
                        file = open("snapshot.txt",'a')
                        text = "SNAPSHOT "+str(self._count_snapshot)+", ident="+str(self._ident)\
                            +", x="+str(self.x)+", vector="+str(self._clock_vector.clocks)+", MESSAGE "\
                            +str(values["identity"])+" TO "+str(self._ident)+"\n"
                        file.write(text)
                    self._clock_vector.sync(other_clock)

                    self._text_debug.insert(Tkinter.END, "[{}][{}] Clock sync: {}\n".format(receive_time, self._ident, self._clock_vector.clocks))
                    self._text_debug.see(Tkinter.END)
                    sys.stderr.write("[{}][{}] Clock sync: {}\n".format(receive_time, self._ident, self._clock_vector.clocks))

                    self.on_update_value(frame["x"])

                self._queue_thread.add_action(QueueThread.TRANS, content)
            elif values["protocol"] == str(2):
                other_clock = Clock()
                other_clock.clocks = frame["clock"]

                if self._ident in values["destination"].split(self._decoder.split_list):
                    if self._ident in other_clock.clocks.keys() and self._clock_vector.clocks[self._ident] < other_clock.clocks[self._ident]:
                        self._text_debug.insert(Tkinter.END, "[{}][{}] Clock not sync, ours are newer: {} < {}\n"\
                            .format(receive_time, self._ident, other_clock.clocks, self._clock_vector.clocks))
                        self._text_debug.see(Tkinter.END)
                        sys.stderr.write("[{}][{}] Clock not sync, ours are newer: {} < {}\n"\
                            .format(receive_time, self._ident, other_clock.clocks, self._clock_vector.clocks))
                    else:
                        if self._saving == True:
                            file = open("snapshot.txt",'a')
                            text = "SNAPSHOT "+str(self._count_snapshot)+", ident="+str(self._ident)\
                                +", x="+str(self.x)+", vector="+str(self._clock_vector.clocks)+", MESSAGE "\
                                +str(values["identity"])+" TO "+str(self._ident)+"\n"
                            file.write(text)
                        self._clock_vector.sync(other_clock)

                        self._text_debug.insert(Tkinter.END, "[{}][{}] Clock sync: {}\n".format(receive_time, self._ident, self._clock_vector.clocks))
                        self._text_debug.see(Tkinter.END)
                        sys.stderr.write("[{}][{}] Clock sync: {}\n".format(receive_time, self._ident, self._clock_vector.clocks))

                        self.on_update_value(frame["x"])

                self._queue_thread.add_action(QueueThread.TRANS, content)

            elif values["protocol"] == str(3):
                # Handle snapshot here
                if self._save_status:
                    if self._saved_clock.clocks[self._ident] < self._clock_vector.clocks[self._ident]:
                        self._save_status = False
                        self.save_snapshot()
                else:
                    self.save_snapshot()

    def __del__(self):
        # Do clean works
        pass
        #del self._thread
