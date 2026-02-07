"""
Advanced Memory Management Module with FAISS + Semantic Search
Quản lý lịch sử hội thoại với khả năng tìm kiếm ngữ cảnh thông minh
"""

import os
import json
import faiss
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
import traceback

# from huggingface_hub import login
# login(token="API_TOKEN_HuggingFace")  # Thay API_TOKEN_HuggingFace 


# ==========================
# 1. Config
# ==========================
MEMORY_DIR = "memory_data"
HISTORY_FILE = os.path.join(MEMORY_DIR, "chat_history.json")
FAISS_INDEX_FILE = os.path.join(MEMORY_DIR, "faiss_index.bin")

# Tạo thư mục nếu chưa có
os.makedirs(MEMORY_DIR, exist_ok=True)

CONFIG = {
    "recent_n": 10,          # Số tin nhắn gần nhất
    "top_k": 5,              # Số ngữ cảnh semantic tìm kiếm
    "summarize_every": 30,   # Sau bao nhiêu tin nhắn thì summarize
    "max_history": 100       # Tối đa số tin nhắn trong memory
}

# Embedding model - multilingual
try:
    embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    emb_dim = embedding_model.get_sentence_embedding_dimension()
except Exception as e:
    print(f"⚠️ Lỗi khi tải embedding model: {e}")
    embedding_model = None
    emb_dim = 384


class AdvancedConversationMemory:
    """
    Memory nâng cấp với FAISS semantic search + Stateful memory
    """
    
    def __init__(self, max_history=100, recent_n=10, top_k=5, summarize_every=30):
        """
        Args:
            max_history: Tối đa số tin nhắn lưu
            recent_n: Số tin nhắn gần nhất để include trong context
            top_k: Số kết quả semantic search trả về
            summarize_every: Summarize sau N tin nhắn
        """
        self.memory = {}  # {id_user: [{"user": "...", "ai": "...", "timestamp": "...", "embedding": [...]}]}
        self.max_history = max_history
        self.recent_n = recent_n
        self.top_k = top_k
        self.summarize_every = summarize_every
        
        # FAISS indexes per user
        self.faiss_indexes = {}  # {id_user: faiss_index}
        self.load_all_history()
    
    def _ensure_user_memory(self, id_user):
        """Đảm bảo user có memory và FAISS index"""
        if id_user not in self.memory:
            self.memory[id_user] = []
        
        if id_user not in self.faiss_indexes:
            if embedding_model:
                self.faiss_indexes[id_user] = faiss.IndexFlatIP(emb_dim)
    
    def add_message(self, id_user, user_msg, ai_msg):
        """
        Thêm tin nhắn và embedding vào memory
        
        Args:
            id_user: ID user
            user_msg: Tin nhắn từ user
            ai_msg: Tin nhắn từ AI
        """
        self._ensure_user_memory(id_user)
        
        # Tạo embedding
        combined_text = f"User: {user_msg}\nAI: {ai_msg}"
        embedding = None
        if embedding_model:
            try:
                embedding = embedding_model.encode(combined_text, convert_to_numpy=True).astype("float32").tolist()
            except Exception as e:
                print(f"⚠️ Lỗi embedding: {e}")
                embedding = None
        
        # Lưu tin nhắn
        self.memory[id_user].append({
            "user": user_msg,
            "ai": ai_msg,
            "timestamp": datetime.now().isoformat(),
            "embedding": embedding
        })
        
        # Cập nhật FAISS index
        if embedding:
            emb_array = np.array([embedding], dtype="float32")
            self.faiss_indexes[id_user].add(emb_array)
        
        # Giữ tối đa max_history
        if len(self.memory[id_user]) > self.max_history:
            # Xóa phần cũ nhất
            removed = len(self.memory[id_user]) - self.max_history
            self.memory[id_user] = self.memory[id_user][removed:]
            
            # Rebuild FAISS index
            self._rebuild_faiss_index(id_user)
        
        # Auto summarize
        if len(self.memory[id_user]) % self.summarize_every == 0:
            self._auto_summarize(id_user)
        
        # Save to disk
        self.save_history(id_user)
    
    def get_recent_context(self, id_user):
        """
        Lấy context từ các tin nhắn gần nhất
        
        Args:
            id_user: ID user
        
        Returns:
            String chứa lịch sử gần đây
        """
        self._ensure_user_memory(id_user)
        history = self.memory[id_user]
        
        if not history:
            return "Đây là lần đầu tiên bạn chat với tôi."
        
        # Lấy recent_n tin nhắn cuối
        recent = history[-self.recent_n:]
        context = "📝 Lịch sử hội thoại gần đây:\n"
        for msg in recent:
            context += f"Bạn: {msg['user']}\n"
            context += f"Tôi: {msg['ai']}\n\n"
        
        return context
    
    def get_semantic_context(self, id_user, query, top_k=None):
        """
        Tìm kiếm ngữ cảnh liên quan dùng semantic search
        
        Args:
            id_user: ID user
            query: Câu truy vấn
            top_k: Số kết quả trả về
        
        Returns:
            String chứa các tin nhắn liên quan
        """
        if top_k is None:
            top_k = self.top_k
        
        self._ensure_user_memory(id_user)
        
        if embedding_model is None or len(self.memory[id_user]) == 0:
            return ""
        
        try:
            # Embed query
            query_emb = embedding_model.encode([query], convert_to_numpy=True).astype("float32")
            
            # Tìm kiếm
            index = self.faiss_indexes[id_user]
            if index.ntotal == 0:
                return ""
            
            scores, indices = index.search(query_emb, min(top_k, index.ntotal))
            
            # Lấy kết quả
            relevant = []
            for idx in indices[0]:
                if idx >= 0 and idx < len(self.memory[id_user]):
                    msg = self.memory[id_user][idx]
                    relevant.append(f"Bạn: {msg['user']}\nTôi: {msg['ai']}")
            
            if not relevant:
                return ""
            
            return "🔗 Ngữ cảnh liên quan:\n" + "\n\n".join(relevant)
        
        except Exception as e:
            print(f"⚠️ Lỗi semantic search: {e}")
            return ""
    
    def get_full_context(self, id_user, query):
        """
        Lấy cả recent context và semantic context
        
        Args:
            id_user: ID user
            query: Câu truy vấn
        
        Returns:
            String chứa đầy đủ context
        """
        recent = self.get_recent_context(id_user)
        semantic = self.get_semantic_context(id_user, query, self.top_k)
        
        return f"{recent}\n{semantic}"
    
    def _rebuild_faiss_index(self, id_user):
        """Rebuild FAISS index từ embedding hiện có"""
        if embedding_model is None:
            return
        
        self.faiss_indexes[id_user] = faiss.IndexFlatIP(emb_dim)
        
        for msg in self.memory[id_user]:
            if msg.get("embedding"):
                emb_array = np.array([msg["embedding"]], dtype="float32")
                self.faiss_indexes[id_user].add(emb_array)
    
    def _auto_summarize(self, id_user):
        """
        Summarize lịch sử cũ để giảm token
        (Có thể gọi API tóm tắt nếu cần)
        """
        history = self.memory[id_user]
        
        if len(history) < self.summarize_every:
            return
        
        # Chỉ giữ recent_n + 1 summary entry
        old_part = history[:-self.recent_n]
        if len(old_part) > 1:
            print(f"⚡ Auto-summarizing {len(old_part)} old messages for user {id_user}")
            
            # Tạo summary text
            summary_text = "📌 Tóm tắt các cuộc hội thoại trước:\n"
            for msg in old_part:
                summary_text += f"- {msg['user'][:50]}...\n"
            
            # Tạo summary embedding
            summary_emb = None
            if embedding_model:
                summary_emb = embedding_model.encode(summary_text, convert_to_numpy=True).astype("float32").tolist()
            
            # Giữ lại summary + recent messages
            self.memory[id_user] = [{
                "user": "[📌 Tóm tắt hệ thống]",
                "ai": summary_text,
                "timestamp": datetime.now().isoformat(),
                "embedding": summary_emb
            }] + history[-self.recent_n:]
            
            # Rebuild index
            self._rebuild_faiss_index(id_user)
    
    def get_history(self, id_user):
        """Lấy toàn bộ lịch sử"""
        self._ensure_user_memory(id_user)
        return self.memory[id_user]
    
    def get_stats(self, id_user):
        """Lấy thống kê"""
        self._ensure_user_memory(id_user)
        history = self.memory[id_user]
        
        return {
            "total_messages": len(history),
            "user_messages": sum(1 for m in history if not m["user"].startswith("[")),
            "ai_messages": len(history),
            "has_summary": any(m["user"].startswith("[") for m in history)
        }
    
    def clear_history(self, id_user):
        """Xóa lịch sử của user"""
        if id_user in self.memory:
            del self.memory[id_user]
        if id_user in self.faiss_indexes:
            del self.faiss_indexes[id_user]
        
        # Xóa file
        user_history_file = os.path.join(MEMORY_DIR, f"history_{id_user}.json")
        if os.path.exists(user_history_file):
            os.remove(user_history_file)
    
    def save_history(self, id_user):
        """Lưu lịch sử của user"""
        try:
            self._ensure_user_memory(id_user)
            user_history_file = os.path.join(MEMORY_DIR, f"history_{id_user}.json")
            
            with open(user_history_file, "w", encoding="utf-8") as f:
                json.dump(self.memory[id_user], f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"⚠️ Lỗi lưu history: {e}")
    
    def load_all_history(self):
        """Load toàn bộ history từ disk"""
        try:
            for filename in os.listdir(MEMORY_DIR):
                if filename.startswith("history_") and filename.endswith(".json"):
                    id_user = int(filename.replace("history_", "").replace(".json", ""))
                    filepath = os.path.join(MEMORY_DIR, filename)
                    
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.memory[id_user] = json.load(f)
                    
                    # Rebuild FAISS index
                    self._rebuild_faiss_index(id_user)
                    print(f"✅ Loaded history for user {id_user}")
        
        except Exception as e:
            print(f"⚠️ Lỗi load history: {e}")
            traceback.print_exc()


# ==========================
# Global instance
# ==========================
conversation_memory = AdvancedConversationMemory(
    max_history=CONFIG["max_history"],
    recent_n=CONFIG["recent_n"],
    top_k=CONFIG["top_k"],
    summarize_every=CONFIG["summarize_every"]
)
