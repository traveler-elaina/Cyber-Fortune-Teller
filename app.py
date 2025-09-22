import streamlit as st
from openai import OpenAI

# 初始化DeepSeek客户端（兼容OpenAI格式）
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# 你的系统提示词（替换为你的实际提示）
system_prompt = "You are a helpful AI assistant. Respond concisely and accurately."

# 初始化会话状态，存储消息历史（包括系统提示）
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# 页面标题
st.title("DeepSeek AI Chat")

# 显示聊天历史（跳过系统提示）
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入框
if user_input := st.chat_input("Type your message here..."):
    # 添加用户消息到历史
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)

    # 显示助手响应（流式）
    with st.chat_message("assistant"):
        message_placeholder = st.empty()  # 占位符，用于更新响应
        full_response = ""

        # 调用DeepSeek API，启用流式响应
        for chunk in client.chat.completions.create(
                model="deepseek-chat",  # 或替换为你的模型，如 "deepseek-coder"
                messages=st.session_state.messages,
                stream=True
        ):
            # 累积响应内容
            content = chunk.choices[0].delta.content or ""
            full_response += content
            # 实时更新显示（添加光标效果）
            message_placeholder.markdown(full_response + "▌")

        # 最终更新（移除光标）
        message_placeholder.markdown(full_response)

    # 添加助手消息到历史
    st.session_state.messages.append({"role": "assistant", "content": full_response})