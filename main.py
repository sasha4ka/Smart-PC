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
        if not isinstance(self.__value, bool): return
        self.__value = not self.__value
        return {}
    
    def inc(self, a: int):
        if not isinstance(self.__value, int): return
        self.__value += a
        return {}
    
    def get(self):
        return {"name": self.name, "value": self.__value}
    
    def set(self, a: object):
        self.__value = a
        return {}

def control_function(state: State, func):
    def wrapper(*args):
        result = func(state, *args)
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
states.append(led_state := State("LED", False))
control.append(ControlUnit("/led", led_state, lambda state: state.get()))
control.append(ControlUnit("/led/toggle", led_state, lambda state: state.toggle()))
#end

app.run("127.0.0.1", 6734, debug=True)