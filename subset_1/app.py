import streamlit as st
import pandas as pd
import os
import glob

# ====== 文件路径设置 ====== #
CSV_PATH = os.path.join(os.path.dirname(__file__), "music_image_combined.csv")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
IMAGE_DIR = os.path.join(os.path.dirname(__file__), "image")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "final_annotations.csv")

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
st.title("🎵 音乐-图像 匹配标注")

# ====== 项目说明 ====== #
st.markdown(
    """
    <div style='background-color:#f0f2f6; padding: 20px; border-radius: 10px;'>
        <h3>📘 使用说明</h3>
        <ul>
            <li>🔊 每页播放一首音乐，下面显示多张候选图像。</li>
            <li>✅ 对每张图像选择是否与音乐意境相符：“是”、“否” 或 “中性”（不想选就保留中性就行）。</li>
            <li>💾 每次点击“保存当前页标注”按钮将保存当前结果（不保存不会被记录）。</li>
            <li>➡️ 通过“上一首 / 下一首”按钮浏览其他音乐。</li>
            <li>📥 最后点击底部“下载全部标注为 CSV 文件”按钮获取所有的标注记录，发送给我，谢谢。</li>
            <li> 能力有限，麻烦翻页后手动滑到顶部播放音乐。</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True
)

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
                    st.image(img_path, use_container_width=True, caption=img_id)  # ✅ 替换为 use_container_width
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

# 初始化保存状态（仅首次）
if "saved_rows" not in st.session_state:
    st.session_state.saved_rows = []
    st.session_state.annotated = set()

with col1:
    if st.button("⬅️ 上一首") and st.session_state.page_index > 0:
        st.session_state.page_index -= 1
        st.rerun()

with col2:
    if st.button("➡️ 下一首") and st.session_state.page_index < len(df) - 1:
        st.session_state.page_index += 1
        st.rerun()

with col3:
    if st.button("✅ 保存当前页标注（翻页前要按一下）"):
        for r in all_rows:
            if (r['song_id'], r['image_id']) not in st.session_state.annotated:
                st.session_state.saved_rows.append(r)
                st.session_state.annotated.add((r['song_id'], r['image_id']))
        st.success("✅ 当前页标注已保存")

# ====== 下载按钮区 ====== #
st.markdown("### 📦 下载全部标注结果")

if st.session_state.saved_rows:
    df_export = pd.DataFrame(st.session_state.saved_rows)
    csv_data = df_export.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="📥 下载全部标注为 CSV 文件",
        data=csv_data,
        file_name="final_annotations.csv",
        mime="text/csv"
    )
else:
    st.info("⚠️ 当前尚未保存任何标注，请先开始标注并保存")