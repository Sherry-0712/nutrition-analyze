// 啟動服務指令：npm run dev
<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const API_BASE = 'https://nutrition-backend.onrender.com'
const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
})

// -- 快速轉換功能 start --
const quickInput = ref({
  protein: '',
  carbs: '',
  fat: '',
  sodium: ''
})

const quickResult = ref(null)

const calculateQuickPortions = () => {
  const { protein, carbs, fat } = quickInput.value
  
  if (protein === '' || carbs === '' || fat === '') {
    alert("請輸入蛋白質、碳水和脂肪的數值喔！")
    return
  }

  // 1. 計算總熱量 (100g 為單位)
  const calories = (protein * 4) + (carbs * 4) + (fat * 9)

  // 2. 計算拳頭數 (以 2:1:1 標準換算)
  // 澱粉：一拳頭約 60g 碳水
  // 蛋白質：一拳頭約 21g 蛋白質
  quickResult.value = {
    totalCalories: Math.round(calories),
    starch_fist: (carbs / 60).toFixed(1),
    protein_fist: (protein / 21).toFixed(1),
    veg_fist: 2.0, // 2:1:1 的標準建議量
    sodium: quickInput.value.sodium
  }
}
// -- 快速轉換功能 end --

// -- 串接後端的分析功能 start --
const foodInput = ref('')
const analysisResult = ref(null)
const isLoading = ref(false)
const loadingMessage = ref('正在分析中...')
const fileInput = ref(null)
const imagePreviewUrl = ref('')
let _lastObjectUrl = ''

const clearImagePreview = () => {
  if (_lastObjectUrl) URL.revokeObjectURL(_lastObjectUrl)
  _lastObjectUrl = ''
  imagePreviewUrl.value = ''
}

watch(foodInput, (val) => {
  // 只要開始輸入文字，就把上一張圖片預覽清掉
  if (val && imagePreviewUrl.value) clearImagePreview()
})

const handleAnalyze = async () => {
  if (!foodInput.value) return alert('請輸入食物名稱！')

  // 使用文字分析時，清掉舊的圖片預覽
  if (imagePreviewUrl.value) clearImagePreview()

  isLoading.value = true
  loadingMessage.value = '正在喚醒雲端伺服器，首次可能需 30～60 秒…'
  try {
    const formData = new FormData()
    formData.append('food_name', foodInput.value)

    const response = await api.post('/analyze', formData)
    analysisResult.value = response.data
  } catch (error) {
    console.error('分析失敗:', error)
    const timedOut = error.code === 'ECONNABORTED'
    alert(
      timedOut
        ? '請求逾時：Render 免費版冷啟動較慢，請等 1 分鐘後再試一次'
        : '後端連線失敗，請確認 Render 已部署且 GEMINI_API_KEY 已設定'
    )
  } finally {
    isLoading.value = false
    loadingMessage.value = '正在分析中...'
  }
}

const onFileChange = async (e) => {
  const file = e?.target?.files?.[0]
  if (!file) return

  // 建立圖片預覽
  if (_lastObjectUrl) URL.revokeObjectURL(_lastObjectUrl)
  _lastObjectUrl = URL.createObjectURL(file)
  imagePreviewUrl.value = _lastObjectUrl

  isLoading.value = true
  loadingMessage.value = '正在喚醒雲端伺服器並分析圖片，可能需 30～90 秒…'
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/analyze', formData)
    analysisResult.value = response.data
  } catch (error) {
    console.error('圖片分析失敗:', error)
    const timedOut = error.code === 'ECONNABORTED'
    alert(
      timedOut
        ? '請求逾時：圖片分析較久，請稍後再試'
        : '圖片分析失敗，請檢查網路或後端服務'
    )
  } finally {
    loadingMessage.value = '正在分析中...'
    isLoading.value = false
    // 允許同一張圖重複上傳也能觸發 change
    if (e?.target) e.target.value = ''
  }
}
// -- 串接後端的分析功能 end --
</script>

<template>
  <div class="min-h-screen bg-morandi-bg text-morandi-dark p-4 md:p-12 font-serif">
    
    <header class="text-center mb-16">
      <h1 class="text-5xl font-extralight tracking-widest text-morandi-green uppercase">Nutri-Check</h1>
      <div class="h-0.5 w-16 bg-morandi-green mx-auto mt-4 opacity-50"></div>
      <p class="mt-4 text-morandi-dark opacity-80 tracking-loose text-sm">2:1:1 比例與智慧營養分析</p>
    </header>

    <main class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-10 gap-12 items-start">
      
      <aside class="bg-morandi-card p-8 rounded-3xl shadow-sm border border-white/50 lg:col-span-4">
        <h3 class="font-medium text-lg mb-8 border-b border-morandi-bg pb-4 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-morandi-orange"></span>
          營養標示轉換
        </h3>
        
        <div class="space-y-6">
          <div v-for="(label, key) in {protein:'蛋白質', carbs:'碳水', fat:'脂肪', sodium:'鈉含量'}" :key="key">
            <label class="text-xs mb-2 block opacity-70">{{ label }}</label>
            <input v-model="quickInput[key]" type="number" 
              class="w-full bg-transparent border-b border-morandi-green/30 focus:border-morandi-green outline-none py-1 transition-colors px-1" />
          </div>
          
          <button @click="calculateQuickPortions" 
            class="w-full mt-4 bg-morandi-green text-white py-3 rounded-full hover:bg-opacity-90 transition-all tracking-widest text-sm shadow-md">
            CALCULATE
          </button>
        </div>

        <div v-if="quickResult" class="mt-10 animate-fade-in text-center">
          <p class="text-2xl font-light mb-6">{{ quickResult.totalCalories }} <span class="text-xs uppercase">kcal</span></p>
          <div class="grid grid-cols-3 gap-4 border-t border-morandi-bg pt-6">
            <div v-for="(val, icon) in {'🍚':quickResult.starch_fist, '🥩':quickResult.protein_fist, '🥦':2.0}" :key="icon">
              <span class="text-lg block mb-1">{{ icon }}</span>
              <span class="text-sm font-medium">{{ val }}拳</span>
            </div>
          </div>
        </div>
      </aside>

      <section class="lg:col-span-6 space-y-10">
        <div class="bg-morandi-card p-2 rounded-full shadow-inner border border-white/40 flex items-center px-6">
          <input type="file" ref="fileInput" class="hidden" @change="onFileChange" accept="image/*" />
          <button @click="fileInput?.click()" class="text-morandi-blue hover:text-morandi-dark transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            </svg>
          </button>
          <input v-model="foodInput" @keyup.enter="handleAnalyze()" type="text" 
            placeholder="輸入食物或拍攝餐點照片..." 
            class="flex-1 bg-transparent border-none focus:ring-0 p-4 text-morandi-dark placeholder-morandi-dark/30" />
          <button @click="handleAnalyze()" class="text-morandi-green font-medium tracking-widest hover:scale-105 transition-transform">
            ANALYZE
          </button>
        </div>

        <div v-if="imagePreviewUrl" class="animate-fade-in">
          <img
            :src="imagePreviewUrl"
            alt="上傳圖片預覽"
            class="w-full max-h-[320px] object-contain rounded-[1.5rem] border border-white/60 bg-white/30 shadow-sm"
          />
        </div>

        <div v-if="isLoading" class="text-center text-sm tracking-widest text-morandi-dark/70 animate-fade-in">
          {{ loadingMessage }}
        </div>

        <div v-if="analysisResult" class="grid grid-cols-1 md:grid-cols-2 gap-8 animate-fade-in">
          <div class="bg-white/40 p-8 rounded-[2rem] border border-white/60 backdrop-blur-sm shadow-sm">
            <h4 class="text-xs tracking-widest mb-3 opacity-60">分析結果</h4>
            <div v-if="analysisResult.source" class="mb-4 flex flex-wrap items-center gap-2">
              <span class="text-[11px] tracking-widest px-3 py-1 rounded-full border border-white/60 bg-white/50">
                資料來源：{{ analysisResult.source }}
              </span>
              <span v-if="analysisResult.matched_sample_name" class="text-[11px] tracking-widest px-3 py-1 rounded-full border border-white/60 bg-white/50">
                比對品名：{{ analysisResult.matched_sample_name }}
              </span>
              <span v-if="analysisResult.matched_keyword" class="text-[11px] tracking-widest px-3 py-1 rounded-full border border-white/60 bg-white/50">
                關鍵字：{{ analysisResult.matched_keyword }}
              </span>
            </div>
            <div v-if="analysisResult.food_name || (analysisResult.dish_names && analysisResult.dish_names.length)" class="mb-6">
              <p v-if="analysisResult.food_name" class="text-xl font-light mb-3">{{ analysisResult.food_name }}</p>
              <div v-if="analysisResult.dish_names && analysisResult.dish_names.length" class="flex flex-wrap gap-2">
                <span v-for="(name, idx) in analysisResult.dish_names" :key="idx"
                  class="px-3 py-1 rounded-full bg-white/50 border border-white/60 text-xs tracking-widest">
                  {{ name }}
                </span>
              </div>
            </div>
            <div class="space-y-4">
              <div class="flex justify-between border-b border-morandi-bg pb-2"><span>熱量</span><span>{{ analysisResult.calories }} 大卡</span></div>
              <div class="flex justify-between border-b border-morandi-bg pb-2"><span>碳水化合物</span><span>{{ analysisResult.carbs }} g</span></div>
              <div v-if="analysisResult.protein != null" class="flex justify-between border-b border-morandi-bg pb-2"><span>蛋白質</span><span>{{ analysisResult.protein }} g</span></div>
              <div v-if="analysisResult.fat != null" class="flex justify-between border-b border-morandi-bg pb-2"><span>脂肪</span><span>{{ analysisResult.fat }} g</span></div>
            </div>
          </div>

          <div class="bg-morandi-green/10 p-8 rounded-[2rem] border border-morandi-green/20 shadow-sm">
            <h4 class="text-xs tracking-widest mb-6 text-morandi-green">2:1:1 拳頭份量</h4>
            <div class="space-y-4 text-morandi-dark">
              <div class="flex justify-between"><span>🍚 澱粉</span><span class="font-bold">{{ analysisResult.starch_fist }} 拳</span></div>
              <div class="flex justify-between"><span>🥩 蛋白質</span><span class="font-bold">{{ analysisResult.protein_fist }} 拳</span></div>
              <div class="flex justify-between"><span>🥦 蔬菜</span><span class="font-bold">{{ analysisResult.veg_fist }} 拳</span></div>
              <div v-if="analysisResult.suggestion" class="pt-3 border-t border-morandi-green/15 text-sm leading-relaxed">
                {{ analysisResult.suggestion }}
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style>
.animate-fade-in { animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>