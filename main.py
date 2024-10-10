from flask import Flask, jsonify
app = Flask(__name__)

states = []
control = []

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

def control_function(state: State, func):
    def wrapper(*args, **kwargs):
        result = func(state, *args, **kwargs)
        base_handler()
        return result
    wrapper.__name__ = str(id(func))
    return wrapper

#function example:          lambda state, value: state.set(value)
class ControlUnit:
    def __init__(self, path: str, state: State, function):
        self.path = path
        self.state = state
        self.function = control_function(self.state, function)
        app.add_url_rule(self.path, view_func=self.function)

#Add your rules here:
states.append(led_state := State("LED", 0))
states.append(imp_state := ImpState("PC"))
control.append(ControlUnit("/led", led_state, lambda state: state.get()))
control.append(ControlUnit("/led/toggle", led_state, lambda state: state.toggle()))
control.append(ControlUnit("/led/set<int:value>", led_state, lambda state, value: state.set(value)))
control.append(ControlUnit("/pc/start", imp_state, lambda i_state: i_state.set()))
control.append(ControlUnit("/pc/check", imp_state, lambda i_state: i_state.check()))
#end

app.run("0.0.0.0", 6734)