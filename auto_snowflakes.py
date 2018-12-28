import imagesearch
import time
import pyautogui
from collections import namedtuple, defaultdict
from itertools import product

from math import sqrt

import cv2
import numpy as np

SNOWFLAKES = 'images/snowflakes_node.png'
MENU = 'images/main_menu.png'
AP = 'images/restore_ap.png'
OK = 'images/ap_ok.png'
WAVER = 'images/waver.png'
WAVER_MLB = 'images/waver_mlb.png'
SUPPORT = 'images/support.png'
UPDATE = 'images/update.png'
SCROLL = 'images/scroll.png'
START = 'images/start.png'

def found(pos):
    return pos[0] != -1

def find(image, p=None):
    return imagesearch.imagesearch(image, precision=(p or 0.85))

def click(image, pos):
    return imagesearch.click_image(image, pos, 'left', 0.25)

def pause():
    time.sleep(1)

def find_loop(image, p=None):
    print('Waiting for', image)
    result = find(image, p)
    while not found(result):
        time.sleep(0.5)
        result = find(image, p)
    print('Found', image)
    return result

def click_loop(image, p=None):
    click(image, find_loop(image, p))

def click_waver():
    first = True
    while True:
        for i in range(3):
            waver = find(WAVER_MLB)
            if found(waver):
                click(WAVER, waver)
                return
            print('Scrolling...')
            click_loop(SCROLL)
            pyautogui.mouseDown()
            pyautogui.moveRel(0, 60, 2)
            pyautogui.mouseUp()
            pause()

        print('Updating supports...')
        if first:
            first = False 
        else:
            time.sleep(15)
        click_loop(UPDATE)
        click_loop(OK)
        find_loop(SUPPORT)

def i(name):
    return 'images/'+name.replace(' ', '_')+'.png'

def click_attack():
    click_loop(i('attack'))

def arash_stella():
    click_loop(i('arash_np'))
    pyautogui.moveRel(0, 250, 0.25)
    pyautogui.click()
    pyautogui.moveRel(150, 0, 0.25)
    pyautogui.click()

Card = namedtuple('Card', ('servant', 'type', 'image', 'pos'))

def sort_cards(cards: list):
    strength = {
        'quick': 0,
        'arts': 10,
        'buster': 20
    }
    cards.sort(key=lambda x: strength[x.type], reverse=True)    

cards = list(product(
    ('chloe', 'scat', 'waver', 'scathach'), 
    ('buster', 'quick', 'arts')
))

def find_multiple(image, p=0.85):
    seen = set()
    im = pyautogui.screenshot()
    #im.save('testarea.png') usefull for debugging purposes, this will save the captured region as "testarea.png"
    img_rgb = np.array(im)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(image, 0)
    template.shape[::-1]

    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    res = np.where(res >= p)
    seen = set()
    near = lambda pt: (pt[0]//50, pt[1]//50)
    filtered = []
    for pt in zip(*res[::-1]):
        if any((pt[0]-x0)**2 + (pt[1]-y0)**2 < 30**2 for x0, y0 in seen):
            continue
        seen.add(pt)
    print('Found multiple', image, seen)
    
    return seen

def detect_cards():
    found = []
    p = 0.8
    target = 5
    while len(found) != target:
        found.clear()
        for card in cards:
            image = i('cards/'+'_'.join(card))
            try:
                for pos in find_multiple(image, p=p):
                    found.append(Card(card[0], card[1], image, pos))
            except AttributeError as e: 
                print(card, 'errored')
        old_p = p
        p += (len(found)-target)*0.025
        p = min(0.9, p)
        print('Corrected p', old_p, p)
    return found

def click_cards(cards):
    print('Clicking cards')
    for c in cards:
        print(c.servant, c.type)
        click(c.image, c.pos)

def count_cards(cards):
    servants = defaultdict(lambda: 0)
    types = defaultdict(lambda: 0)
    for c in cards:
        servants[c.servant] += 1 
        types[c.type] += 1 
    return (servants, types)

def strongest(n, cards):
    cards = list(cards)
    if n:
        return cards[:n][::-1]
    return cards[::-1]

def wave_cards(order1, order2=('scat', 'chloe', 'scathach', 'waver'), n=2):
    cards = detect_cards()
    servants, types = count_cards(cards)

    type_priority = ('buster', 'arts', 'quick')
    by_type = lambda c: type_priority.index(c.type)


    of_servant = lambda s: filter(lambda c: c.servant==s, cards)
    of_type = lambda t: filter(lambda c: c.type==t, cards)

    for s in order1:
        if servants[s] >= 2:
            print('found 2 of', s)
            chosen = set(of_servant(s))
            chosen.update(cards)
            chosen = list(chosen)

            combined_order = (s, ) + order1 + order2
            chosen.sort(key=by_type)
            chosen.sort(key=lambda c: combined_order.index(c.servant) 
                if c.servant in combined_order else 100)
            
            click_cards(strongest(n, chosen))
            return 
    
    print('fallback!')
    fallbacks = []
    for s in order2:
        fallbacks.extend(of_servant(s))
    fallbacks.sort(key=by_type)
    fallbacks.sort(key=lambda c: order2.index(c.servant) 
        if c.servant in order2 else 100)
    print(fallbacks)
    click_cards(strongest(n, fallbacks))

def click_skill(skill):
    click_loop(i('skill_'+skill), p=0.8)
    time.sleep(0.25)

def click_loopi(image):
    click_loop(i(image))

def face_card():
    click_attack()
    wave_cards(('scat', 'chloe', 'scathach', 'waver'), n=3)
    pause()

def run_snowflakes():
    start_time = time.time()

    click_loop(SNOWFLAKES, p=0.7)
    time.sleep(2)
    ap = find(AP)
    
    if found(ap):
        click(AP, ap)
        click(OK, find_loop(OK))

    find_loop(SUPPORT)
    click_waver()

    click_loop(START)
    click_loop(i('arash_np_up'))
    pause()
    click_loop(i('attack'))
    arash_stella()

    find_loop(i('wave_2'))
    
    for s in ('atk', 'def', 'proj', 'np'):
        click_skill(s)
    click_attack()

    click_loop(i('chloe_np'))
    wave_cards(('chloe', 'scat'))

    while True:    
        find_loop(i('battle_menu'))
        if found(find(i('wave 2'))):
            face_card()
        else:
            break
    for s in ('target', 'pierce', 'evade', 'crit'):
        click_skill(s)
    click_skill('on_scat')
    click_skill('master')
    click_skill('atk_master')
    click_skill('master')
    click_skill('gandr')
    click_skill('master')
    click_skill('change')
    
    click_loopi('waver_icon')
    click_loopi('scathach_icon')
    click_loopi('replace')

    click_skill('quick')
    click_skill('on_scat')

    click_attack()

    click_loopi('scat_np')
    wave_cards(('scat', ))

    while True:
        bond = found(find(i('bond')))
        tap = found(find(i('please_tap')))
        battle = found(find(i('battle_menu')))
        pause()
        if bond or tap:
            break
        elif battle:
            face_card()
    
    while True:
        close = find(i('close'))
        next_button = find(i('next'))
        if found(next_button):
            click(i('next'), next_button)
            pyautogui.moveRel(0, -100, 1)
            break
        elif found(close):
            click(i('close'), close)
            continue
        pyautogui.click()
        pause()
        pause()

    while True:
        request = find(i('request'))
        menu = find(MENU)
        if found(menu):
            break 
        elif found(request):
            click(i('request'), request)
        pyautogui.click()
        pause()

    return time.time() - start_time

if __name__ == '__main__':
    times = []
    while True:
        times.append(run_snowflakes()/60)
        print('Previous run:', times[-1], 'minutes')
        print(f'Average of {len(times)} runs:', sum(times)/len(times), 'minutes')