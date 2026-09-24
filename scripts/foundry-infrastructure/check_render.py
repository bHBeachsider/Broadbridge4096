from pathlib import Path
import pypdfium2 as pdfium
from pypdf import PdfReader
from PIL import Image, ImageOps, ImageDraw

root = Path(__file__).resolve().parents[2]
out = root / 'tmp/foundry-infrastructure/render'
path = out / 'SLM_Foundry_Broadbridge_Infrastructure_Brief.pdf'
pdf = pdfium.PdfDocument(path)
reader = PdfReader(path)
print('Pages:', len(pdf))
thumbs = []
for i, page in enumerate(pdf):
    image = page.render(scale=1.5).to_pil().convert('RGB')
    image.save(out / f'page-{i+1}.png')
    image.thumbnail((425, 550))
    thumb = Image.new('RGB', (445, 580), 'white')
    thumb.paste(image, (10, 20))
    ImageDraw.Draw(thumb).text((10, 3), f'Page {i+1}', fill='black')
    thumbs.append(thumb)
    txt = reader.pages[i].extract_text()
    lines = txt.splitlines()
    print(i+1, 'words', len(txt.split()), 'first', ' '.join(lines[:2]), 'last', ' '.join(lines[-3:]))
for start in range(0, len(thumbs), 4):
    canvas = Image.new('RGB', (890, 1160), '#d0d0d0')
    for k, thumb in enumerate(thumbs[start:start+4]):
        canvas.paste(thumb, ((k % 2)*445, (k // 2)*580))
    canvas.save(out / f'contact-{start//4+1}.png')
