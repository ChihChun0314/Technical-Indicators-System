/*---------------------------------scroll to top-------------------------------------------------------------*/
// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function () {
    showScrollTopButton();
};

function showScrollTopButton() {
    var scrollToTopBtn = document.getElementById("scrollToTopBtn");

    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
        scrollToTopBtn.style.display = "block";
    } else {
        scrollToTopBtn.style.display = "none";
    }
}

function scrollToTop() {
    document.body.scrollTop = 0; // For Safari
    document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE, and Opera
}
