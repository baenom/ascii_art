import io
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont

app = FastAPI(title="Dynamic ASCII Art Generator API")

def get_char_darkness(char, font_size=20):
    img = Image.new("L", (font_size * 2, font_size * 2), 255)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("NanumGothic.ttf", font_size)
    except:
        font = ImageFont.load_default()

    draw.text((font_size // 2, font_size // 2), char, fill=0, font=font)
    pixels = list(img.getdata())
    darkness = sum(255 - p for p in pixels)
    
    return darkness

def make_ascii_chars_from_word(word_string, reverse=True):
    unique_chars = list(set(word_string))
    char_scores = [(char, get_char_darkness(char)) for char in unique_chars]

    char_scores.sort(key=lambda x: x[1], reverse=reverse)
    sorted_chars = [char for char, score in char_scores]
            
    return sorted_chars

def resize_image(image, new_width=100):
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(new_width * aspect_ratio * 0.8)
    return image.resize((new_width, new_height))

def grayscale_image(image):
    return image.convert("L")

def pixels_to_ascii(image, ascii_chars):
    pixels = image.getdata()
    ascii_str = ""
    num_chars = len(ascii_chars)
    
    for pixel_value in pixels:
        index = pixel_value * (num_chars - 1) // 255
        ascii_str += ascii_chars[index]
        
    return ascii_str

@app.post("/generate-ascii")
async def generate_ascii(
    image: UploadFile = File(...),
    word: str = Form(...),
    reverse: bool = Form(True),
    output_width: int = Form(40)
):
    try:
        image_bytes = await image.read()
        img = Image.open(io.BytesIO(image_bytes))
        
        dynamic_ascii_chars = make_ascii_chars_from_word(word, reverse=reverse)
        
        img = resize_image(img, output_width)
        img = grayscale_image(img)
        
        ascii_str = pixels_to_ascii(img, dynamic_ascii_chars)
        pixel_count = len(ascii_str)
        
        ascii_image = "\n".join(
            ascii_str[i:(i + output_width)] for i in range(0, pixel_count, output_width)
        )
        
        return JSONResponse(content={
            "success": True,
            "used_chars": "".join(dynamic_ascii_chars),
            "result": ascii_image
        })
        
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "success": False,
            "detail": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)