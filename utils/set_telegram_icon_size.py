from PIL import Image

path = ''
resize_img_path = ''

img = Image.open(path)
img = img.resize((150, 150))
img.save(resize_img_path)
