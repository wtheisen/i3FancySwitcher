import tcolors, cv2, numpy, math
from PIL import Image, ImageDraw, ImageFont
from i3ipc import Connection, Event

icon_dict = {
    'term':'',
    'chrome':'',
    'slack':'聆',
    'spotify':'',
    'vim': ''
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

def create_ws_matte(apps, ws_w, ws_h, ws_name, ws_x_offset, ws_y_offset, main_matte, scale):
    global icon_dict
    global ws_pos_dict
    global color_dict

    fnt =  ImageFont.truetype('/home/wtheisen/Downloads/Literation Mono Bold Nerd Font Complete.ttf', 64)

    def draw_app_rect(x, y, w, h, g, s, x_o, y_o):
        x = int(x * s) + x_o
        y = int(y * s) + y_o
        w = int(w * s)
        h = int(h * s)

        main_matte.rectangle([x, y, x + w, y + h], fill = color_dict['background'] + (255,))
        main_matte.text((int(x + w / 2) - 20, int(y + h / 2) - 20), g, font=fnt, fill = color_dict['color5'] + (255,))

    for a in apps:
        r = a.rect
        if 'vim' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['vim'], scale, ws_x_offset, ws_y_offset)
        elif 'Term' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['term'], scale, ws_x_offset, ws_y_offset)
        elif 'Chrome' in a.name or 'chrom' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['chrome'], scale, ws_x_offset, ws_y_offset)
        elif 'Spotify' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['spotify'], scale, ws_x_offset, ws_y_offset)
        elif 'Slack' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, icon_dict['slack'], scale, ws_x_offset, ws_y_offset)
        else:
            print('App type not found')

tree = i3.get_tree()

t_rect = tree.rect
main_matte = Image.new('RGBA', (t_rect.width, t_rect.height), color = color_dict['background'] + (0,))
draw_matte = ImageDraw.Draw(main_matte)

x_offset = 0
y_offset = int(t_rect.height / 2) - 250
num_ws = len(tree.workspaces())
rows = math.ceil(num_ws / 3)
scale = 1 / num_ws
print(f'Rows: {rows}, Scale: {scale}')

for ws in tree.workspaces():
    r = ws.rect
    x = int(r.x * scale) + x_offset
    y = int(r.y * scale) + y_offset
    w = int(r.width * scale)
    h = int(r.height * scale)
    ws_pos_dict[ws.name] = (x, y, w, h)

    draw_matte.rectangle([x, y, x + w, y + h], outline = color_dict['color1'] + (255,), fill = color_dict['foreground'] + (255,), width = 4)
    create_ws_matte(ws.leaves(), ws.rect.width, ws.rect.height, ws.name, x_offset, y_offset, draw_matte, scale)
    x_offset += int(ws.rect.width * scale)

img = numpy.array(main_matte)
img = img[:, :, ::-1].copy()

window_name = 'image'

cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
cv2.moveWindow(window_name, t_rect.x - 1, t_rect.y - 1)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow(window_name, img)
cv2.setMouseCallback(window_name, mouse_click)
cv2.waitKey(0)
