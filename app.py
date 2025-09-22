import streamlit as st
from openai import OpenAI
from supabase import create_client, Client
import os

# 加载 CSS 优化聊天界面和侧边栏
st.markdown(
    """
    <style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        cursor: default;
    }
    .stChatMessage.user {
        background-color: #e6f3ff;
    }
    .stChatMessage.assistant {
        background-color: #f0f0f0;
    }
    .stSidebar {
        width: 250px !important;
    }
    .conversation-button {
        display: block;
        width: 100%;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: #f0f0f0;
        border: none;
        text-align: left;
        cursor: pointer;
        font-size: 16px;
        transition: background-color 0.2s;
    }
    .conversation-button:hover {
        background-color: #e0e0e0;
    }
    .conversation-button.active {
        background-color: #007bff;
        color: white;
    }
    [data-testid="stTextInput"] {
        cursor: pointer;
    }
    .stMarkdown {
        user-select: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# 初始化 Supabase 客户端
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)

# 中文系统提示词（可替换为你的提示词）
system_prompt = st.secrets["SYSTEM_PROMPT"]

# 保存消息到 Supabase
def save_message(conv_id, role, content):
    try:
        data = {"conv_id": conv_id, "role": role, "content": content}
        response = supabase.table("conversations").insert(data).execute()
        if response.data:
            st.cache_data.clear()
    except Exception as e:
        st.error(f"保存消息失败：{str(e)}")

# 加载对话历史
@st.cache_data
def load_conversation(conv_id):
    try:
        response = supabase.table("conversations").select("role, content").eq("conv_id", conv_id).order("timestamp").execute()
        messages = [{"role": "system", "content": system_prompt}]
        for item in response.data:
            messages.append({"role": item["role"], "content": item["content"]})
        return messages
    except Exception as e:
        st.error(f"加载对话失败：{str(e)}")
        return [{"role": "system", "content": system_prompt}]

# 获取所有对话 ID
@st.cache_data
def get_conversation_ids():
    try:
        response = supabase.table("conversations").select("conv_id", distinct=True).execute()
        conv_ids = [item["conv_id"] for item in response.data]
        return conv_ids if conv_ids else ["对话 1"]
    except Exception as e:
        st.error(f"获取对话列表失败：{str(e)}")
        return ["对话 1"]

# 初始化会话状态
if "conversations" not in st.session_state:
    st.session_state.conversations = {
        "对话 1": load_conversation("对话 1")
    }
if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = "对话 1"

# 侧边栏：对话管理
with st.sidebar:
    st.header("对话列表")
    conversation_names = get_conversation_ids()
    if not conversation_names:
        conversation_names = ["对话 1"]
    
    # 垂直排列的会话按钮
    for conv_name in conversation_names:
        is_active = conv_name == st.session_state.current_conversation
        button_style = "conversation-button active" if is_active else "conversation-button"
        st.markdown(
            f'<button class="{button_style}" onclick="this.blur()">{conv_name}</button>',
            unsafe_allow_html=True
        )
        if st.button(" ", key=f"conv_{conv_name}", on_click=lambda c=conv_name: setattr(st.session_state, "current_conversation", c)):
            pass

    # 新建对话
    if st.button("新建对话", key="new_conversation"):
        new_conversation = f"对话 {len(conversation_names) + 1}"
        st.session_state.conversations[new_conversation] = [{"role": "system", "content": system_prompt}]
        st.session_state.current_conversation = new_conversation
        st.rerun()

    # 删除当前对话
    if len(conversation_names) > 1:
        if st.button("删除当前对话", key="delete_conversation"):
            try:
                supabase.table("conversations").delete().eq("conv_id", st.session_state.current_conversation).execute()
                del st.session_state.conversations[st.session_state.current_conversation]
                st.session_state.current_conversation = get_conversation_ids()[0] if get_conversation_ids() else "对话 1"
                st.rerun()
            except Exception as e:
                st.error(f"删除对话失败：{str(e)}")

    # 重命名当前对话
    new_name = st.text_input("重命名当前对话", value=st.session_state.current_conversation, key="rename_conversation")
    if new_name != st.session_state.current_conversation and new_name and new_name not in conversation_names:
        try:
            # 先删除旧 ID 的记录，再插入新 ID 的记录（模拟更新主键）
            supabase.table("conversations").delete().eq("conv_id", st.session_state.current_conversation).execute()
            # 重新插入所有消息（从内存中）
            for msg in st.session_state.conversations[st.session_state.current_conversation]:
                if msg["role"] != "system":  # 系统提示不存入
                    save_message(new_name, msg["role"], msg["content"])
            st.session_state.conversations[new_name] = st.session_state.conversations.pop(st.session_state.current_conversation)
            st.session_state.current_conversation = new_name
            st.rerun()
        except Exception as e:
            st.error(f"重命名对话失败：{str(e)}")

# 主界面
st.title("DeepSeek AI 聊天")

# 导出/导入对话历史
with st.container():
    col_export, col_import = st.columns(2)
    with col_export:
        chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversations[st.session_state.current_conversation][1:]])
        st.download_button("导出当前对话", chat_history, file_name=f"{st.session_state.current_conversation}.txt")
    with col_import:
        uploaded_file = st.file_uploader("导入对话历史", type=["txt"])
        if uploaded_file:
            try:
                content = uploaded_file.read().decode("utf-8")
                messages = [{"role": "system", "content": system_prompt}]
                for line in content.split("\n"):
                    if line.startswith("user:"):
                        user_content = line[5:].strip()
                        messages.append({"role": "user", "content": user_content})
                        save_message(st.session_state.current_conversation, "user", user_content)
                    elif line.startswith("assistant:"):
                        assistant_content = line[10:].strip()
                        messages.append({"role": "assistant", "content": assistant_content})
                        save_message(st.session_state.current_conversation, "assistant", assistant_content)
                st.session_state.conversations[st.session_state.current_conversation] = messages
                st.rerun()
            except Exception as e:
                st.error(f"导入对话失败：{str(e)}")

# 显示当前对话的聊天历史
chat_container = st.container()
with chat_container:
    for message in st.session_state.conversations[st.session_state.current_conversation][1:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 用户输入
if user_input := st.chat_input("请输入你的消息...", key="chat_input"):
    st.session_state.conversations[st.session_state.current_conversation].append({"role": "user", "content": user_input})
    save_message(st.session_state.current_conversation, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 流式响应
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("正在思考... ⏳")
        full_response = ""
        try:
            for chunk in client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.conversations[st.session_state.current_conversation],
                stream=True
            ):
                content = chunk.choices[0].delta.content or ""
                full_response += content
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            if "401" in str(e):
                message_placeholder.error("API 密钥无效，请检查 DeepSeek API 密钥。")
            elif "network" in str(e).lower():
                message_placeholder.error("网络错误，请检查校园网络或使用 VPN。")
            elif "token" in str(e).lower():
                message_placeholder.error("API token 额度不足，请检查 DeepSeek 平台。")
            else:
                message_placeholder.error(f"错误：{str(e)}")
        st.session_state.conversations[st.session_state.current_conversation].append({"role": "assistant", "content": full_response})
        save_message(st.session_state.current_conversation, "assistant", full_response)

