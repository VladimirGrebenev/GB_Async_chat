import yaml

doom_setup = {
    'cheats': ['god', 'give ammo', 'spawn weapon_bfg'],
    'doom version': 1,
    'cost': {
        'god': '3€',
        'give ammo': '2€',
        'spawn weapon_bfg': '1€',
    },
}

with open('file.yaml', 'w') as f_n:
    yaml.dump(doom_setup, f_n,  default_flow_style=False, allow_unicode=True)

with open('file.yaml', 'r') as f_n:
    print(f_n.read())

