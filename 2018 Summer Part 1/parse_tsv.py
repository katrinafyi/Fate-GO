import os
import json

def main():
    os.chdir(os.path.dirname(__file__))
    currencies = ('water', 'wood', 'iron', 'stone', 'food')
    
    locations = {}
    with open('currency_drop.tsv') as f:
        current_mat = None
        for l in f:
            if l.startswith('Your Bonus:'):
                continue
            s = l.rstrip('\n').split('\t')
            s[0] = s[0].lower()
            if s[0] in currencies:
                current_mat = s[0]
            elif s[0]:
                if s[0] not in locations:
                    locations[s[0]] = {}
                locations[s[0]][current_mat.lower()] = [float(x) for x in s[1:]]
    
    with open('currency_drops_parsed.json', 'w') as f:
        f.write(json.encoder.JSONEncoder(indent=2)
            .encode(locations)
            )

if __name__ == '__main__':
    main()