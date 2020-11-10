from PIL import Image, ImageDraw, ImageFont
from i3ipc import Connection, Event

def show_image(img):
    img.show()

def create_ws_matte(apps, ws_w, ws_h, ws_name, ws_offset, main_matte, scale):
    term = ''
    chrome = ''
    fnt =  ImageFont.truetype('/home/wtheisen/Downloads/Literation Mono Bold Nerd Font Complete.ttf', 32)

    def draw_app_rect(x, y, w, h, g, s, o):
        x = int(x * s) + offset
        y = int(y * s)
        w = int(w * s)
        h = int(h * s)

        main_matte.rectangle([x, y, x + w, y + h], fill = (255, 0, 0))
        main_matte.text((int(x + w / 2), int(y + h / 2)), g, font=fnt, fill=(0, 0, 255))

    for a in apps:
        r = a.rect
        if 'Term' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, term, scale, offset)
        elif 'Chrome' in a.name:
            draw_app_rect(r.x, r.y, r.width, r.height, chrome, scale, offset)
        else:
            print('App type not found')
        # print(f'Name: {a.name}, W: {r.width}, H: {r.height}, X: {r.x}, Y: {r.y}')

    # matte.save(f'ws_{ws_name}_matte.png')

def combine_ws_mattes(ws_mattes):
    pass

i3 = Connection()

tree = i3.get_tree()

t_rect = tree.rect
main_matte = Image.new('RGB', (t_rect.width, t_rect.height), color = (150, 150, 150))
draw_matte = ImageDraw.Draw(main_matte)

offset = 0
num_ws = len(tree.workspaces())
scale = 1 / num_ws
for ws in tree.workspaces():
    create_ws_matte(ws.leaves(), ws.rect.width, ws.rect.height, ws.name, offset, draw_matte, scale)
    offset += int(ws.rect.width * scale)

show_image(main_matte)
