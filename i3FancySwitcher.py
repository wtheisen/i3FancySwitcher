import tcolors, cv2, numpy
from PIL import Image, ImageDraw, ImageFont
from i3ipc import Connection, Event

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

def create_ws_matte(apps, ws_w, ws_h, ws_name, ws_offset, main_matte, scale):
    global ws_pos_dict
    global color_dict

    term = ''
    chrome = ''
    fnt =  ImageFont.truetype('/home/wtheisen/Downloads/Literation Mono Bold Nerd Font Complete.ttf', 32)

    def draw_app_rect(x, y, w, h, g, s, o):
        x = int(x * s) + offset
        y = int(y * s)
        w = int(w * s)
        h = int(h * s)


        main_matte.rectangle([x, y, x + w, y + h], fill = color_dict['background'] + (255,))
        main_matte.text((int(x + w / 2), int(y + h / 2)), g, font=fnt, fill = color_dict['color5'] + (255,))

    for a in apps:
        r = a.rect
        if 'Term' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, term, scale, offset)
        elif 'Chrome' in a.name or 'chrom' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, chrome, scale, offset)
        else:
            print('App type not found')

tree = i3.get_tree()

t_rect = tree.rect
main_matte = Image.new('RGBA', (t_rect.width, t_rect.height), color = color_dict['background'] + (255,))
draw_matte = ImageDraw.Draw(main_matte)

offset = 0
num_ws = len(tree.workspaces())
scale = 1 / num_ws

for ws in tree.workspaces():
    r = ws.rect
    x = int(r.x * scale) + offset
    y = int(r.y * scale)
    w = int(r.width * scale)
    h = int(r.height * scale)
    ws_pos_dict[ws.name] = (x, y, w, h)

    draw_matte.rectangle([x, y, x + w, y + h], outline = color_dict['color1'] + (255,), fill = color_dict['color2'] + (255,), width = 4)
    create_ws_matte(ws.leaves(), ws.rect.width, ws.rect.height, ws.name, offset, draw_matte, scale)
    offset += int(ws.rect.width * scale)

img = numpy.array(main_matte)
img = img[:, :, ::-1].copy()

window_name = 'image'

cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow(window_name, t_rect.x - 1, t_rect.y - 1)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow(window_name, img)
cv2.setMouseCallback(window_name, mouse_click)
cv2.waitKey(0)
