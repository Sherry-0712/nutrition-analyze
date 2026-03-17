import pandas as pd
import json
import os

excel_file = "食品營養成分資料庫2024UPDATE2.xlsx"
json_output = "taiwan_food.json"

def convert_nutrition_xlsx_to_json():
    if not os.path.exists(excel_file):
        print(f"❌ 找不到檔案：{excel_file}")
        return

    print(f"🚀 正在從第二列讀取標題...")
    
    try:
        # skiprows=1 表示跳過第一列的說明文字，從第二列開始讀取標題
        df = pd.read_excel(excel_file, skiprows=1)
        
        # 根據你的檔案內容，精確定義欄位映射
        column_mapping = {
            "樣品名稱": "name",
            "熱量(kcal)": "calories",
            "總碳水化合物(g)": "carbs",
            "粗蛋白(g)": "protein",  # 注意：你的檔案標題是『粗蛋白(g)』
            "粗脂肪(g)": "fat"      # 注意：你的檔案標題是『粗脂肪(g)』
        }

        # 檢查檔案是否包含這些必要欄位
        missing_cols = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_cols:
            print(f"❌ 仍缺少欄位：{missing_cols}")
            print(f"偵測到的欄位有：{df.columns.tolist()[:15]}...") 
            return

        # 篩選並重新命名
        filtered_df = df[list(column_mapping.keys())].rename(columns=column_mapping)

        # 數據清洗：將微量(TR)或非數字內容轉為 0
        for col in ["calories", "carbs", "protein", "fat"]:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)

        # 轉換為 JSON 格式
        food_list = filtered_df.to_dict(orient="records")

        with open(json_output, "w", encoding="utf-8") as f:
            json.dump(food_list, f, ensure_ascii=False, indent=2)

        print(f"✅ 成功轉換！產出：{json_output}")
        print(f"📊 資料筆數：{len(food_list)} 筆")

    except Exception as e:
        print(f"❌ 執行出錯: {e}")

if __name__ == "__main__":
    convert_nutrition_xlsx_to_json()