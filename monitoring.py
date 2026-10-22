"""Read-only state change alerts."""

def transitions(previous, current):
    alerts = []
    for name, state in current.items():
        old = previous.get(name)
        if old is None and not state[0]:
            alerts.append('WARNING ' + name + ': ' + state[1])
        elif old is not None and old[0] != state[0]:
            alerts.append(('RECOVERED ' if state[0] else 'DOWN ') + name + ': ' + state[1])
    return alerts

def format_report(states):
    return '\n'.join(name + ': ' + detail for name, (healthy, detail) in states.items())
