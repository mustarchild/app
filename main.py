from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

from jnius import autoclass
import threading

# ================= ANDROID BLUETOOTH =================
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
UUID = autoclass('java.util.UUID')
InputStreamReader = autoclass('java.io.InputStreamReader')
BufferedReader = autoclass('java.io.BufferedReader')
OutputStreamWriter = autoclass('java.io.OutputStreamWriter')

HC06_NAME = "HC-06"
SPP_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")

# ================= SHARED DATA =================
bms_data = {
    "V": 0.0,
    "I": 0.0,
    "T": 0.0,
    "SOC": 0.0,
    "cells": [0.0] * 16
}

params_data = {
    "UV": 2.8,
    "OV": 4.2,
    "UC": -50,
    "OC": 100
}

bt_writer = None

# ================= PARSER =================
def parse_data(line):
    try:
        parts = line.split(",")
        for p in parts:
            k, v = p.split("=")
            if k == "V": bms_data["V"] = float(v)
            elif k == "I": bms_data["I"] = float(v)
            elif k == "T": bms_data["T"] = float(v)
            elif k == "SOC": bms_data["SOC"] = float(v)
            elif k.startswith("C"):
                idx = int(k[1:]) - 1
                if 0 <= idx < 16:
                    bms_data["cells"][idx] = float(v)
    except:
        pass

# ================= BLUETOOTH THREAD =================
def bluetooth_thread():
    global bt_writer
    adapter = BluetoothAdapter.getDefaultAdapter()

    device = None
    for d in adapter.getBondedDevices().toArray():
        if d.getName() == HC06_NAME:
            device = d
            break

    if device is None:
        print("HC-06 not paired")
        return

    socket = device.createRfcommSocketToServiceRecord(SPP_UUID)
    socket.connect()

    reader = BufferedReader(InputStreamReader(socket.getInputStream()))
    bt_writer = OutputStreamWriter(socket.getOutputStream())

    while True:
        line = reader.readLine()
        if line:
            parse_data(line)

def send_params():
    if bt_writer:
        msg = f"UV={params_data['UV']},OV={params_data['OV']}," \
              f"UC={params_data['UC']},OC={params_data['OC']}\n"
        bt_writer.write(msg)
        bt_writer.flush()

# ================= DASHBOARD =================
class Dashboard(Screen):
    def build_ui(self):
        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        top = BoxLayout(size_hint_y=None, height=70)
        btn = Button(text="Set Parameters", size_hint=(None, None), size=(200, 70))
        btn.bind(on_press=lambda x: setattr(self.manager, "current", "params"))
        top.add_widget(btn)
        top.add_widget(Label(text="16S BMS DASHBOARD", font_size=32))
        root.add_widget(top)

        def row(name):
            b = BoxLayout(size_hint_y=None, height=50)
            b.add_widget(Label(text=name))
            t = TextInput(readonly=True)
            b.add_widget(t)
            root.add_widget(b)
            return t

        self.v = row("Voltage")
        self.i = row("Current")
        self.t = row("Temperature")
        self.soc = row("SOC")

        self.bar = ProgressBar(max=100, size_hint_y=None, height=25)
        root.add_widget(self.bar)

        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        self.cells = []

        for i in range(16):
            b = BoxLayout(size_hint_y=None, height=45)
            b.add_widget(Label(text=f"Cell {i+1}"))
            ti = TextInput(readonly=True)
            b.add_widget(ti)
            grid.add_widget(b)
            self.cells.append(ti)

        root.add_widget(grid)
        self.add_widget(root)

        Clock.schedule_interval(self.update_ui, 0.3)

    def update_ui(self, dt):
        self.v.text = f"{bms_data['V']:.2f}"
        self.i.text = f"{bms_data['I']:.2f}"
        self.t.text = f"{bms_data['T']:.1f}"
        self.soc.text = f"{bms_data['SOC']:.1f}"
        self.bar.value = bms_data["SOC"]

        for i in range(16):
            self.cells[i].text = f"{bms_data['cells'][i]:.3f}"

# ================= PARAMETERS =================
class Params(Screen):
    def build_ui(self):
        root = BoxLayout(orientation="vertical", padding=20, spacing=15)

        root.add_widget(Label(text="Set Protection Parameters",
                              font_size=28, size_hint_y=None, height=50))

        self.inputs = {}

        def param(name, key):
            b = BoxLayout(size_hint_y=None, height=60)
            b.add_widget(Label(text=name))
            ti = TextInput(text=str(params_data[key]), multiline=False)
            self.inputs[key] = ti
            b.add_widget(ti)
            root.add_widget(b)

        param("Under Voltage", "UV")
        param("Over Voltage", "OV")
        param("Under Current", "UC")
        param("Over Current", "OC")

        save = Button(text="Save & Send", size_hint_y=None, height=65)
        save.bind(on_press=self.save)
        root.add_widget(save)

        back = Button(text="Back", size_hint_y=None, height=65)
        back.bind(on_press=lambda x: setattr(self.manager, "current", "dash"))
        root.add_widget(back)

        root.add_widget(Label(size_hint_y=1))
        self.add_widget(root)

    def save(self, instance):
        for k in self.inputs:
            params_data[k] = float(self.inputs[k].text)
        send_params()

# ================= APP =================
class BMSApp(App):
    def build(self):
        threading.Thread(target=bluetooth_thread, daemon=True).start()

        sm = ScreenManager()
        d = Dashboard(name="dash"); d.build_ui()
        p = Params(name="params"); p.build_ui()
        sm.add_widget(d)
        sm.add_widget(p)
        return sm

if __name__ == "__main__":
    BMSApp().run()
