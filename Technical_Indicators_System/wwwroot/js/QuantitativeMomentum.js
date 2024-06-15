function validateDates() {
    const Remove_Low_Momentum_Stocks_Number = new Date(document.getElementById('Remove_Low_Momentum_Stocks_Number').value);

    if (Remove_Low_Momentum_Stocks_Number > 50) {
        // Show the modal
        var myModal = new bootstrap.Modal(document.getElementById('exampleModal'), {
            keyboard: false
        });
        myModal.show();
        return false;
    }

    return true;
}