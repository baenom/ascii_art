import io
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_char_darkness(char):
    darkness_map = {
        " ": 0, ".": 5, ",": 7, "-": 10, "_": 12, "+": 25, "=": 30, 
        "ㄱ": 35, "ㄴ": 35, "ㅇ": 45, "ㄹ": 55, "ㅎ": 65, "ㅂ": 70, 
        "ㅁ": 75, "ㅌ": 75, "형": 95, "빽": 100, "먕": 100
    }
    if char in darkness_map:
        return darkness_map[char]
    return 20 + (ord(char) % 70)


def make_ascii_chars_from_word(word_string, is_reverse=True):
    unique_chars = list(set(word_string))
    char_scores = [(char, get_char_darkness(char)) for char in unique_chars]
    
    if is_reverse:
        char_scores.sort(key=lambda x: x[1], reverse=True) 
    else:
        char_scores.sort(key=lambda x: x[1], reverse=False)

    sorted_chars = [char for char, score in char_scores]
    
    if " " not in sorted_chars:
        if is_reverse:
            sorted_chars.append(" ")
        else:
            sorted_chars.insert(0, " ")
            
    return sorted_chars


def resize_image(image, new_width=100):
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(new_width * aspect_ratio * 0.5)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS) 

def pixels_to_ascii(image, ascii_chars):

    pixels = list(image.getdata())
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
    reverse: str = Form("true"),
    output_width: int = Form(40)
):
    try:
        image_bytes = await image.read()
        raw_img = Image.open(io.BytesIO(image_bytes))

        if raw_img.mode in ("RGBA", "LA") or (raw_img.mode == "P" and "transparency" in raw_img.info):
            img = Image.new("RGBA", raw_img.size, (255, 255, 255))
            img.paste(raw_img, mask=raw_img.convert("RGBA").split()[3])
            img = img.convert("RGB")
        else:
            img = raw_img.convert("RGB")

        is_reverse_bool = (reverse.lower() == "true")

        dynamic_ascii_chars = make_ascii_chars_from_word(word, is_reverse=is_reverse_bool)

        img = resize_image(img, int(output_width))
        img = img.convert("L")

        ascii_str = pixels_to_ascii(img, dynamic_ascii_chars)
        pixel_count = len(ascii_str)
        
        ascii_image = "\n".join(
            ascii_str[i:(i + int(output_width))] for i in range(0, pixel_count, int(output_width))
        )
        
        return JSONResponse(content={
            "success": True,
            "used_chars": "".join(dynamic_ascii_chars),
            "result": ascii_image
        })
        
    except Exception as e:
        print(f"[SERVER ERROR]에러: {str(e)}")
        return JSONResponse(status_code=500, content={"success": False, "detail": str(e)})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)