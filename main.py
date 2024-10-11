from flask import Flask, jsonify
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
        self.__shutdown = False
        self.__turned_on = True
        self.name = name
    
    def set(self, state: str):
        if state == "shutdown":
            self.__shutdown = True
            self.__turned_on = False
        if state == "turnon":
            self.__turned_on = True
        else:
            return {"text":"State not found"}
        return self.get()
    
    def set_state(self, value: int):
        self.__turned_on = not bool(value)
        return self.get()

    def check(self, state: str):
        result = self.get()
        if state == "shutdown": self.__shutdown = False
        return result
    
    def get(self): 
        return {"name": self.name, "turned_on": self.__turned_on, "shutdown": self.__shutdown}
    
    def turned_on(self):
        return {"name": self.name, "value": 1 if self.__turned_on else 0}

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
states.append(led_state := State("LED", 0))
states.append(pc_state := PC("Home's pc"))

pc_group = []
group_voice = []

group_voice.append(ControlUnit("/led", led_state, lambda state: state.get()))
group_voice.append(ControlUnit("/led/toggle", led_state, lambda state: state.toggle()))
group_voice.append(ControlUnit("/led/set<int:value>", led_state, lambda state, value: state.set(value)))
group_voice.append(ControlUnit("/pc/<string:param>/set", pc_state, lambda pc, param: pc.set(param)))
group_voice.append(ControlUnit("/pc/state", pc_state, lambda pc: pc.turned_on()))

pc_group.append(ControlUnit("/pc/<string:param>/check", pc_state, lambda pc, param: pc.check(param)))
pc_group.append(ControlUnit("/pc/state/set<int:value>", pc_state, lambda pc, value: pc.set_state(value)))

control.extend(pc_group)
control.extend(group_voice)

tokens.update({"4ae48788aa9dad4dfa84ce9f822220c2": Token("4ae48788aa9dad4dfa84ce9f822220c2", group_voice)})      #Alice's token
tokens.update({"4279f50441a1370ea8b5a0fabd686f2d": Token("4279f50441a1370ea8b5a0fabd686f2d", pc_group)})           #PC's token
#end

app.run("0.0.0.0", 6734, debug=True)