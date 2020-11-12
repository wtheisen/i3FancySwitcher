import tcolors, cv2, numpy, math, sys, getopt
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
try:
    for c in tcolors.get_xcolors('/home/wtheisen/.cache/wal/colors.Xresources', '*'):
        color_dict[c[0]] = hex_to_rgb(c[1])
except:
    print('No .Xresources found, using fallbacks')
    color_dict['background'] = (10, 10, 10)
    color_dict['color5'] = (127, 127, 127)

def show_image(img):
    img.show()

def create_ws_matte(ws, scale, ws_matte, fnt_size_glyph, fnt_size_text, glyphs, ws_num):
    global icon_dict
    global ws_pos_dict
    global color_dict

    draw_matte = ImageDraw.Draw(ws_matte)

    def get_label(key):
        if glyphs:
            return icon_dict[key[0]]
        return key[0]

    def normalize(ws_rect, a_rect):
        if a_rect.x > ws_rect.width:
            a_rect.x = a_rect.x - ws_rect.width
        elif a_rect.y > ws_rect.height:
            a_rect.y = a_rect.y - ws_rect.height

        return a_rect

    def draw_app_rect(x, y, w, h, g, s):
        print(ws.rect.height, y + h)
        if (y + h) > ws.rect.height:
            h = (ws.rect.height - y) - ((ws.rect.height - y) * 0.05)
        x = int(x * s)
        y = int(y * s)
        w = int(w * s)
        h = int(h * s)

        draw_matte.rectangle([x, y, x + w, y + h], fill = color_dict['background'] + (255,))

        if glyphs:
            t_w, t_h = draw_matte.textsize(g, font=fnt_size_glyph)
            t_x = x + (w - t_w) / 2
            t_y = y + (h - t_h) / 2
            draw_matte.text((t_x, t_y), g, font=fnt_size_glyph, fill = color_dict['color5'] + (255,))
        else:
            t_w, t_h = draw_matte.textsize(g, font=fnt_size_text)
            t_x = x + (w - t_w) / 2
            t_y = y + (h - t_h) / 2
            draw_matte.text((t_x, t_y), g, font=fnt_size_text, fill = color_dict['color5'] + (255,))

        t_w, t_h = draw_matte.textsize(str(ws_num), font=fnt_size_glyph)
        draw_matte.text((1, 1), str(ws_num), font=fnt_size_glyph, fill = color_dict['color5'] + (255,))
        draw_matte.text((t_w + 5, (t_h - 1) / 2), '(' + ws.name + ')', font=fnt_size_text, fill = color_dict['color5'] + (255,))

    prev_app_rect = None
    tabbed = False
    g_string = ''
    for a in ws.leaves():
        r = normalize(ws.rect, a.rect)

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
            g_string += (' / ' + get_label(key))
            prev_app_rect = r
        elif g_string != '':
            if prev_app_rect:
                p_r = prev_app_rect
                draw_app_rect(p_r.x, p_r.y, p_r.width, p_r.height, g_string, scale)
                g_string = ''
            draw_app_rect(r.x, r.y, r.width, r.height, get_label(key), scale)
        elif g_string == '':
            g_string = get_label(key)
            draw_app_rect(r.x, r.y, r.width, r.height, g_string, scale)
            prev_app_rect = r

    if tabbed and g_string != '':
        p_r = prev_app_rect
        draw_app_rect(p_r.x, p_r.y, p_r.width, p_r.height, g_string, scale)

    ws_matte.save(f'ws_{ws.name}_matte.png')
    return f'ws_{ws.name}_matte.png'

def create_ws_buttons(ws_matte_filename_list, ws_rect, orient, scale):
    if orient[0] == 'v':
        layout_list = []
    else:
        layout_list = [[]]

    for ws_matte in ws_matte_filename_list:
        ws_name = ''.join(ws_matte.split('_')[1:-1])
        btn = sg.Button('', image_filename = ws_matte,
                image_size=(int(ws_rect.width * scale), int(ws_rect.height * scale)),
                border_width=0,
                key=ws_name,)
                # button_color=(sg.theme_background_color(), sg.theme_background_color()))
        if orient[0] == 'v':
            layout_list.append([btn])
        else:
            layout_list[0].append(btn)

    return layout_list

def usage(exit_code):
    print('Usage: python3 i3FancySwitcher -b [BACKGROUND_IMAGE] -f [FONT.TTF] [OPTIONAL_ARGS]')
    print('\t-b/--background: Path to the background image to use')
    print('\t-f/--font: Path to the .ttf file to use for the text')
    print("\t-l/--location: Location of the bar, options of 'vl', 'vr', 'ht', 'hb' (vertical left/right, horizontal top/bottom). If not given defaults to the center of the screen.")
    print('\t-g/--glyphs: no argument, specifies whether to describe workspace windows using icons or just text. Defaults to text')
    print('\t-s/--scale: Percentage of screen real estate to take up, defaults to 20%')
    print('\t-h/--help: Prints the usage')
    exit(exit_code)

#################################

if __name__ == "__main__":
    argv = sys.argv[1:]

    bg_image = None
    font = None
    orient = 'c'
    glyphs = False
    scale = 0.20

    try:
        opts, args = getopt.getopt(argv, 'b:f:l:ghs:',
                ['background=', 'font=', 'location=', 'scale=', 'glyphs', 'help'])
    except getopt.GetoptError:
        usage(1)

    for opt, arg in opts:
        print(opt, arg)
        if opt in ('-h', '--help'):
            usage(1)
        elif opt in ('-b', '--background'):
            bg_image = arg
        elif opt in ('-f', '--font'):
            font = arg
        elif opt in ('-l', '--location'):
            orient = arg
        elif opt in ('-g', '--glyphs'):
            glyphs = True
        elif opt in ('-s', '--scale'):
            scale = float(arg)

    if not bg_image or not font:
        print('background or font not set')
        usage(1)

    tree = i3.get_tree()
    t_rect = tree.rect

    num_ws = len(tree.workspaces())
    print(f'Scale: {scale}')

    fnt_size_glyph = ImageFont.truetype(font, int(320 * scale))
    fnt_size_text = ImageFont.truetype(font, int(130 * scale))

    ws_matte = Image.open(bg_image).resize((int(t_rect.width * scale), int(t_rect.height * scale)))
    ws_matte_filename_list = []

    main_size = [0, 0]
    ws_rect = None
    ws_num = 1

    ws_num_map_dict = {}

    for ws in tree.workspaces():
        r = ws.rect
        x = int(r.x * scale)
        y = int(r.y * scale)
        w = int(r.width * scale)
        h = int(r.height * scale)
        ws_pos_dict[ws.name] = (x, y, w, h)
        main_size[0] += w
        main_size[1] += h

        ws_matte_filename_list.append(create_ws_matte(ws, scale, ws_matte.copy(), fnt_size_glyph, fnt_size_text, glyphs, ws_num))
        ws_rect = ws.rect

        ws_num_map_dict[str(ws_num)] = ws.name
        ws_num += 1

    if len(sys.argv) == 4:
        orient = sys.argv[3]
    ws_button_list = create_ws_buttons(ws_matte_filename_list, ws_rect, orient, scale)

    loc = [1, 1]
    size = [1, 1]

    if orient[0] == 'v':
        size[0] = int(ws_rect.width * (scale + 0.01))
        size[1] = main_size[1] + int(ws_rect.height * 0.02)
        if orient[1] == 'l':
            loc[0] = 1
            loc[1] = int(ws_rect.height / 2) - int(size[1] / 2)
        elif orient[1] == 'r':
            loc[0] = ws_rect.width - size[0]
            loc[1] = int(ws_rect.height / 2) - int(size[1] / 2)
        w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0,
                return_keyboard_events=True,
                location=(loc[0],loc[1]),
                size=(size[0], size[1]))
    elif orient[0] == 'h':
        size[0] = main_size[0] + int(ws_rect.width * 0.02)
        size[1] = int(ws_rect.height * (scale + 0.01))
        if orient[1] == 't':
            loc[0] = int(ws_rect.width / 2) - int(size[0] / 2)
            loc[1] = 1
        elif orient[1] == 'b':
            loc[0] = int(ws_rect.width / 2) - int(size[0] / 2)
            loc[1] = ws_rect.height - size[1]
        w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0,
                return_keyboard_events=True,
                location=(loc[0],loc[1]),
                size=(size[0], size[1]))
    else:
        w = sg.Window('i3FancySwitcher', ws_button_list, alpha_channel = 1.0, return_keyboard_events=True)

    events, values = w.read()
    w.close()
    print(f'Clicked on {events}')
    if events in ws_num_map_dict.keys():
        events = ws_num_map_dict[events]
    i3.command(f'workspace {events}')
