from flask import Flask, jsonify, Response
app = Flask(__name__)

states = []
control = []
tokens = {}

base_handler = lambda: print("\n".join(map(lambda st: str(st.get()), states)))

class State:
    def __init__(self, name: str, default_value: object):
        self.name = name
        self.__value = default_value
    def toggle(self):
        if isinstance(self.__value, bool):
            self.__value = not self.__value
        elif isinstance(self.__value, int):
            if self.__value == 0: self.__value = 1
            elif self.__value == 1: self.__value = 0
        return self.get()
    def inc(self, a: int):
        if not isinstance(self.__value, int): return
        self.__value += a
        return self.get()
    def get(self):
        return {"name": self.name, "value": self.__value}
    def set(self, a: object):
        self.__value = a
        return self.get()

class ImpState(State):
    def __init__(self, name: str):
        self.name = name
        self.__value = False
    def set(self):
        self.__value = True
        return {"name": self.name, "value": self.__value}
    def check(self):
        if self.__value == True:
            self.__value = False
            return {"name": self.name, "value": True}
        return {"name": self.name, "value": False}
    def get(self):
        return {"name": self.name, "value": self.__value}

class PC:
    def __init__(self, name: str):
        self.__enable = False
        self.__disable = False
        self.value = False
        self.name = name
    
    def set(self, value):
        if value == 1:
            self.__enable = True
        if value == 0:
            self.__disable = True
            self.value = False
        return self.get()
    
    def check_enable(self):
        result = self.get()
        self.__enable = False
        return result
    
    def check_disable(self):
        result = self.get()
        self.__disable = False
        return result
    
    def check(self):
        result = self.get()
        self.__disable = self.__enable = False
        return result

    def get(self): 
        return {"name": self.name, "value": self.value, "disable": self.__disable, "enable": self.__enable}
    
    def sync(self, value: int):
        self.value = bool(value)
        return self.get()

class LED:
    def __init__(self, name):
        self.name = name
        self.__enable = False
        self.__disable = False
        self.value = False
    
    def set(self, value):
        if value == 1:
            self.__enable = True
            self.value = True
        elif value == 0:
            self.__disable = True
            self.value = False
        return self.get()
    
    def toggle(self):
        if self.value:
            self.__disable = True
        else:
            self.__enable = True
        self.value = not self.value
        return self.get()
    
    def sync(self):
        self.value = not self.value
        return self.get()
    
    def get(self): 
        return {"name": self.name, "value": self.value}
    
    def get_str(self):
        result = f"{'1' if self.__enable else '0'}{'1' if self.__disable else '0'}"
        self.__enable = self.__disable = False
        return result

#function example:          lambda state, value: state.set(value)
def control_function(state: State, func, unit):
    def wrapper(*args, **kwargs):
        if kwargs["token"] not in tokens.keys(): return {"text":"not authorizated"}
        if not tokens[kwargs["token"]].match(unit): return {"text":"not access"}
        kwargs.pop("token")
        result = func(state, *args, **kwargs)
        base_handler()
        return result
    wrapper.__name__ = str(id(func))
    return wrapper

class ControlUnit:
    def __init__(self, path: str, state: State, function):
        self.path = path + "/<string:token>"
        self.state = state
        self.function = control_function(self.state, function, self)
        app.add_url_rule(self.path, view_func=self.function)

class Token:
    def __init__(self, text: str, units: list[ControlUnit]):
        self.text = text
        self.units = units
    
    def match(self, unit):
        if unit in self.units:
            return True
        return False

#Add your rules here:
states.append(led_state := LED("LED"))
states.append(pc_state := PC("Home's pc"))

pc_group = []
group_voice = []
esp_group = []

group_voice.append(ControlUnit("/led", led_state, lambda led: led.get()))
group_voice.append(ControlUnit("/led/toggle", led_state, lambda led: led.toggle()))
group_voice.append(ControlUnit("/led/set<int:value>", led_state, lambda led, value: led.set(value)))
group_voice.append(a:=ControlUnit("/pc/set<int:value>", pc_state, lambda pc, value: pc.set(value)))
group_voice.append(ControlUnit("/pc", pc_state, lambda pc: pc.get()))

esp_group.append(ControlUnit("/str/led", led_state, lambda led: led.get_str()))
esp_group.append(ControlUnit("/str/led/toggle", led_state, lambda led: led.toggle()))
esp_group.append(ControlUnit("/str/led/set<int:value>", led_state, lambda led, value: led.set(value)))

pc_group.append(ControlUnit("/pc/check/enable", pc_state, lambda pc: pc.check_enable()))
pc_group.append(ControlUnit("/pc/check/disable", pc_state, lambda pc: pc.check_disable()))
pc_group.append(ControlUnit("/pc/check", pc_state, lambda pc: pc.check()))
pc_group.append(ControlUnit("/pc/sync<int:value>", pc_state, lambda pc, value: pc.sync(value)))
pc_group.append(a)

control.extend(pc_group)
control.extend(group_voice)

tokens.update({"4ae48788aa9dad4dfa84ce9f822220c2": Token("4ae48788aa9dad4dfa84ce9f822220c2", group_voice)})        #Alice's token
tokens.update({"4279f50441a1370ea8b5a0fabd686f2d": Token("4279f50441a1370ea8b5a0fabd686f2d", pc_group)})           #PC's token
tokens.update({"843447436771e832c9c70b07ef2daaca": Token("843447436771e832c9c70b07ef2daaca", esp_group)})          #esp's token
#end

app.run("0.0.0.0", 6734, debug=True)