
// --- FINANCIAL STATS LOGIC (Quick Win) ---
async function fetchFinancials() {
    const statsContainer = document.getElementById('financialStats');
    const bnaEl = document.getElementById('dolarBnaValue');
    const blueEl = document.getElementById('dolarBlueValue');
    
    // Ensure skeleton loading state
    if (bnaEl) bnaEl.parentElement.classList.add('loading');
    if (blueEl) blueEl.parentElement.classList.add('loading');

    try {
        const response = await fetch('/api/financials');
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();
        
        // Update DOM with animation delay for effect
        setTimeout(() => {
            if (bnaEl && data.dolar_bna) {
                bnaEl.textContent = `$${data.dolar_bna.venta}`;
                bnaEl.parentElement.classList.remove('loading');
            }
            
            if (blueEl && data.dolar_blue) {
                blueEl.textContent = `$${data.dolar_blue.venta}`;
                blueEl.parentElement.classList.remove('loading');
            }
            
            // Show container if hidden
            if (statsContainer) statsContainer.classList.remove('hidden');
            
        }, 500); // Small artificial delay for smooth UX
        
    } catch (error) {
        console.warn('Could not fetch financials:', error);
        // On error, hide values or show fallback
        if (bnaEl) {
            bnaEl.textContent = '---'; 
            bnaEl.parentElement.classList.remove('loading');
        }
        if (blueEl) {
            blueEl.textContent = '---';
            blueEl.parentElement.classList.remove('loading');
        }
    }
}

// Call on load
document.addEventListener('DOMContentLoaded', () => {
    fetchFinancials();
    // Refresh every 5 minutes
    setInterval(fetchFinancials, 300000); 
});
