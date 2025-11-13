import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import os, platform, numpy as np
import uuid # Untuk membuat nama file unik

# Direktori sementara untuk menyimpan file yang akan diunduh
OUTPUT_DIR = "temp_downloads"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------
#  FUNGSI DASAR (SAMA DENGAN VERSI KAMU)
# -------------------------------

def load_font(font_name="arial", size=40):
    system = platform.system()
    font_paths = {
        "Windows": {
            "arial": "C:\\Windows\\Fonts\\arial.ttf",
            "impact": "C:\\Windows\\Fonts\\impact.ttf"
        },
        "Linux": {
            "arial": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "impact": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        },
        "Darwin": {
            "arial": "/Library/Fonts/Arial.ttf",
            "impact": "/Library/Fonts/Impact.ttf"
        },
    }
    try:
        path = font_paths.get(system, {}).get(font_name.lower(), None)
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
        else:
            return ImageFont.load_default()
    except:
        return ImageFont.load_default()

def parse_color(c):
    if isinstance(c, str):
        if c.startswith("rgba"):
            nums = [float(x) for x in c.replace("rgba(", "").replace(")", "").split(",")]
            return (int(nums[0]), int(nums[1]), int(nums[2]))
        elif c.startswith("rgb"):
            nums = [float(x) for x in c.replace("rgb(", "").replace(")", "").split(",")]
            return (int(nums[0]), int(nums[1]), int(nums[2]))
        elif c.startswith("#"):
            return c
    return (255, 255, 255)

# -------------------------------
#  FUNGSI MEMBUAT MEME
# -------------------------------
# Fungsi ini sekarang mengembalikan objek Image PIL
def generate_meme(image, top_text, bottom_text, font_size, color, font_name, top_y, bottom_y):
    if image is None:
        return None

    color = parse_color(color)

    if isinstance(image, dict):
        if "image" in image:
            image = image["image"]
        else:
            image = list(image.values())[0]

    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    elif isinstance(image, str):
        image = Image.open(image)
    elif not isinstance(image, Image.Image):
        return None

    image = image.convert("RGBA")
    draw = ImageDraw.Draw(image)
    font = load_font(font_name, int(font_size))
    width, height = image.size

    # Fungsi draw_multiline_centered (tetap di dalam)
    def draw_multiline_centered(text, y):
        lines = text.split("\n")
        
        try:
            line_height = font.getbbox("A")[3] + 5
        except: # Fallback
            line_height = int(font_size * 1.2)
            
        current_y = y
        for line in lines:
            w = draw.textlength(line, font=font)
            x = (width - w) / 2
            for ox in [-2, 0, 2]:
                for oy in [-2, 0, 2]:
                    if ox != 0 or oy != 0:
                        draw.text((x + ox, current_y + oy), line, font=font, fill="black")
            draw.text((x, current_y), line, font=font, fill=color)
            current_y += line_height

    if top_text:
        draw_multiline_centered(top_text.upper(), top_y)
    if bottom_text:
        draw_multiline_centered(bottom_text.upper(), bottom_y)

    return image # Mengembalikan objek Image PIL

# 🆕 FUNGSI BARU: Simpan Gambar dan Kembalikan Path untuk Download
def save_and_return_path(image):
    if image is None:
        return None
    
    # Simpan file dengan nama unik
    filename = os.path.join(OUTPUT_DIR, f"meme_result_{uuid.uuid4()}.png")
    image.save(filename, format="PNG")
    
    # Kembalikan path file, yang akan digunakan oleh gr.File
    return filename

# -------------------------------
#  TEMPLATE HANDLER
# -------------------------------
def load_template(template_name):
    if not template_name or template_name == "Upload Sendiri":
        return None
    # Asumsi Anda sudah memiliki folder 'templates' dengan gambar-gambar
    template_path = os.path.join("templates", template_name.lower().replace(" ", "_") + ".jpg")
    # Cek apakah file template ada di path 'templates/'
    if os.path.exists(template_path):
        return template_path
    else:
        # Jika template tidak ditemukan, kembalikan None atau path dummy
        return None

# -------------------------------
#  UI GRADIO
# -------------------------------
with gr.Blocks() as demo:
    gr.Markdown("## 💾 Meme Generator")

    with gr.Row():
        template = gr.Dropdown(
            ["Upload Sendiri", "jaemin", "jeno", "haechan"],
            label="Pilih Template Meme",
            value="Upload Sendiri"
        )
        # Input gambar tetap sama
        image_input = gr.Image(type="filepath", label="Upload Gambar Sendiri (opsional)")
    
    with gr.Row():
        # Output 1: Preview (PIL Image)
        image_preview = gr.Image(label="Preview Meme", type="pil", interactive=False)
        # Output 2: Download Link (File Path) 🆕
        download_file = gr.File(label="Hasil Unduhan", type="filepath", interactive=False)

    with gr.Row():
        top_text = gr.Textbox(label="Teks Atas", lines=2)
        bottom_text = gr.Textbox(label="Teks Bawah", lines=2)

    with gr.Row():
        font_size = gr.Slider(10, 100, value=40, step=2, label="Ukuran Font")
        font_name = gr.Dropdown(["arial", "impact"], label="Font", value="impact")
        color = gr.ColorPicker(value="#ffffff", label="Warna Font")

    with gr.Row():
        top_y = gr.Slider(0, 1000, value=50, step=5, label="Posisi Y Teks Atas")
        bottom_y = gr.Slider(0, 1000, value=900, step=5, label="Posisi Y Teks Bawah")

    generate_btn = gr.Button("🎨 Generate & Download Meme")
    
    # Saat user pilih template, update gambar otomatis
    template.change(fn=load_template, inputs=template, outputs=image_input)

    # Memproses klik tombol:
    # 1. generate_meme menghasilkan objek PIL Image.
    # 2. save_and_return_path menerima objek tersebut, menyimpannya, dan mengembalikan path filenya.
    generate_btn.click(
        fn=generate_meme,
        inputs=[image_input, top_text, bottom_text, font_size, color, font_name, top_y, bottom_y],
        outputs=image_preview
    ).then(
        fn=save_and_return_path,
        inputs=image_preview,
        outputs=download_file
    )

demo.launch()