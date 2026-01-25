import fitz
from PIL import Image

pdf_path = r"E:\临时文件\郭修传离职证明.pdf"
output_path = "E:\临时文件\离职证明.png"

pdf = fitz.open(pdf_path)

imgs = []
for page in pdf:
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    imgs.append(img)

width = max(i.width for i in imgs)
height = sum(i.height for i in imgs)

long_img = Image.new("RGB", (width, height), "white")

y = 0
for img in imgs:
    long_img.paste(img, (0, y))
    y += img.height

long_img.save(output_path)
print("生成成功")
