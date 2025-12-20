from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import random


class BMSApp(App):

    def build(self):
        main_layout = BoxLayout(
            orientation='vertical',
            padding=10,
            spacing=10
        )

        # ---------------- TOP BAR ----------------
        top_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=75,
            spacing=10
        )

        menu_button = Button(
            text='Menu',
            size_hint=(None, None),
            size=(120, 75),
            font_size=22
        )
        menu_button.bind(on_press=self.open_menu)
        top_layout.add_widget(menu_button)

        title = Label(
            text='5S1P BMS DASHBOARD',
            font_size=36,
            bold=True
        )
        top_layout.add_widget(title)

        main_layout.add_widget(top_layout)

        # ---------------- PACK PARAMETERS ----------------
        def create_param(label_text, value_text):
            layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=55,
                spacing=20
            )
            label = Label(
                text=label_text,
                font_size=20,
                bold=True,
                size_hint_x=0.5
            )
            value = TextInput(
                text=value_text,
                readonly=True,
                multiline=False,
                font_size=30,
                halign='center'
            )
            layout.add_widget(label)
            layout.add_widget(value)
            return layout, value

        voltage_layout, self.pack_voltage = create_param(
            "Pack Voltage (V):",
            str(round(random.uniform(57, 60), 2))
        )

        current_layout, self.pack_current = create_param(
            "Pack Current (A):",
            str(round(random.uniform(0, 10), 2))
        )

        temp_layout, self.pack_temp = create_param(
            "Temperature (°C):",
            str(round(random.uniform(20, 40), 2))
        )

        soc_layout, self.pack_soc = create_param(
            "State of Charge (%):",
            str(round(random.uniform(20, 100), 1))
        )

        main_layout.add_widget(voltage_layout)
        main_layout.add_widget(current_layout)
        main_layout.add_widget(temp_layout)
        main_layout.add_widget(soc_layout)

        self.soc_bar = ProgressBar(
            max=100,
            value=float(self.pack_soc.text),
            size_hint_y=None,
            height=25
        )
        main_layout.add_widget(self.soc_bar)

        # ---------------- CELL VOLTAGES (5S1P) ----------------
        cell_title = Label(
            text="Cell Voltages",
            font_size=28,
            bold=True,
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(cell_title)

        self.cell_grid = GridLayout(
            cols=1,
            spacing=10,
            padding=5,
            size_hint_y=None
        )
        self.cell_grid.bind(minimum_height=self.cell_grid.setter('height'))

        self.cell_inputs = []

        for i in range(1, 6):  # 5S1P = 5 cells
            cell_layout = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=55,
                spacing=20
            )

            label = Label(
                text=f"Cell {i}",
                font_size=20,
                bold=True,
                size_hint_x=0.4
            )

            value = TextInput(
                text=str(round(random.uniform(3.6, 3.9), 3)),
                readonly=True,
                multiline=False,
                font_size=30,
                halign='center'
            )

            self.cell_inputs.append(value)
            cell_layout.add_widget(label)
            cell_layout.add_widget(value)
            self.cell_grid.add_widget(cell_layout)

        main_layout.add_widget(self.cell_grid)

        # ---------------- UPDATE TIMER ----------------
        Clock.schedule_interval(self.update_values, 1)

        return main_layout

    # ---------------- DATA UPDATE ----------------
    def update_values(self, dt):
        self.pack_voltage.text = str(round(random.uniform(57, 60), 2))
        self.pack_current.text = str(round(random.uniform(0, 10), 2))
        self.pack_temp.text = str(round(random.uniform(20, 40), 2))

        soc = round(random.uniform(20, 100), 1)
        self.pack_soc.text = str(soc)
        self.soc_bar.value = soc

        for cell in self.cell_inputs:
            cell.text = str(round(random.uniform(3.6, 3.9), 3))

    # ---------------- MENU ----------------
    def open_menu(self, instance):
        layout = BoxLayout(
            orientation='vertical',
            spacing=15,
            padding=15
        )

        dashboard_btn = Button(text="Dashboard")
        params_btn = Button(text="Set Parameters")
        close_btn = Button(text="Close")

        close_btn.bind(on_press=lambda x: self.menu_popup.dismiss())

        layout.add_widget(dashboard_btn)
        layout.add_widget(params_btn)
        layout.add_widget(close_btn)

        self.menu_popup = Popup(
            title="Menu",
            content=layout,
            size_hint=(None, None),
            size=(400, 500)
        )
        self.menu_popup.open()


if __name__ == "__main__":
    BMSApp().run()
