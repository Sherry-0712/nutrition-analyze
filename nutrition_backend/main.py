# 啟動虛擬環境：.\venv\Scripts\activate 
# 設定執行策略：Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process 
# 啟動app：uvicorn main:app --reload ； python -m uvicorn main:app --reload

import os
import json
import re
from typing import Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv

# ==========================================
# 1. 核心路徑與啟動檢查
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 確保 .env 與檔案路徑正確
dotenv_path = os.path.join(BASE_DIR, ".env")
json_path = os.path.join(BASE_DIR, "taiwan_food.json")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"📖 已載入設定檔: {dotenv_path}")
else:
    print(f"⚠️ 找不到 .env 檔案，請確認位置於: {dotenv_path}")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 錯誤：GEMINI_API_KEY 為空，請檢查 .env 內容")
else:
    print(f"✅ API Key 讀取成功 (前五碼): {api_key[:5]}...")
    genai.configure(api_key=api_key)

# 檢查資料庫是否存在
if not os.path.exists(json_path):
    print(f"❌ 警告：找不到資料庫 {json_path}，在地搜尋功能將失效")
else:
    print(f"✅ 資料庫準備就緒: {json_path}")

model = genai.GenerativeModel('gemini-3-flash-preview')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. 營養分析邏輯 (2:1:1 法則)
# ==========================================

SYSTEM_PROMPT = """
你是一位專業營養師。請分析使用者提供的食物。
請精確估計營養成分，並將其換算為 2:1:1 餐盤分量（1 拳頭澱粉約 60g 碳水, 1 拳頭蛋白質約 20g 蛋白質）。

請嚴格回傳以下 JSON 格式，不要 Markdown：
{
  "food_name": "餐點名稱",
  "dish_names": ["菜色1", "菜色2"],
  "calories": 數字,
  "carbs": 數字,
  "protein": 數字,
  "fat": 數字,
  "starch_fist": 數字,
  "protein_fist": 數字,
  "veg_fist": 數字,
  "suggestion": "建議文字"
}
"""

def _extract_json_object(text: str) -> dict:
    try:
        cleaned = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except:
        match = re.search(r"\{[\s\S]*\}", text)
        if match: return json.loads(match.group(0))
        raise ValueError("AI 回傳並非有效的 JSON 格式")

def _get_search_keyword(user_input: str) -> str:
    """利用 AI 將口語轉為資料庫關鍵字"""
    try:
        prompt = f"將『{user_input}』簡化為一個核心食物名詞（例如：『一大碗滷肉飯』轉為『滷肉飯』）。只需回傳名詞。"
        resp = model.generate_content([prompt])
        return resp.text.strip().replace(" ", "").replace("。", "")
    except:
        return user_input

def _search_local_fda(aligned_keyword: str) -> Optional[dict]:
    """在地資料庫檢索"""
    if not aligned_keyword: return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            food_list = json.load(f)
        
        # 優先找完全符合，再找部分符合
        for item in food_list:
            if item["name"] == aligned_keyword:
                return _format_db_result(item, "2024 官方資料庫 (精確)")
        
        for item in food_list:
            if aligned_keyword in item["name"]:
                return _format_db_result(item, "2024 官方資料庫 (模糊)")
    except Exception as e:
        print(f"🔍 搜尋錯誤: {e}")
    return None

def _format_db_result(item: dict, source: str) -> dict:
    c = float(item.get("carbs", 0))
    p = float(item.get("protein", 0))
    
    # 這裡可以根據食物類型判斷，或者預設給 0，讓 Gemini 去填寫
    return {
        "source": source,
        "food_name": item["name"],
        "calories": float(item.get("calories", 0)),
        "carbs": c,
        "protein": p,
        "fat": float(item.get("fat", 0)),
        "starch_fist": round(c / 60, 1),
        "protein_fist": round(p / 21, 1),
        "veg_fist": 0.0,  # 改為 0，或從資料庫讀取（但資料庫通常沒這項）
        "suggestion": f"這份{item['name']}含有約 {round(c/60, 1)} 拳頭澱粉。依照 2:1:1 法則，請記得額外攝取 2 拳頭的蔬菜喔！"
}

# ==========================================
# 3. API 路由
# ==========================================

@app.post("/analyze")
async def analyze_food(food_name: str = Form(None), file: UploadFile = File(None)):
    try:
        # --- 步驟 A：Gemini 初步理解 ---
        # 無論如何先讓 Gemini 辨識圖片或文字，因為它擅長「拆解食物組合」
        content = [SYSTEM_PROMPT]
        if file:
            img_bytes = await file.read()
            content.append({"mime_type": file.content_type, "data": img_bytes})
        elif food_name:
            content.append(f"請分析：{food_name}")
        
        response = model.generate_content(content)
        gemini_result = _extract_json_object(response.text)
        
        # --- 步驟 B：嘗試「關鍵字對齊」與「資料庫檢索」 ---
        # 抓取 Gemini 辨識出來的 food_name 來進行在地搜尋
        candidate = gemini_result.get("food_name") or food_name
        
        if candidate:
            keyword = _get_search_keyword(candidate)
            print(f"🔍 嘗試對齊在地資料庫: {keyword}")
            
            db_data = _search_local_fda(keyword)
            
            if db_data:
                print(f"✅ 發現官方數據，進行數值替換")
                # 如果在地資料庫找到了，我們就用官方的數值
                # 但保留 Gemini 給的建議 (suggestion) 和菜色拆解 (dish_names)
                db_data["dish_names"] = gemini_result.get("dish_names") or []
                db_data["suggestion"] = gemini_result.get("suggestion") or db_data["suggestion"]
                
                # 關鍵修正：如果是純白飯，蔬菜量回歸 AI 判斷或設為 0
                # 這裡讓它聰明一點：如果在地資料庫只有單一項，就參考 AI 的蔬菜量
                db_data["veg_fist"] = gemini_result.get("veg_fist", 0) 
                
                return db_data

        # --- 步驟 C：保底方案（AI 全權處理） ---
        # 如果在地資料庫沒找到，或者是像「火鍋」這種複雜食物
        print("💡 資料庫無匹配，採用 Gemini 全權預估")
        gemini_result["source"] = "Gemini 智慧預估"
        return gemini_result

    except Exception as e:
        print(f"🔥 分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)