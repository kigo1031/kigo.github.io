#!/usr/bin/env python3
"""
더 나은 파비콘을 생성하는 스크립트
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_favicon():
    # 32x32 크기의 이미지 생성
    img = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 배경 사각형 그리기 (둥근 모서리 흉내)
    draw.rounded_rectangle([1, 1, 30, 30], radius=6, fill=(255, 255, 255, 255), outline=(229, 231, 235, 255), width=1)

    # K 문자 그리기 (더 굵게)
    # K의 세로선
    draw.rectangle([8, 6, 10, 25], fill=(0, 0, 0, 255))

    # K의 위쪽 대각선
    points = [(10, 6), (18, 6), (18, 8), (12, 14), (10, 14)]
    draw.polygon(points, fill=(0, 0, 0, 255))

    # K의 아래쪽 대각선
    points = [(10, 17), (12, 17), (18, 25), (18, 27), (14, 27), (10, 20)]
    draw.polygon(points, fill=(0, 0, 0, 255))

    # 여러 크기로 저장
    sizes = [16, 32, 48, 96, 144, 256]

    for size in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'static/images/favicon-{size}.png', 'PNG')

    # 기본 favicon.png (32x32)
    img.save('static/images/favicon.png', 'PNG')

    # favicon.ico 생성 (여러 크기 포함)
    ico_sizes = [(16, 16), (32, 32), (48, 48)]
    ico_images = []
    for size in ico_sizes:
        ico_img = img.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(ico_img)

    ico_images[0].save('static/images/favicon.ico', format='ICO', sizes=ico_sizes)

    print("파비콘 생성 완료!")
    print("생성된 파일들:")
    for size in sizes:
        print(f"- favicon-{size}.png")
    print("- favicon.png")
    print("- favicon.ico")

if __name__ == "__main__":
    create_favicon()
