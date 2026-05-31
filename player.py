import subprocess

def play(url):
    subprocess.run(["mpc", "clear"])
    subprocess.run(["mpc", "add", url])
    subprocess.run(["mpc", "play"])

def stop():
    subprocess.run(["mpc", "stop"])

def toggle():
    subprocess.run(["mpc", "toggle"])

def volume_up():
    subprocess.run(["mpc", "volume", "+5"])

def volume_down():
    subprocess.run(["mpc", "volume", "-5"])

def set_volume(volume):
    subprocess.run(
        ["mpc", "volume", str(volume)]
    )

def status():
    subprocess.run(["mpc"])
    
