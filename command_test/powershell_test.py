import subprocess
def run(source_file, result_file):
    command = "powershell C:\\ffmpeg\\bin\\ffmpeg.exe -i {} {}".format(source_file, result_file)
    completed = subprocess.run(command, capture_output=True, shell=True,  text=True, input="y")
    return completed.returncode


if __name__ == '__main__':
    convert = " C:\\ffmpeg\\bin\\ffmpeg.exe -i .\_PrSxoMJPL8 test.mp3"
    source = ".\_PrSxoMJPL8"
    result = r".\test.mp3"
    return_code = run(source, result)
    print(return_code)
    """if convert_result.returncode != 0:
        print("An error occured: %s", convert_result.stderr)
    else:
        print("Hello command executed successfully!")"""

