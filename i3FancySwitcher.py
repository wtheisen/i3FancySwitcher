import tcolors, cv2, numpy, math, sys
import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont
from i3ipc import Connection, Event

icon_dict = {
    'Vim': '',
    'Term':'',
    'Chrom':'',
    'Slack':'聆',
    'Spotify':'',
    'unknown':''
}

ws_pos_dict = {}
i3 = Connection()

def hex_to_rgb(hex_col):
    h = hex_col.lstrip('#')
    return tuple((int(h[i:i+2], 16) for i in (0, 2, 4)))

color_dict = {}
for c in tcolors.get_xcolors('/home/wtheisen/.cache/wal/colors.Xresources', '*'):
    color_dict[c[0]] = hex_to_rgb(c[1])

def show_image(img):
    img.show()

def create_ws_matte(apps, ws_w, ws_h, ws_name, scale, ws_matte, fnt):
    global icon_dict
    global ws_pos_dict
    global color_dict

    draw_matte = ImageDraw.Draw(ws_matte)

    def draw_app_rect(x, y, w, h, g, s):
        x = int(x * s)
        y = int(y * s)
        w = int(w * s)
        h = int(h * s)

        draw_matte.rectangle([x, y, x + w, y + h], fill = color_dict['background'] + (255,))
        t_w, t_h = draw_matte.textsize(g, font=fnt)
        t_x = (x + w - t_w) / 2
        t_y = (y + h - t_h) / 2
        draw_matte.text((t_x, t_y), g, font=fnt, fill = color_dict['color5'] + (255,))

    prev_app_rect = None
    tabbed = False
    g_string = ''
    for a in apps:
        r = a.rect

        if prev_app_rect:
            tabbed = False
            if r.x == prev_app_rect.x and r.y == prev_app_rect.y:
                tabbed = True
            else:
                prev_app_rect = None

        key = [s for s in icon_dict.keys() if s in a.name]
        if len(key) < 1:
            key = ['unknown']

        if tabbed:
            g_string += (' ' + icon_dict[key[0]])
            prev_app_rect = r
        elif not tabbed and g_string != '':
            if prev_app_rect:
                p_r = prev_app_rect
                draw_app_rect(p_r.x, p_r.y, p_r.width, p_r.height, g_string, scale)
                g_string = ''
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict[key[0]], scale)
        elif not tabbed and g_string == '':
            g_string = icon_dict[key[0]]
            draw_app_rect(r.x, r.y, r.width, r.height, g_string, scale)
            prev_app_rect = r

    if tabbed and g_string != '':
        p_r = prev_app_rect
        draw_app_rect(p_r.x, p_r.y, p_r.width, p_r.height, g_string, scale)

    ws_matte.save(f'ws_{ws_name}_matte.png')
    return f'ws_{ws_name}_matte.png'

def create_ws_buttons(ws_matte_filename_list, t_rect, orient, scale):
    if orient[0] == 'v':
        layout_list = []
    else:
        layout_list = [[]]

    for ws_matte in ws_matte_filename_list:
        ws_name = ''.join(ws_matte.split('_')[1:-1])
        btn = sg.Button('', image_filename = ws_matte,
                image_size=(int(t_rect.width * scale), int(t_rect.height * scale)),
                key=ws_name,)
                # button_color=(sg.theme_background_color(), sg.theme_background_color()))
        if orient[0] == 'v':
            layout_list.append([btn])
        else:
            layout_list[0].append(btn)

    return layout_list

#################################

bg_image = sys.argv[1]

tree = i3.get_tree()
t_rect = tree.rect

num_ws = len(tree.workspaces())
# scale = 1 / num_ws
scale = 0.25
print(f'Scale: {scale}')

fnt =  ImageFont.truetype('/home/wtheisen/Downloads/Literation Mono Bold Nerd Font Complete.ttf', 64)
ws_matte = Image.open(bg_image).resize((int(t_rect.width * scale), int(t_rect.height * scale)))
ws_matte_filename_list = []

main_size = [0, 0]
for ws in tree.workspaces():
    r = ws.rect
    x = int(r.x * scale)
    y = int(r.y * scale)
    w = int(r.width * scale)
    h = int(r.height * scale)
    ws_pos_dict[ws.name] = (x, y, w, h)
    main_size[0] += w
    main_size[1] += h

    ws_matte_filename_list.append(create_ws_matte(ws.leaves(), w, h, ws.name, scale, ws_matte.copy(), fnt))

orient = sys.argv[2]
ws_button_list = create_ws_buttons(ws_matte_filename_list, t_rect, orient, scale)

loc = [1, 1]
size = [1, 1]

if orient[0] == 'c':
    w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0)
elif orient[0] == 'v':
    size[0] = int(t_rect.width * 0.25) + 30
    size[1] = main_size[1] + 100
    if orient[1] == 'l':
        loc[0] = 1
        loc[1] = int(t_rect.height / 2) - int(size[1] / 2)
    elif orient[1] == 'r':
        loc[0] = t_rect.width - size[0]
        loc[1] = int(t_rect.height / 2) - int(size[1] / 2)
    w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0,
            location=(loc[0],loc[1]),
            size=(size[0], size[1]))
elif orient[0] == 'h':
    size[0] = main_size[0] + 70
    size[1] = int(t_rect.height * 0.25) + 30
    if orient[1] == 't':
        loc[0] = int(t_rect.width / 2) - int(size[0] / 2)
        loc[1] = 1
    elif orient[1] == 'b':
        loc[0] = int(t_rect.width / 2) - int(size[0] / 2)
        loc[1] = t_rect.height - size[1]
    w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0,
            location=(loc[0],loc[1]),
            size=(size[0], size[1]))

events, values = w.read()
print(f'Clicked on {events}')
w.close()
i3.command(f'workspace {events}')
