import webbrowser
url =[
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%B4%AB%E3%81%AE%E5%A4%A2&index=18",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%B4%AB%E3%81%AE%E5%A4%A2&index=16",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%B4%AB%E3%81%AE%E5%A4%A2%203&index=32",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%9C%9F%E5%A4%8F%E3%81%AE%E5%A4%9C%E3%81%AE%E5%A4%A2&index=13",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%9C%9F%E5%A4%8F%E3%81%AE%E5%A4%9C%E3%81%AE%E5%A4%A2&index=14",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%B4%AB%E3%81%AE%E5%A4%A2%203&index=33",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E7%B4%AB%E3%81%AE%E5%A4%A2&index=17",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E5%9C%86%E9%A6%99%E6%B7%B1%E5%96%89&index=5",
  "http://127.0.0.1:5000/view_image?dir_path=YD%2F%E5%9C%86%E9%A6%99%E6%B7%B1%E5%96%89&index=6"
]
# 打开指定 URL
for i in url:
    webbrowser.open(i)