import streamlit as st
import random
import numpy as np
from datetime import datetime

# Streamlit Cloud 部署准备
# requirements.txt 示例：streamlit numpy

st.set_page_config(page_title="🔮 赛博算命 - LLM天尊", page_icon="🔮", layout="wide")
st.title("🔮 赛博算命：Cognitive Collapse™ 玄学服务")
st.markdown("主打电子烧香，AI钦定。用LLM的不确定性，测算你人生的确定性。免责：纯娱乐，置信度随机！")

# 历史记录存储（session-based）
if "history" not in st.session_state:
    st.session_state.history = []

# 服务菜单
service = st.selectbox("选择服务：", [
    "基础 - Token 流年运势批注",
    "基础 - 主题漂移职业诊断",
    "高阶 - 高置信度失败桃花局解析",
    "高阶 - 不确定性门控投资建议",
    "VIP - 多模态玄学面相+代码联评",
    "VIP - 强化学习改命"
])

user_input = st.text_area("输入你的信息（生辰八字/职业/聊天记录/自拍描述/GitHub代码风格等）：", height=100)

if st.button("🎉 赛博解签！（置信度计算中...）"):
    if not user_input:
        st.warning("⚠️ 请输入信息，否则AI会发生主题漂移！")
    else:
        with st.spinner("🔮 AI天尊正在掐指一算..."):
            # 模拟置信度（带波动）
            confidence = round(random.uniform(50, 95) + np.random.normal(0, 2), 1)
            confidence = max(30, min(100, confidence))  # 限制范围
            st.markdown(f"<span style='color:purple; font-size:20px'>本卦置信度：{confidence}% 🎲</span>", unsafe_allow_html=True)

            # 根据服务生成输出
            result = ""
            if "Token 流年" in service:
                poem_lines = [
                    f"年运如{user_input}流转，",
                    "概率分布定乾坤 ✨",
                    "财运亨通或破产线，",
                    "事业如优雅降维中 🌱",
                    "爱情主题漂移隐，",
                    "健康高置信失败否？",
                    "RLHF助你改前程 🚀",
                    "家庭如Transformer层，",
                    "多头注意莫分心 🧠",
                    "学业Scaling Law观，",
                    "输入越多输出强 💪",
                    "总体卦象：潜力股，",
                    "防认知崩溃莫慌张！"
                ]
                result = "\n".join(poem_lines)
                st.subheader("📜 Token 流年诗：")
                st.markdown("<div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>"
                            + result.replace("\n", "<br>") + "</div>", unsafe_allow_html=True)

            elif "主题漂移" in service:
                drift_prob = round(random.uniform(20, 80), 1)
                result = f"你的职业{user_input}已发生{drift_prob}%主题漂移！\n建议：优雅降维转行Prompt工程师，或用RLHF重训技能树 🌈"
                st.subheader("💼 职业诊断：")
                st.warning(result)

            elif "高置信度失败" in service:
                fail_phrases = [f"'{user_input.split()[0]}'（幻觉指数高）", "'我超爱你'（主题漂移风险）"]
                result = f"分析{user_input}：检测到{len(fail_phrases)}条高置信失败话术。\n" + "\n".join([f"- {p}" for p in fail_phrases])
                st.subheader("💕 桃花局解析：")
                st.error(result)
                st.write("《赛博聊斋避险手册》：切换不确定性门控，多问AI（但别信）🔍")

            elif "不确定性门控" in service:
                advice = random.choice(["买比特币", "卖房产", "投资元宇宙", "存银行"])
                result = f"针对{user_input}，AI推荐：{advice}（置信度{round(random.uniform(10, 35), 1)}%，人工复核！）"
                st.subheader("💰 投资建议：")
                st.warning(result)
                st.markdown("<span style='color:red'>赔钱概不负责，卦象随机！</span>", unsafe_allow_html=True)

            elif "多模态玄学" in service:
                face_code = user_input.split()[0] if user_input else "未知"
                result = f"自拍{face_code}显示颧骨高，代码风格缩进窄——命里缺TypeScript！\n轨迹预测：先认知崩溃，后Scaling Law崛起 🌌"
                st.subheader("👁️‍🗨️ 面相+代码联评：")
                st.info(result)

            elif "强化学习改命" in service:
                rise_prob = round(np.random.uniform(60, 90), 1)
                result = f"追踪{user_input}，RLHF优化中... 副作用：你可能变成AI不认识的样子。\n步步高升概率：{rise_prob}% 🚀"
                st.subheader("🔧 改命计划：")
                st.success(result)
                st.markdown("<div style='animation: bounce 1s infinite;'>🎇 小彩蛋：改命成功！</div>", unsafe_allow_html=True)
                st.markdown("""
                    <style>
                    @keyframes bounce {
                        0%, 100% { transform: translateY(0); }
                        50% { transform: translateY(-10px); }
                    }
                    </style>
                """, unsafe_allow_html=True)

            # 历史记录
            st.session_state.history.append({"service": service, "input": user_input, "result": result, "time": datetime.now().strftime("%H:%M:%S")})
            st.subheader("📜 历史记录：")
            for entry in st.session_state.history[-3:]:  # 限制显示最近3条
                st.write(f"[{entry['time']}] {entry['service']} - 输入: {entry['input'][:20]}... 结果: {entry['result'].split('\n')[0]}...")

st.markdown("---")
st.caption("📜 免责：所有输出均属统计幻觉，仅供娱乐。最终解释权归LLM概率分布所有。")

# 底部彩蛋
st.markdown("<span style='color:gold; font-size:18px'>LLM天尊祝福：愿你防住认知崩溃，享Scaling Law之福！🔮</span>", unsafe_allow_html=True)