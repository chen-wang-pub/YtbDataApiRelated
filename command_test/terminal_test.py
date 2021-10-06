import os
temp_dir_loc = os.path.dirname(__file__)
print(temp_dir_loc)
ffmpeg_path = 'ffmpeg-static/ffmpeg'
ffmpeg_real_path = os.path.join(temp_dir_loc, ffmpeg_path)
print(ffmpeg_real_path)
source_file = 'WAQIv2IP0bM'
output_file = 'test.mp3'
convert_command = '{} -i {} {} -y'.format(ffmpeg_real_path, source_file, output_file)

os.system(convert_command)