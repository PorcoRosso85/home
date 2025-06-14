// @ts-nocheck
// テーマ切り替えとインタラクティブ機能の実装
document.addEventListener('DOMContentLoaded', () => {
  // テーマ切り替え機能
  const themeToggle = document.getElementById('theme-toggle');
  
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-theme');
      
      // ユーザー設定を保存
      const isDarkTheme = document.body.classList.contains('dark-theme');
      localStorage.setItem('dark-theme', isDarkTheme.toString());
    });
    
    // 保存された設定を復元
    const savedTheme = localStorage.getItem('dark-theme');
    if (savedTheme === 'true') {
      document.body.classList.add('dark-theme');
    }
  }
  
  // カウンターのサンプル実装
  const counterElement = document.getElementById('counter');
  const incrementButton = document.getElementById('increment');
  
  if (counterElement && incrementButton) {
    let count = 0;
    
    incrementButton.addEventListener('click', () => {
      count++;
      counterElement.textContent = count.toString();
    });
  }
  
  // アニメーション効果
  const animateElements = document.querySelectorAll('.animate-on-scroll');
  
  const checkVisibility = () => {
    animateElements.forEach(element => {
      const boundingRect = element.getBoundingClientRect();
      const isVisible = boundingRect.top < window.innerHeight * 0.8;
      
      if (isVisible) {
        element.classList.add('visible');
      }
    });
  };
  
  // スクロール時のアニメーション
  window.addEventListener('scroll', checkVisibility);
  
  // 初期チェック
  checkVisibility();
  
  console.log('Client-side interactivity loaded successfully!');
});
