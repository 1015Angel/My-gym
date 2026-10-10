"""Prepara la app Mi Gym para compilarla como APK (lo usa GitHub Actions)."""
import os, re, sys, shutil, glob

WEB = ["index.html", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "manifest.webmanifest"]
BLUE = (47, 123, 245, 255)
DARK = (18, 18, 18, 255)
WHITE = (255, 255, 255, 255)


def web():
    os.makedirs("www", exist_ok=True)
    for f in WEB:
        if os.path.exists(f):
            shutil.copy(f, os.path.join("www", f))
    print("web lista")


def dumbbell(size, frac, color=WHITE, bg=None, rounded=False):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if bg:
        if rounded:
            d.ellipse([0, 0, size - 1, size - 1], fill=bg)
        else:
            d.rectangle([0, 0, size, size], fill=bg)
    s = size * frac / 10000
    o = (size - 100 * s) / 2

    def r(x0, y0, x1, y1, rad):
        d.rounded_rectangle([round(o + x0 * s), round(o + y0 * s), round(o + x1 * s), round(o + y1 * s)], radius=max(1, round(rad * s)), fill=color)

    r(10, 38, 18, 62, 3); r(20, 28, 32, 72, 4); r(68, 28, 80, 72, 4); r(82, 38, 90, 62, 3); r(30, 46, 70, 54, 2)
    return im


def android():
    from PIL import Image
    res = "android/app/src/main/res"
    # Íconos de la app
    for f in glob.glob(res + "/mipmap-*/ic_launcher_foreground.png"):
        n = Image.open(f).size[0]
        dumbbell(n, 50).save(f)
    for f in glob.glob(res + "/mipmap-*/ic_launcher.png"):
        n = Image.open(f).size[0]
        im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(im).rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.22), fill=BLUE)
        im.alpha_composite(dumbbell(n, 72))
        im.save(f)
    for f in glob.glob(res + "/mipmap-*/ic_launcher_round.png"):
        n = Image.open(f).size[0]
        dumbbell(n, 66, bg=BLUE, rounded=True).save(f)
    with open(res + "/values/ic_launcher_background.xml", "w") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#2F7BF5</color>\n</resources>\n')
    # Pantalla de carga
    for f in glob.glob(res + "/drawable*/splash.png"):
        w, h = Image.open(f).size
        im = Image.new("RGBA", (w, h), DARK)
        n = int(min(w, h) * 0.32)
        icon = dumbbell(n, 72, bg=BLUE, rounded=True)
        im.alpha_composite(icon, ((w - n) // 2, (h - n) // 2))
        im.convert("RGB").save(f)
    # Ícono de notificación (blanco sobre transparente)
    for dens, n in {"mdpi": 24, "hdpi": 36, "xhdpi": 48, "xxhdpi": 72, "xxxhdpi": 96}.items():
        os.makedirs(f"{res}/drawable-{dens}", exist_ok=True)
        dumbbell(n, 92).save(f"{res}/drawable-{dens}/ic_stat_migym.png")
    # Colores de la barra de estado (sobrescriben los de Capacitor)
    with open(res + "/values/colors.xml", "w") as fh:
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                 '    <color name="colorPrimary">#121212</color>\n'
                 '    <color name="colorPrimaryDark">#121212</color>\n'
                 '    <color name="colorAccent">#2F7BF5</color>\n</resources>\n')
    # Versión y firma
    run = int(os.environ.get("RUN_NUMBER", "1"))
    g = "android/app/build.gradle"
    txt = open(g).read()
    txt = re.sub(r"versionCode \d+", f"versionCode {run}", txt)
    txt = re.sub(r'versionName "[^"]*"', f'versionName "1.{run}"', txt)
    txt += """
android {
    signingConfigs {
        release {
            storeFile file('migym.jks')
            storePassword System.getenv('KS_PASS')
            keyAlias 'migym'
            keyPassword System.getenv('KS_PASS')
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled false
        }
    }
    lint {
        checkReleaseBuilds false
        abortOnError false
    }
}
"""
    open(g, "w").write(txt)
    print(f"android listo (versión 1.{run})")


if __name__ == "__main__":
    {"web": web, "android": android}[sys.argv[1]]()
