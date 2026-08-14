#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按帧边界解压 zstd 拼接帧存档。

zstd 拼接帧（concatenated frames）格式：多个独立的 zstd 帧首尾相连，
每帧以 magic 0xFD2FB528 开头。此处逐帧独立解压后拼接，避免依赖
单一工具对拼接帧的隐式处理。

用法: python3 decompress_session.py <input.zstd> <output.jsonl>
"""
import sys
import struct
import zstandard

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def find_frame_boundaries(data: bytes):
    """扫描拼接帧的字节边界（每帧起点与终点偏移）。"""
    boundaries = []  # (start, end) 帧区间列表
    pos = 0
    n = len(data)
    while pos < n:
        if data[pos:pos + 4] != ZSTD_MAGIC:
            raise ValueError(f"offset {pos}: 未找到 zstd magic 0xFD2FB528")
        # 解析帧头以确定各字段长度，从而定位帧尾
        hdr = data[pos + 4]
        fcs_flag = (hdr >> 6) & 0x3      # Frame_Content_Size flag
        single_seg = (hdr >> 5) & 0x1    # Single_Segment flag
        dict_flag = hdr & 0x3            # Dictionary_ID flag
        off = pos + 5
        if not single_seg:
            # Window_Descriptor: 1 字节
            off += 1
        # Dictionary_ID: 0/1/2/4 字节
        off += {0: 0, 1: 1, 2: 2, 3: 4}[dict_flag]
        # Frame_Content_Size:
        #   flag==0: 无（或 single_seg 时 1 字节）
        #   flag==1: 2 字节, flag==2: 4 字节, flag==3: 8 字节
        if fcs_flag == 0 and single_seg:
            off += 1
        elif fcs_flag == 1:
            off += 2
        elif fcs_flag == 2:
            off += 4
        elif fcs_flag == 3:
            off += 8
        # 顺序读取数据块直到 last_block 置位
        while True:
            bh = data[off:off + 3]
            if len(bh) < 3:
                raise ValueError(f"offset {off}: 块头不完整")
            block_hdr = bh[0] | (bh[1] << 8) | (bh[2] << 16)
            last_block = block_hdr & 0x1
            block_size = block_hdr >> 3
            off += 3 + block_size
            if off > n:
                raise ValueError(f"offset {off}: 数据块超出文件末尾")
            if last_block:
                break
        # 帧尾可能带 4 字节校验和
        end = off
        if end + 4 <= n and not data[end:end + 4].startswith(ZSTD_MAGIC):
            end += 4  # 保守处理：若帧尾非 magic，则按校验和存在处理
        boundaries.append((pos, end))
        pos = end
    return boundaries


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, "rb") as f:
        data = f.read()
    frames = find_frame_boundaries(data)
    print(f"共发现 {len(frames)} 个 zstd 帧", file=sys.stderr)
    dctx = zstandard.ZstdDecompressor()
    parts = []
    for i, (s, e) in enumerate(frames):
        frame = data[s:e]
        try:
            parts.append(dctx.decompress(frame, max_output_size=2**31 - 1))
        except Exception as ex:  # 帧尾校验和按保守处理可能多读 4 字节，尝试裁剪
            frame = data[s:e - 4] if e - s > 4 else frame
            parts.append(dctx.decompress(frame, max_output_size=2**31 - 1))
        print(f"  帧 {i + 1}: bytes={e - s}", file=sys.stderr)
    out = b"".join(parts)
    with open(dst, "wb") as f:
        f.write(out)
    print(f"解压完成: {len(data)} bytes -> {len(out)} bytes, 输出 {dst}", file=sys.stderr)


if __name__ == "__main__":
    main()
