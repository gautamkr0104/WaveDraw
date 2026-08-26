import os
from PIL import Image, ImageDraw, ImageFilter

def create_glow_image(draw_func, size=(64, 64), glow_color=(0, 255, 255, 255), core_color=(255, 255, 255, 255)):
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    
    # 1. Base image for glow (blurred thick stroke)
    img_glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(img_glow)
    draw_func(draw_glow, scale, glow_color, width=int(4*scale))
    img_glow = img_glow.filter(ImageFilter.GaussianBlur(2.5 * scale))
    
    # 2. Base image for core (sharp thin stroke)
    img_core = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_core = ImageDraw.Draw(img_core)
    draw_func(draw_core, scale, core_color, width=int(1.5*scale))
    
    # Composite the core over the glow
    final_img = Image.alpha_composite(img_glow, img_core)
    
    # Resize down with Lanczos resampling for anti-aliasing
    final_img = final_img.resize(size, Image.Resampling.LANCZOS)
    return final_img

# --- Custom Icon Drawings ---

def draw_brush(draw, scale, color, width):
    # Handle
    draw.line([(34*scale, 30*scale), (52*scale, 12*scale)], fill=color, width=width)
    # Ferrule (metal band)
    draw.line([(28*scale, 36*scale), (34*scale, 30*scale)], fill=color, width=int(width * 1.5))
    # Bristles (polygon pointing down-left)
    draw.polygon([
        (28*scale, 36*scale),
        (34*scale, 30*scale),
        (16*scale, 48*scale)
    ], fill=color)
    # Sleek curved splash stroke underneath
    draw.arc([(10*scale, 38*scale), (32*scale, 54*scale)], start=60, end=240, fill=color, width=width)

def draw_eraser(draw, scale, color, width):
    # Draw a tilted eraser block
    p1 = (20*scale, 36*scale)
    p2 = (44*scale, 20*scale)
    p3 = (50*scale, 28*scale)
    p4 = (26*scale, 44*scale)
    draw.polygon([p1, p2, p3, p4], outline=color, width=width)
    
    # Divide the eraser block to look like sleeve + rubber
    pm1 = (32*scale, 28*scale)
    pm2 = (38*scale, 36*scale)
    draw.line([pm1, pm2], fill=color, width=width)
    
    # Erase dust details
    draw.line([(10*scale, 44*scale), (16*scale, 44*scale)], fill=color, width=width)
    draw.line([(8*scale, 39*scale), (13*scale, 39*scale)], fill=color, width=width)

def draw_save(draw, scale, color, width):
    # Floppy disk shape
    p1 = (14*scale, 14*scale)
    p2 = (42*scale, 14*scale)
    p3 = (50*scale, 22*scale)
    p4 = (50*scale, 50*scale)
    p5 = (14*scale, 50*scale)
    draw.polygon([p1, p2, p3, p4, p5], outline=color, width=width)
    
    # Sliding metal cover at the bottom
    draw.rectangle([(22*scale, 34*scale), (42*scale, 50*scale)], outline=color, width=width)
    
    # Write-protect window
    draw.rectangle([(33*scale, 38*scale), (38*scale, 45*scale)], fill=color)
    
    # Sticker area at the top
    draw.rectangle([(20*scale, 14*scale), (44*scale, 28*scale)], outline=color, width=width)

def main():
    os.makedirs("assets", exist_ok=True)
    os.makedirs("outputs/drawings", exist_ok=True)
    
    # Generate and save brush icon (Cyan Theme)
    brush_img = create_glow_image(draw_brush, glow_color=(0, 220, 255, 200), core_color=(240, 255, 255, 255))
    brush_img.save("assets/brush.png")
    print("Saved assets/brush.png")
    
    # Generate and save eraser icon (Pink/Magenta Theme)
    eraser_img = create_glow_image(draw_eraser, glow_color=(255, 0, 180, 200), core_color=(255, 240, 250, 255))
    eraser_img.save("assets/eraser.png")
    print("Saved assets/eraser.png")
    
    # Generate and save save icon (Green Theme)
    save_img = create_glow_image(draw_save, glow_color=(0, 255, 120, 200), core_color=(240, 255, 245, 255))
    save_img.save("assets/save.png")
    print("Saved assets/save.png")

if __name__ == "__main__":
    main()
