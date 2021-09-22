import subprocess
def run(cmd):
    completed = subprocess.run("powershell "+cmd, shell=True,  text=True, input="y")
    return completed


if __name__ == '__main__':
    convert = " C:\\ffmpeg\\bin\\ffmpeg.exe -i .\_PrSxoMJPL8 test.mp3"
    convert_result = run(convert)
    """if convert_result.returncode != 0:
        print("An error occured: %s", convert_result.stderr)
    else:
        print("Hello command executed successfully!")"""

