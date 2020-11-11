import tcolors, cv2, numpy, math
import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont
from i3ipc import Connection, Event

icon_dict = {
    'term':'',
    'chrome':'',
    'slack':'聆',
    'spotify':'',
    'vim': '',
    'unknown': ''
}

ws_pos_dict = {}
i3 = Connection()

def mouse_click(event, x, y, flags, params):
    global i3
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f'Clicked X: {x}, Y: {y}')
        for name, pos in ws_pos_dict.items():
            if x > pos[0] and x < pos[0] + pos[2]:
                if y > pos[1] and y < pos[1] + pos[3]:
                    print(f'Clicked on {name}')
                    i3.command(f'workspace {name}')
                    exit()

def hex_to_rgb(hex_col):
    h = hex_col.lstrip('#')
    return tuple((int(h[i:i+2], 16) for i in (0, 2, 4)))

color_dict = {}
for c in tcolors.get_xcolors('/home/wtheisen/.cache/wal/colors.Xresources', '*'):
    color_dict[c[0]] = hex_to_rgb(c[1])

def show_image(img):
    img.show()

def create_ws_matte(apps, ws_w, ws_h, ws_name, scale):
    global icon_dict
    global ws_pos_dict
    global color_dict

    fnt =  ImageFont.truetype('/home/wtheisen/Downloads/Literation Mono Bold Nerd Font Complete.ttf', 64)
    ws_matte = Image.new('RGBA', (ws_w, ws_h), color = color_dict['background'] + (0,))
    draw_matte = ImageDraw.Draw(ws_matte)

    def draw_app_rect(x, y, w, h, g, s):
        x = int(x * s)
        y = int(y * s)
        w = int(w * s)
        h = int(h * s)

        draw_matte.rectangle([x, y, x + w, y + h], fill = color_dict['background'] + (255,))
        draw_matte.text((int(x + w / 2) - 20, int(y + h / 2) - 20), g, font=fnt, fill = color_dict['color5'] + (255,))

    for a in apps:
        r = a.rect
        if 'vim' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['vim'], scale)
        elif 'Term' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['term'], scale)
        elif 'Chrome' in a.name or 'chrom' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['chrome'], scale)
        elif 'spotify' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['spotify'], scale)
        elif 'Slack' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['slack'], scale)
        else:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['unknown'], scale)

    ws_matte.save(f'ws_{ws_name}_matte.png')
    return f'ws_{ws_name}_matte.png'

def create_ws_buttons(ws_matte_filename_list, t_rect, orient):
    if orient == 'vert':
        layout_list = []
    else:
        layout_list = [[]]

    for ws_matte in ws_matte_filename_list:
        ws_name = ''.join(ws_matte.split('_')[1:-1])
        btn = sg.Button('', image_filename = ws_matte,
                image_size=(int(t_rect.width * scale), int(t_rect.height * scale)),
                key=ws_name,)
                # button_color=(sg.theme_background_color(), sg.theme_background_color()))
        if orient == 'vert':
            layout_list.append([btn])
        else:
            layout_list[0].append(btn)

    return layout_list

#################################

tree = i3.get_tree()
t_rect = tree.rect

num_ws = len(tree.workspaces())
rows = math.ceil(num_ws / 3)
scale = 1 / num_ws
print(f'Rows: {rows}, Scale: {scale}')

ws_matte_filename_list = []
for ws in tree.workspaces():
    r = ws.rect
    x = int(r.x * scale)
    y = int(r.y * scale)
    w = int(r.width * scale)
    h = int(r.height * scale)
    ws_pos_dict[ws.name] = (x, y, w, h)

    ws_matte_filename_list.append(create_ws_matte(ws.leaves(), w, h, ws.name, scale))

orient = 'hor'
ws_button_list = create_ws_buttons(ws_matte_filename_list, t_rect, orient)
w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0)
events, values = w.read()
print(f'Clicked on {events}')
w.close()
i3.command(f'workspace {events}')
