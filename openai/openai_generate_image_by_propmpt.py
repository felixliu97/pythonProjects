import openai
import os

response = openai.Image.create(
  prompt="baby shark cocomelon",
  n=1,
  size="1024x1024"
)
image_url = response['data'][0]['url']

print(image_url)

os.startfile(image_url)