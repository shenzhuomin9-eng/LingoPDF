"""Build matching vector, PNG and Windows icon assets from simple geometry."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / 'static'
scale = 3
image = Image.new('RGBA', (512 * scale, 512 * scale))
draw = ImageDraw.Draw(image)
for y in range(512 * scale):
    t = y / (512 * scale - 1)
    color = tuple(round(a + (b - a) * t) for a, b in zip((9,99,86),(25,156,133))) + (255,)
    draw.line((0,y,512*scale,y), fill=color)
mask = Image.new('L', image.size)
ImageDraw.Draw(mask).rounded_rectangle((0,0,512*scale-1,512*scale-1), radius=112*scale, fill=255)
image.putalpha(mask)
shapes = [
    ('polygon', [(83,154),(216,120),(255,140),(295,120),(427,154),(427,377),(295,351),(255,370),(215,351),(83,377)], '#044f48'),
    ('polygon', [(91,137),(221,111),(249,129),(249,350),(216,337),(91,362)], '#f6fbf6'),
    ('polygon', [(263,129),(292,111),(421,137),(421,362),(293,337),(263,350)], '#ffffff'),
    ('line', [(130,283),(207,267)], '#b3d9cb',12),
    ('line', [(130,312),(207,296)], '#b3d9cb',12),
    ('line', [(301,267),(379,283)], '#b3d9cb',12),
    ('line', [(301,296),(379,312)], '#b3d9cb',12),
    ('line', [(139,238),(166,165),(194,227)], '#147c69',14),
    ('line', [(150,211),(182,205)], '#147c69',12),
    ('line', [(337,165),(337,244)], '#147c69',12),
    ('line', [(306,179),(369,190),(369,223),(306,212),(306,179)], '#147c69',10),
    ('circle', (381,374,66), '#eed78e'),
    ('line', [(349,363),(403,363),(391,350)], '#08665a',10),
    ('line', [(414,386),(360,386),(372,399)], '#08665a',10),
]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">',
       '<defs><linearGradient id="teal" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#096356"/><stop offset="1" stop-color="#199c85"/></linearGradient></defs>',
       '<rect width="512" height="512" rx="112" fill="url(#teal)"/>']
for kind, points, color, *extra in shapes:
    if kind == 'circle':
        x,y,radius = points
        draw.ellipse(tuple(v*scale for v in (x-radius,y-radius,x+radius,y+radius)),fill=color)
        svg.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{color}"/>')
    else:
        coords = [(x*scale,y*scale) for x,y in points]
        vertices = ' '.join(f'{x},{y}' for x,y in points)
        if kind == 'polygon':
            draw.polygon(coords, fill=color)
            svg.append(f'<polygon points="{vertices}" fill="{color}"/>')
        else:
            width = extra[0]
            draw.line(coords,fill=color,width=width*scale,joint='curve')
            for x,y in coords:
                r = width*scale/2
                draw.ellipse((x-r,y-r,x+r,y+r),fill=color)
            svg.append(f'<polyline points="{vertices}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')
svg.append('</svg>')
(root/'favicon.svg').write_text('\n'.join(svg),encoding='utf-8')
image = image.resize((512,512),Image.Resampling.LANCZOS)
image.save(root/'favicon.png')
image.save(root/'app-icon.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
(root/'favicon.ico').write_bytes((root/'app-icon.ico').read_bytes())
print('SVG / PNG / ICO icons generated')
