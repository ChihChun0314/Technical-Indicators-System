function validateDates() {
    const startDate = new Date(document.getElementById('stdate').value);
    const endDate = new Date(document.getElementById('eddate').value);

    // Calculate the difference in time
    const timeDifference = endDate - startDate;

    // Convert time difference to days
    const dayDifference = timeDifference / (1000 * 3600 * 24);

    if (dayDifference <= 1036) {
        // Show the modal
        var myModal = new bootstrap.Modal(document.getElementById('exampleModal'), {
            keyboard: false
        });
        myModal.show();
        return false;
    }

    return true;
}