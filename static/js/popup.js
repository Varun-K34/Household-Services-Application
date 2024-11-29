// Wait for the document to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
    // Get all alert messages
    const alertMessages = document.querySelectorAll('.alert');

    // Loop through each alert and hide after a delay
    alertMessages.forEach(function (alert) {
        // Set a timeout to remove the alert after 5 seconds
        setTimeout(function () {
            alert.style.display = 'none';
        }, 5000); // 5000 milliseconds (5 seconds)
    });
});
