try:
    from PIL import Image, ImageDraw, ImageFont
    print("PIL_AVAILABLE = True")
except ImportError:
    print("PIL_AVAILABLE = False")
