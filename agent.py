from langchain_google_genai import ChatGoogleGenerativeAI
from prompt import BASE_ROLE_PROMPT, PROMPTS, CHATBOT_PROMPT
from dotenv import load_dotenv
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import os
import json
from struc_lesson import *
import re

load_dotenv()

app = Flask(__name__)
CORS(app)

class EnglishTeachingAgent:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            api_key=api_key,
            model=model,
            temperature=1
        )

    def generate(self, task: str, **kwargs) -> dict:
        if task not in PROMPTS:
            raise ValueError(f"Nhiệm vụ {task} chưa được định nghĩa trong PROMPTS")

        full_prompt = BASE_ROLE_PROMPT + "\n\n" + PROMPTS[task].format(**kwargs)
        response = self.llm.invoke(full_prompt)

        try:
            result_json = json.loads(response.content)
        except json.JSONDecodeError:
            result_json = {"content": response.content}

        return result_json

API_KEY = os.getenv("GEMINI_API_KEY")
agent = EnglishTeachingAgent(api_key=API_KEY)


@app.route('/')
def index():
    return send_file('index.html')

# Trang bài học
@app.route('/lesson')
def lesson_page():
    return send_file('lesson.html')

# Trang chatbot
@app.route('/chatbot')
def chatbot_page():
    return send_file('chatbot.html')


# API tạo bài học
@app.route('/generate/lesson/<topic>')
def generate_content(topic):
    try:
        # Bước 1: Tạo bài học ban đầu từ AI
        print(f"🚀 Bước 1: Tạo bài học ban đầu cho chủ đề '{topic}'")
        lesson_data = agent.generate("lesson", topic=topic)
        content = lesson_data.get('content', '{}')
        print("🔥 AI raw content:", content)

        try:
            # Xử lý trường hợp AI trả về markdown code blocks
            if "```json" in content:
                # Tìm và extract JSON từ markdown
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                    ai_json = json.loads(json_str)
                else:
                    ai_json = {"topic": topic}  
            elif "```" in content:
                # Tìm JSON trong code blocks thông thường
                start = content.find("```") + 3
                end = content.find("```", start)
                if end != -1:
                    json_str = content[start:end].strip()
                    ai_json = json.loads(json_str)
                else:
                    ai_json = {"topic": topic}  
            else:
                # Parse JSON thông thường
                ai_json = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Raw content: {content}")
            ai_json = {"topic": topic} 

        # Bước 2: Chuẩn hóa cấu trúc và tạo exercises mẫu
        print("🔧 Bước 2: Chuẩn hóa cấu trúc và tạo exercises")
        standardized_lesson = standardize_lesson(ai_json, topic)
        print("✅ Standardized lesson JSON:", json.dumps(standardized_lesson, ensure_ascii=False, indent=2))

        # Bước 3: Đưa bài học đã chuẩn hóa qua AI lần 2 để tối ưu hóa
        print("🎯 Bước 3: Tối ưu hóa bài học qua AI")
        lesson_json_str = json.dumps(standardized_lesson, ensure_ascii=False, indent=2)
        
        final_lesson_data = agent.generate("finalize_lesson", lesson_data=lesson_json_str)
        final_content = final_lesson_data.get('content', '{}')
        print("🌟 AI final content:", final_content)

        try:
            # Parse JSON cuối cùng từ AI - xử lý markdown code blocks
            if "```json" in final_content:
                start = final_content.find("```json") + 7
                end = final_content.find("```", start)
                if end != -1:
                    json_str = final_content[start:end].strip()
                    final_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No closing ``` found", final_content, 0)
            elif "```" in final_content:
                start = final_content.find("```") + 3
                end = final_content.find("```", start)
                if end != -1:
                    json_str = final_content[start:end].strip()
                    final_result = json.loads(json_str)
                else:
                    raise json.JSONDecodeError("No closing ``` found", final_content, 0)
            else:
                final_result = json.loads(final_content)
            
            print("🎉 Final lesson JSON:", json.dumps(final_result, ensure_ascii=False, indent=2))
            return jsonify(final_result)
        except json.JSONDecodeError as e:
            # Nếu AI không trả về JSON hợp lệ, dùng kết quả đã chuẩn hóa
            print(f"⚠️ AI không trả về JSON hợp lệ: {e}")
            print("🔄 Sử dụng kết quả đã chuẩn hóa")
            return jsonify(standardized_lesson)

    except Exception as e:
        print(f"❌ Error generating content: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
#//////////////////////////////// CHATBOT DẠY HỌC ////////////////////////////////////////////////////

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    student_input = data.get("message", "")

    chat_prompt = CHATBOT_PROMPT.replace("{student_input}", student_input)
    response = agent.llm.invoke(chat_prompt)
    print("Raw response:", response)

    content = response.content

    # Loại bỏ ```json, ```, và dấu * thừa
    cleaned = re.sub(r"```json\s*|\s*```|\*+", "", content).strip()

    # Parse JSON
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {"response_english": cleaned}

    # Chuẩn hóa kết quả (null -> "")
    result = {
        "response_english": parsed.get("response_english") or "",
        "explanation_vietnamese": parsed.get("explanation_vietnamese") or "",
        "correction": parsed.get("correction") or ""
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)