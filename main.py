from flask import Flask, jsonify
app = Flask(__name__)

states = []
control = []
tokens = {}

base_handler = lambda: print("\n".join(map(lambda state: f"{state.name}\t\t{state.get()['value']}", states)))

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
group1 = []
group_voice = []
states.append(led_state := State("LED", 0))
states.append(start_state := ImpState("PC_start"))
states.append(halt_state := ImpState("PC_halt"))
group_voice.append(ControlUnit("/led", led_state, lambda state: state.get()))
group_voice.append(ControlUnit("/led/toggle", led_state, lambda state: state.toggle()))
group_voice.append(ControlUnit("/led/set<int:value>", led_state, lambda state, value: state.set(value)))
group_voice.append(ControlUnit("/pc-start/start", start_state, lambda i_state: i_state.set()))
group_voice.append(ControlUnit("/pc-halt/halt", halt_state, lambda i_state: i_state.set()))
group1.append(ControlUnit("/pc-start/check", start_state, lambda i_state: i_state.check()))
group1.append(ControlUnit("/pc-halt/check", halt_state, lambda i_state: i_state.check()))
control.extend(group1)
control.extend(group_voice)
tokens.update({"4ae48788aa9dad4dfa84ce9f822220c2": Token("4ae48788aa9dad4dfa84ce9f822220c2", group_voice)})      #Alice's token
tokens.update({"4279f50441a1370ea8b5a0fabd686f2d": Token("4279f50441a1370ea8b5a0fabd686f2d", group1)})           #PC's token
#end

app.run("0.0.0.0", 6734, debug=True)