document.addEventListener('DOMContentLoaded', function() {
    // Auto-calculate remaining funds for comptable
    const entrantInput = document.getElementById('frais_entrant');
    const depensesInput = document.getElementById('frais_depenses');
    const restantInput = document.getElementById('frais_restant');
    
    if (entrantInput && depensesInput && restantInput) {
        entrantInput.addEventListener('input', calculateRestant);
        depensesInput.addEventListener('input', calculateRestant);
        
        function calculateRestant() {
            const entrant = parseFloat(entrantInput.value) || 0;
            const depenses = parseFloat(depensesInput.value) || 0;
            restantInput.value = (entrant - depenses).toFixed(2);
        }
    }
});