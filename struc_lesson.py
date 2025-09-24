from copy import deepcopy

LESSON_TEMPLATE = {
    "topic": "",
    "vocabulary": [
        {"word": "", "pronunciation": "", "english_meaning": "", "vietnamese_meaning": "", "example": ""} for _ in range(5)
    ],
    "example_sentences": [
        {"english": "", "translation": ""} for _ in range(5)
    ],
    "conversation": [
        {"speaker": "A", "text": "", "translation": ""},
        {"speaker": "B", "text": "", "translation": ""},
        {"speaker": "A", "text": "", "translation": ""},
        {"speaker": "B", "text": "", "translation": ""}
    ],
    "exercises": [
        {"type": "fill_in_blank", "question": "", "options": [], "answer": ""} for _ in range(3)
    ] + [
        {"type": "sentence_order", "scrambled": [], "answer": ""} for _ in range(3)
    ] + [
        {"type": "make_sentence", "word": "", "example": ""} for _ in range(3)
    ]
}

def standardize_lesson(ai_json: dict, topic: str) -> dict:
    """
    Chuẩn hóa JSON bài học AI trả về sang cấu trúc chuẩn LESSON_TEMPLATE.
    """
    result = deepcopy(LESSON_TEMPLATE)
    result['topic'] = ai_json.get('topic', topic)

    # --- Vocabulary ---
    vocab_mapping = {
        "word": ["word"],
        "pronunciation": ["pronunciation"],
        "english_meaning": ["english_meaning", "english_definition", "meaning"],
        "vietnamese_meaning": ["vietnamese_meaning", "vietnamese_definition", "translation"],
        "example": ["example"]
    }
    for i, vocab in enumerate(ai_json.get('vocabulary', [])):
        if i >= len(result['vocabulary']):
            break
        new_vocab = {}
        for k, keys in vocab_mapping.items():
            for key in keys:
                if key in vocab:
                    new_vocab[k] = vocab[key]
                    break
            else:
                new_vocab[k] = ""
        result['vocabulary'][i].update(new_vocab)

    # --- Example sentences ---
    ex_mapping = {
        "english": ["sentence", "english"],
        "translation": ["vietnamese_translation", "translation"]
    }
    # Tìm examples từ AI response (có thể là 'examples' hoặc 'example_sentences')
    examples_data = ai_json.get('examples', ai_json.get('example_sentences', []))
    for i, ex in enumerate(examples_data):
        if i >= len(result['example_sentences']):
            break
        new_ex = {}
        for k, keys in ex_mapping.items():
            for key in keys:
                if key in ex:
                    new_ex[k] = ex[key]
                    break
            else:
                new_ex[k] = ""
        result['example_sentences'][i].update(new_ex)

    # --- Conversation ---
    conv_mapping = {
        "speaker": ["speaker"],
        "text": ["dialogue", "text", "sentence"],
        "translation": ["vietnamese_translation", "translation"]
    }
    conv_list = ai_json.get('conversation', [])
    
    # Xử lý conversation có thể có cấu trúc khác nhau
    for i, msg in enumerate(conv_list):
        new_msg = {}
        
        # Xử lý trường hợp dialogue chứa cả A và B trong một string
        if 'dialogue' in msg and isinstance(msg['dialogue'], str):
            dialogue_text = msg['dialogue']
            translation = msg.get('vietnamese_translation', '')
            
            # Parse format "A: Do you like apples? B: Yes, I love apples!"
            if "A:" in dialogue_text and "B:" in dialogue_text:
                parts = dialogue_text.split("B:")
                if len(parts) == 2:
                    # Thêm message A
                    a_text = parts[0].replace("A:", "").strip()
                    if a_text:
                        new_msg_a = {"speaker": "A", "text": a_text, "translation": translation}
                        if i * 2 >= len(result['conversation']):
                            result['conversation'].append(new_msg_a)
                        else:
                            result['conversation'][i * 2].update(new_msg_a)
                    
                    # Thêm message B  
                    b_text = parts[1].strip()
                    if b_text:
                        new_msg_b = {"speaker": "B", "text": b_text, "translation": translation}
                        if i * 2 + 1 >= len(result['conversation']):
                            result['conversation'].append(new_msg_b)
                        else:
                            result['conversation'][i * 2 + 1].update(new_msg_b)
                    continue
        
        # Xử lý object thông thường
        for k, keys in conv_mapping.items():
            for key in keys:
                if key in msg:
                    new_msg[k] = msg[key]
                    break
            else:
                new_msg[k] = ""
        
        if i >= len(result['conversation']):
            result['conversation'].append(new_msg)
        else:
            result['conversation'][i].update(new_msg)

    # --- Exercises ---
    # Nếu AI không trả về exercises, tạo exercises mẫu từ vocabulary
    if not ai_json.get('exercises'):
        result['exercises'] = create_sample_exercises(result['vocabulary'])

    return result

def create_sample_exercises(vocabulary):
    """Tạo exercises mẫu từ vocabulary"""
    exercises = []
    
    # Fill in blank exercises (3 bài)
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('word') and vocab.get('example'):
            word = vocab['word'].lower()
            example = vocab['example']
            
            # Tạo câu hỏi điền từ
            if word in example.lower():
                question = example.replace(word, '_____').replace(word.capitalize(), '_____')
                # Tạo options
                options = [word]
                other_words = [v.get('word', '').lower() for v in vocabulary if v != vocab and v.get('word')]
                options.extend(other_words[:3])
                
                exercises.append({
                    "type": "fill_in_blank",
                    "question": question,
                    "options": options,
                    "answer": word
                })
    
    # Sentence order exercises (3 bài)
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('example'):
            example = vocab['example']
            words = example.split()
            if len(words) > 3:
                exercises.append({
                    "type": "sentence_order", 
                    "scrambled": words,
                    "answer": example
                })
    
    # Make sentence exercises (3 bài)
    for i, vocab in enumerate(vocabulary[:3]):
        if vocab.get('word') and vocab.get('example'):
            exercises.append({
                "type": "make_sentence",
                "word": vocab['word'],
                "example": vocab['example']
            })
    
    return exercises