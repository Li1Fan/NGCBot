import os
from concurrent.futures import ThreadPoolExecutor

from PIL import Image


def process_frame(frame_path, is_jpg, quality):
    """处理单帧图像并返回处理后的图像"""
    with Image.open(frame_path) as frame:
        if is_jpg:
            compress_png2jpg(frame_path, quality=quality)
        return frame


def gif2png(input_gif_path, output_folder, is_jpg=False, quality=100):
    with Image.open(input_gif_path) as img:
        os.makedirs(output_folder, exist_ok=True)
        # 清空输出文件夹
        for f in os.listdir(output_folder):
            os.remove(os.path.join(output_folder, f))

        num_frames = img.n_frames
        print(f"Total frames: {num_frames}")
        frame_durations = []

        # 使用线程池处理帧
        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(num_frames):
                img.seek(i)
                duration = img.info.get('duration', 100)
                # print(f"Frame {i:03d} duration: {duration} ms")
                frame_durations.append(duration)

                frame_filename = os.path.join(output_folder, f"frame_{i:03d}.png")
                img.save(frame_filename, format="PNG")
                futures.append(executor.submit(process_frame, frame_filename, is_jpg, quality))

            # 等待所有线程完成
            processed_frames = [future.result() for future in futures]

        return output_folder, int(frame_durations[0])


def png2gif(input_folder, output_gif_path, duration_ms=100, step=1, is_delete_last=False, is_jpg=False):
    if is_jpg:
        png_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.jpg')])
    else:
        png_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])

    if step < 1:
        raise ValueError("step must be at least 1")

    images = []
    if is_delete_last:
        png_files = png_files[:len(png_files) // step]
        step = 1
    # 遍历 PNG 文件并选择图像
    for i in range(0, len(png_files), step):
        frame_path = os.path.join(input_folder, png_files[i])
        frame = Image.open(frame_path)
        # 处理透明部分
        frame = frame.convert("RGBA")  # 转换为 RGBA 模式
        background = Image.new("RGBA", frame.size, (255, 255, 255, 255))  # 创建白色背景
        frame = Image.alpha_composite(background, frame)  # 合成图像
        images.append(frame)

    if not images:
        raise ValueError("No images to save")

    images[0].save(output_gif_path, save_all=True, append_images=images[1:], duration=duration_ms, loop=0)
    return output_gif_path


def gif_minimize(input_gif_path, output_gif_path, step=1, is_delete_last=False, is_jpg=True, quality=75):
    try:
        output_folder, frame_duration = gif2png(input_gif_path, 'output_frames', is_jpg=is_jpg, quality=quality)
        return png2gif(output_folder, output_gif_path, frame_duration, step, is_delete_last, is_jpg=is_jpg)
    except Exception as e:
        print(f"Error: {e}")
        return None


def jpg2gif(input_jpg_path, output_gif_path, duration_ms=100):
    with Image.open(input_jpg_path) as img:
        img.save(output_gif_path, format='GIF', duration=duration_ms, loop=0)
    return output_gif_path


def compress_png2jpg(input_path, output_path=None, quality=100):
    if output_path is None:
        output_path = input_path.replace('.png', '.jpg')

    with Image.open(input_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path, quality=quality)


if __name__ == "__main__":
    # jpg2gif(r'help.jpg', r'help.gif', 40)
    # gif_minimize(r'/home/frz/github/NGCBot/Meme_Cache/1_confuse.gif',
    #              r'/home/frz/github/NGCBot/Meme_Cache/1_confuse_1.gif', 1, is_delete_last=False, is_jpg=True,
    #              quality=35)
    gif2png(r'/home/frz/ftp/Prj/yaobai.gif', r'/home/frz/robot/Test_demo/Meme_Cache/1',)