/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'morandi-bg': '#E7E3D7',      // 燕麥底色
        'morandi-green': '#9FA896',  // 灰豆綠 (主色)
        'morandi-blue': '#94A7AE',   // 霧霾藍 (次色)
        'morandi-orange': '#C5A88E', // 琥珀肉粉 (澱粉/提醒色)
        'morandi-dark': '#6B6E70',   // 炭灰 (文字)
        'morandi-card': '#F4F2ED',   // 奶油色 (卡片)
      }
    },
  },
  plugins: [],
}