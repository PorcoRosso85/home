// Client-side JavaScript
console.log('Client JS loaded! 🎉');

// Add interactive element
document.addEventListener('DOMContentLoaded', () => {
  const clientDiv = document.getElementById('client-message');
  if (clientDiv) {
    clientDiv.textContent = 'Client-side JavaScript is running!';
    clientDiv.style.color = '#10b981';
    
    // Add click interaction
    clientDiv.addEventListener('click', () => {
      clientDiv.textContent = `Clicked at ${new Date().toLocaleTimeString()}`;
    });
  }
});