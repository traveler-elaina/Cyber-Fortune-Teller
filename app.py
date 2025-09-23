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
    .conversation-button {
        display: block;
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
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .conversation-button:hover {
        background-color: #f0f0f0;
        border-color: #ccc;
    }
    .conversation-button.active {
        background-color: #007bff;
        color: white;
        border-color: #0056b3;
    }
    .conversation-button span {
        display: block;
        font-size: 12px;
        color: #666;
    }
    [data-testid="stTextInput"], [data-testid="stSelectbox"] {
        cursor: pointer;
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
            st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"保存消息失败：{str(e)}")
        return False

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
        return response.data[0]["content"][:20] + "..." if response.data else "无消息"
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

    # 垂直排列的会话按钮
    for conv_name in conversation_names:
        is_active = conv_name == st.session_state.current_conversation
        button_style = "conversation-button active" if is_active else "conversation-button"
        preview = get_preview(conv_name)
        st.markdown(
            f'<button class="{button_style}" onclick="Streamlit.setComponentValue({{conv: \'{conv_name}\'}});this.blur()">{conv_name}<br><span>{preview}</span></button>',
            unsafe_allow_html=True
        )

    # 处理组件值变化
    if st.session_state.get("component_value"):
        if "conv" in st.session_state.component_value:
            setattr(st.session_state, "current_conversation", st.session_state.component_value["conv"])
            del st.session_state["component_value"]  # 清理临时状态

    # 新建对话
    if st.button("新建对话", key="new_conversation", on_click=lambda: [
        setattr(st.session_state, "current_conversation", f"对话 {len(conversation_names) + 1}"),
        st.session_state.conversations.update({f"对话 {len(conversation_names) + 1}": [{"role": "system", "content": system_prompt}]}),
        st.rerun()
    ]):
        pass

    # 删除当前对话
    if len(conversation_names) > 1:
        if st.button("删除当前对话", key="delete_conversation", on_click=lambda: [
            supabase.table("conversations").delete().eq("conv_id", st.session_state.current_conversation).execute(),
            st.session_state.conversations.pop(st.session_state.current_conversation, None),
            setattr(st.session_state, "current_conversation", get_conversation_ids()[0] if get_conversation_ids() else "对话 1"),
            st.rerun()
        ] if len(conversation_names) > 1 else None):
            pass

    # 重命名当前对话
    def rename_conversation(new_name):
        try:
            supabase.table("conversations").delete().eq("conv_id", st.session_state.current_conversation).execute()
            for msg in st.session_state.conversations[st.session_state.current_conversation]:
                if msg["role"] != "system":
                    save_message(new_name, msg["role"], msg["content"])
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
                if "401" in str(e):
                    message_placeholder.error("API 密钥无效，请检查 DeepSeek API 密钥。")
                elif "network" in str(e).lower():
                    message_placeholder.error("网络错误，请检查校园网络或使用 VPN。")
                elif "token" in str(e).lower():
                    message_placeholder.error("API token 额度不足，请检查 DeepSeek 平台。")
                else:
                    message_placeholder.error(f"错误：{str(e)}")
            if full_response:
                st.session_state.conversations[st.session_state.current_conversation].append({"role": "assistant", "content": full_response})
                save_message(st.session_state.current_conversation, "assistant", full_response)
