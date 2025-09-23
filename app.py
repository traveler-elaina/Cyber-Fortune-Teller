import streamlit as st
from openai import OpenAI
from supabase import create_client, Client

# 加载 CSS 优化聊天界面和侧边栏
st.markdown(
    """
    <style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        cursor: default;
        user-select: text; /* 允许复制 */
    }
    .stChatMessage.user {
        background-color: #e6f3ff;
    }
    .stChatMessage.assistant {
        background-color: #f0f0f0;
    }
    .stSidebar {
        width: 250px !important;
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        padding: 10px;
        margin: 2px 0;
        border-radius: 8px;
        background-color: #ffffff;
        border: 1px solid #ddd;
        text-align: left;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s;
        white-space: pre-wrap;
    }
    .stButton>button:hover {
        background-color: #f0f0f0;
        border-color: #ccc;
    }
    .stButton[data-baseweb="button"] button[title*="对话"] {
        background-color: #007bff;
        color: white;
        border-color: #0056b3;
    }
    [data-testid="stTextInput"], [data-testid="stSelectbox"] {
        cursor: pointer;
    }
    .conversation-item {
        padding: 5px;
        margin: 2px 0;
        border-radius: 8px;
        background-color: #ffffff;
        border: 1px solid #ddd;
        cursor: pointer;
    }
    .conversation-item:hover {
        background-color: #f0f0f0;
        border-color: #ccc;
    }
    .conversation-preview {
        font-size: 12px;
        color: #666;
        margin-top: 2px;
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

# 从 Secrets 读取提示词
system_prompt = st.secrets["SYSTEM_PROMPT"]

# 保存消息到 Supabase
@st.cache_data
def save_message(conv_id, role, content):
    try:
        data = {"conv_id": conv_id, "role": role, "content": content}
        response = supabase.table("conversations").insert(data).execute()
        if response.data:
            load_conversation.clear(conv_id=conv_id)
            get_preview.clear(conv_id=conv_id)
        return True
    except Exception as e:
        st.error(f"保存消息失败：{str(e)}")
        return False

# 加载对话历史
@st.cache_data
def load_conversation(conv_id, _cache_key=None):
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
        response = supabase.table("conversations").select("conv_id").execute()
        conv_ids = list(set(item["conv_id"] for item in response.data))
        return conv_ids if conv_ids else ["对话 1"]
    except Exception as e:
        st.error(f"获取对话列表失败：{str(e)}")
        return ["对话 1"]

# 获取最新消息预览
@st.cache_data
def get_preview(conv_id):
    try:
        response = supabase.table("conversations").select("content").eq("conv_id", conv_id).order("timestamp", desc=True).limit(1).execute()
        return response.data[0]["content"][:50] + "..." if response.data else "无消息"
    except Exception:
        return "无消息"

# 初始化会话状态
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "current_conversation" not in st.session_state or st.session_state.current_conversation not in st.session_state.conversations:
    st.session_state.current_conversation = "对话 1"
    st.session_state.conversations["对话 1"] = load_conversation("对话 1")

# 侧边栏：对话管理
with st.sidebar:
    st.header("对话列表")
    conversation_names = get_conversation_ids()
    if not conversation_names:
        conversation_names = ["对话 1"]

    # 动态加载对话
    for conv_name in conversation_names:
        if conv_name not in st.session_state.conversations:
            st.session_state.conversations[conv_name] = load_conversation(conv_name)

    # 同步当前对话
    if st.session_state.current_conversation not in conversation_names:
        st.session_state.current_conversation = conversation_names[0]

    # 垂直排列的会话项
    for conv_name in conversation_names:
        is_active = conv_name == st.session_state.current_conversation
        preview = get_preview(conv_name)
        with st.container():
            # 使用 button 显示对话名称，保持点击功能
            if st.button(
                conv_name,
                key=f"conv_{conv_name}",
                on_click=lambda c=conv_name: setattr(st.session_state, "current_conversation", c),
                help=f"切换到 {conv_name}",
                disabled=is_active  # 禁用当前选中的对话按钮
            ):
                st.session_state.current_conversation = conv_name
            # 使用 markdown 显示预览文本，支持样式
            st.markdown(
                f"<div class='conversation-preview'>{preview}</div>",
                unsafe_allow_html=True
            )

    # 新建对话
    def create_new_conversation():
        conversation_names = get_conversation_ids()
        new_id = "对话 1"
        try:
            conv_numbers = [
                int(c.split(' ')[1])
                for c in conversation_names
                if c.startswith('对话') and len(c.split(' ')) > 1 and c.split(' ')[1].isdigit()
            ]
            new_id = f"对话 {max(conv_numbers + [0]) + 1}"
        except Exception:
            pass
        st.session_state.current_conversation = new_id
        st.session_state.conversations[new_id] = [{"role": "system", "content": system_prompt}]
        save_message(new_id, "system", system_prompt)
        st.rerun()

    if st.button("新建对话", key="new_conversation", on_click=create_new_conversation):
        pass

    # 删除当前对话
    def delete_conversation():
        try:
            current_conv = st.session_state.current_conversation
            supabase.table("conversations").delete().eq("conv_id", current_conv).execute()
            st.session_state.conversations.pop(current_conv, None)
            new_convs = get_conversation_ids()
            new_conv = new_convs[0] if new_convs else "对话 1"
            if new_conv not in st.session_state.conversations:
                st.session_state.conversations[new_conv] = [{"role": "system", "content": system_prompt}]
                save_message(new_conv, "system", system_prompt)
            st.session_state.current_conversation = new_conv
            st.rerun()
        except Exception as e:
            st.error(f"删除对话失败：{e}")

    if len(conversation_names) > 1:
        if st.button("删除当前对话", key="delete_conversation", on_click=delete_conversation):
            pass

    # 重命名当前对话
    def rename_conversation(new_name):
        try:
            supabase.table("conversations").update({"conv_id": new_name}).eq("conv_id", st.session_state.current_conversation).execute()
            st.session_state.conversations[new_name] = st.session_state.conversations.pop(st.session_state.current_conversation)
            st.session_state.current_conversation = new_name
            st.rerun()
        except Exception as e:
            st.error(f"重命名对话失败：{str(e)}")

    new_name = st.text_input("重命名当前对话", value=st.session_state.current_conversation, key="rename_conversation")
    if new_name != st.session_state.current_conversation and new_name and new_name not in conversation_names:
        st.button("确认重命名", key="confirm_rename", on_click=lambda: rename_conversation(new_name))

# 主界面
st.title("DeepSeek AI 聊天")

# 导出/导入对话历史
with st.container():
    col_export, col_import = st.columns(2)
    with col_export:
        current_conv = st.session_state.current_conversation
        if current_conv in st.session_state.conversations and st.session_state.conversations[current_conv]:
            chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversations[current_conv][1:]])
            st.download_button("导出当前对话", chat_history, file_name=f"{current_conv}.txt")
        else:
            st.warning("当前对话为空或不存在，无法导出！")
    with col_import:
        uploaded_file = st.file_uploader("导入对话历史", type=["txt"])
        if uploaded_file:
            try:
                content = uploaded_file.read().decode("utf-8")
                messages = [{"role": "system", "content": system_prompt}]
                for line in content.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    if not (line.startswith("user:") or line.startswith("assistant:")):
                        st.error(f"无效的行格式：{line}")
                        continue
                    role, content = line.split(":", 1)
                    role = role.strip()
                    content = content.strip()
                    if role == "user":
                        messages.append({"role": "user", "content": content})
                        save_message(st.session_state.current_conversation, "user", content)
                    elif role == "assistant":
                        messages.append({"role": "assistant", "content": content})
                        save_message(st.session_state.current_conversation, "assistant", content)
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
    if save_message(st.session_state.current_conversation, "user", user_input):
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
                error_message = str(e).lower()
                if "401" in error_message:
                    message_placeholder.error("API 密钥无效，请检查 DeepSeek API 密钥。")
                elif "network" in error_message:
                    message_placeholder.error("网络错误，请检查网络连接或使用 VPN。")
                elif "token" in error_message:
                    message_placeholder.error("API token 额度不足，请检查 DeepSeek 平台。")
                elif "rate_limit" in error_message:
                    message_placeholder.error("API 请求超限，请稍后重试。")
                else:
                    message_placeholder.error(f"未知错误：{str(e)}")
            if full_response:
                st.session_state.conversations[st.session_state.current_conversation].append({"role": "assistant", "content": full_response})
                save_message(st.session_state.current_conversation, "assistant", full_response)
