import streamlit as st
import pandas as pd
import os
import glob

# ====== 文件路径设置 ====== #
CSV_PATH = "music_image_combined.csv"
AUDIO_DIR = "audio"
IMAGE_DIR = "image"
OUTPUT_CSV = "final_annotations.csv"

# ====== 加载数据 ====== #
df = pd.read_csv(CSV_PATH)

# ====== 恢复历史标注（如有） ====== #
if os.path.exists(OUTPUT_CSV):
    old_df = pd.read_csv(OUTPUT_CSV)
    annotated = set(zip(old_df['song_id'], old_df['image_id']))
    saved_rows = old_df.to_dict("records")
else:
    annotated = set()
    saved_rows = []

# ====== 页面配置 ====== #
st.set_page_config(layout="wide")
st.title("🎵 音乐-图像 匹配标注工具（三分类）")

# ====== 读取音频路径 ====== #
def find_audio(song_id):
    for file in glob.glob(f"{AUDIO_DIR}/**/{song_id}.mp3", recursive=True):
        return file
    return None

# ====== 渲染图像列 ====== #
def render_image_columns(song_id, row, col_names, group_label, section_title):
    st.subheader(section_title)
    rows = []
    cols_per_row = 5
    image_data = []

    for col in col_names:
        if col in row and pd.notna(row[col]):
            image_data.append((col, row[col]))

    for row_start in range(0, len(image_data), cols_per_row):
        cols = st.columns(cols_per_row)
        for col_idx, (col, img_id) in enumerate(image_data[row_start:row_start + cols_per_row]):
            img_path = os.path.join(IMAGE_DIR, img_id)
            with cols[col_idx]:
                if os.path.exists(img_path):
                    st.image(img_path, use_column_width=True, caption=img_id)
                    key_base = f"{song_id}_{col}"
                    selected_label = st.radio(
                        "",
                        ["中性", "是", "否"],
                        key=key_base,
                        horizontal=True,
                        index=0,
                        label_visibility="collapsed"
                    )
                    st.markdown(
                        f"<style>div[data-baseweb='radio'] label span {{ font-size: 18px !important; }}</style>",
                        unsafe_allow_html=True
                    )
                    if selected_label != "中性":
                        rows.append({
                            "song_id": song_id,
                            "image_id": img_id,
                            "group": group_label,
                            "label": selected_label
                        })
                else:
                    st.error(f"图像缺失: {img_id}")
    return rows

# ====== 分页状态初始化 ====== #
if "page_index" not in st.session_state:
    st.session_state.page_index = 0

idx = st.session_state.page_index
row = df.iloc[idx]
song_id = row['song_id']

# ====== 音频播放区 ====== #
st.header(f"{idx+1}. 🎶 歌曲: {song_id}")
audio_file = find_audio(song_id)
if audio_file:
    st.audio(audio_file)
else:
    st.warning(f"未找到音频文件: {song_id}.mp3")

# ====== 标注图像区域 ====== #
all_rows = []

# 正样本列
positive_cols = [col for col in df.columns if col.startswith("match_img") and col.endswith("_x")]
all_rows += render_image_columns(song_id, row, positive_cols, group_label="positive", section_title="🎯 与音乐感觉相符的图像")

# 负样本列
negative_cols = [col for col in df.columns if col.startswith("match_img") and col.endswith("_y")]
all_rows += render_image_columns(song_id, row, negative_cols, group_label="negative", section_title="🚫 与音乐感觉相悖的图像")

# 城市图像列
city_cols = [col for col in df.columns if col.startswith("city_day_img") or col.startswith("city_night_img")]
all_rows += render_image_columns(song_id, row, city_cols, group_label="city", section_title="🏙️ 城市图像是否契合音乐意境")

# ====== 页脚按钮区 ====== #
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("⬅️ 上一首") and st.session_state.page_index > 0:
        st.session_state.page_index -= 1
        st.experimental_rerun()
with col2:
    if st.button("➡️ 下一首") and st.session_state.page_index < len(df) - 1:
        st.session_state.page_index += 1
        st.experimental_rerun()
with col3:
    if st.button("✅ 保存当前页标注（翻页前要按一下）"):
        for r in all_rows:
            if (r['song_id'], r['image_id']) not in annotated:
                saved_rows.append(r)
                annotated.add((r['song_id'], r['image_id']))
        pd.DataFrame(saved_rows).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        st.success(f"✅ 已保存至本地文件：{OUTPUT_CSV}")