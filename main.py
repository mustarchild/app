from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen

import asyncio
import threading
from bleak import BleakClient


# ================= BLE CONFIG =================
BLE_ADDRESS = "AA:BB:CC:DD:EE:FF"   # 🔴 CHANGE THIS
BLE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # 🔴 CHANGE THIS


# ================= SHARED BMS DATA =================
bms_data = {
    "pack_voltage": 0.0,
    "pack_current": 0.0,
    "pack_temp": 0.0,
    "soc": 0.0,
    "cells": [0.0] * 16
}


# ================= BLE HANDLER =================
def parse_ble_data(data: str):
    """
    Expected:
    V=56.2,I=12.4,T=32.1,SOC=78,C1=3.65,...,C16=3.67
    """
    try:
        parts = data.split(",")

        for part in parts:
            if "=" not in part:
                continue

            key, val = part.split("=")

            if key == "V":
                bms_data["pack_voltage"] = float(val)
            elif key == "I":
                bms_data["pack_current"] = float(val)
            elif key == "T":
                bms_data["pack_temp"] = float(val)
            elif key == "SOC":
                bms_data["soc"] = float(val)
            elif key.startswith("C"):
                idx = int(key[1:]) - 1
                if 0 <= idx < 16:
                    bms_data["cells"][idx] = float(val)
    except:
        pass


async def ble_task():
    async with BleakClient(BLE_ADDRESS) as client:
        print("BLE Connected")

        def notification_handler(sender, data):
            text = data.decode(errors="ignore")
            parse_ble_data(text)

        await client.start_notify(BLE_CHAR_UUID, notification_handler)

        while True:
            await asyncio.sleep(1)


def start_ble_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ble_task())


# ================= DASHBOARD SCREEN =================
class DashboardScreen(Screen):

    def build_ui(self):
        main = BoxLayout(orientation='vertical', padding=10, spacing=10)

        top = BoxLayout(size_hint_y=None, height=75, spacing=10)

        btn = Button(text="Set Parameters", size_hint=(None, None),
                     size=(200, 75), font_size=20)
        btn.bind(on_press=self.goto_params)

        title = Label(text="16S BMS DASHBOARD", font_size=34, bold=True)

        top.add_widget(btn)
        top.add_widget(title)
        main.add_widget(top)

        def param(name):
            box = BoxLayout(size_hint_y=None, height=55)
            lbl = Label(text=name, font_size=18, bold=True)
            ti = TextInput(readonly=True, font_size=26, text="0.0")
            box.add_widget(lbl)
            box.add_widget(ti)
            main.add_widget(box)
            return ti

        self.pack_voltage = param("Pack Voltage (V)")
        self.pack_current = param("Pack Current (A)")
        self.pack_temp = param("Temperature (°C)")
        self.pack_soc = param("State of Charge (%)")

        self.soc_bar = ProgressBar(max=100, size_hint_y=None, height=25)
        main.add_widget(self.soc_bar)

        grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        self.cell_inputs = []

        for i in range(16):
            box = BoxLayout(size_hint_y=None, height=50)
            lbl = Label(text=f"Cell {i+1}", font_size=16)
            ti = TextInput(readonly=True, font_size=22, text="0.000")
            box.add_widget(lbl)
            box.add_widget(ti)
            grid.add_widget(box)
            self.cell_inputs.append(ti)

        main.add_widget(grid)
        self.add_widget(main)

        Clock.schedule_interval(self.update_ui, 0.5)

    def update_ui(self, dt):
        self.pack_voltage.text = str(bms_data["pack_voltage"])
        self.pack_current.text = str(bms_data["pack_current"])
        self.pack_temp.text = str(bms_data["pack_temp"])
        self.pack_soc.text = str(bms_data["soc"])
        self.soc_bar.value = bms_data["soc"]

        for i in range(16):
            self.cell_inputs[i].text = str(bms_data["cells"][i])

    def goto_params(self, instance):
        self.manager.current = "params"


# ================= PARAMETERS SCREEN =================
class ParamsScreen(Screen):

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=20, spacing=15)

        root.add_widget(Label(text="BMS Protection Parameters",
                              font_size=30, bold=True,
                              size_hint_y=None, height=50))

        self.param(root, "Under Voltage (V)", 2.8)
        self.param(root, "Over Voltage (V)", 4.2)
        self.param(root, "Under Current (A)", -50)
        self.param(root, "Over Current (A)", 100)

        btn = Button(text="Back to Dashboard", size_hint_y=None,
                     height=65, font_size=22)
        btn.bind(on_press=self.goto_dashboard)
        root.add_widget(btn)

        root.add_widget(Label(size_hint_y=1))
        self.add_widget(root)

    def param(self, parent, name, default):
        box = BoxLayout(size_hint_y=None, height=60)
        box.add_widget(Label(text=name, font_size=18))
        box.add_widget(TextInput(text=str(default),
                                 font_size=24,
                                 multiline=False))
        parent.add_widget(box)

    def goto_dashboard(self, instance):
        self.manager.current = "dashboard"


# ================= APP =================
class BMSApp(App):

    def build(self):
        # Start BLE thread
        threading.Thread(target=start_ble_loop, daemon=True).start()

        sm = ScreenManager()

        dash = DashboardScreen(name="dashboard")
        dash.build_ui()

        params = ParamsScreen(name="params")
        params.build_ui()

        sm.add_widget(dash)
        sm.add_widget(params)

        return sm


if __name__ == "__main__":
    BMSApp().run()
